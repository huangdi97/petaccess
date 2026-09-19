/**
 * MapProvider adapter interface (ADR-008). Implementations per platform:
 * - H5: canvas/svg mock renderer (apps/client-h5)
 * - uni-app x: <map> component adapter (apps/client platform adapters)
 * A real Tencent key only swaps the provider config — business logic unchanged.
 *
 * Everything below the `MapAdapter` interface is provider-neutral *behaviour*
 * (clustering, coverage hint, location state) shared by every renderer, so the
 * map home shell behaves identically on Mock and on Tencent.
 */

/**
 * The neutral presentation vocabulary, shared with the rest of the app.
 *
 * These are the SAME keys the answer model's effect maps onto
 * (`@petaccess/design-tokens`), not a map-only set: a marker used to speak a
 * second dialect ("MATCH") for the same rule the search row called "ALLOWED",
 * which is precisely the split the unified answer model removes.
 */
export type MarkerStatus =
  "ALLOWED" | "CONDITIONAL" | "RESTRICTED" | "UNKNOWN" | "CONFLICT" | "STALE";

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  /** neutral status glyph, never moral red/green coding (design #34) */
  status: MarkerStatus;
}

export interface MapPolygon {
  id: string;
  /** GeoJSON ring: [[lng, lat], ...] */
  ring: [number, number][];
  label: string;
  status: string;
}

export interface MapCamera {
  lat: number;
  lng: number;
  zoom: number;
}

export interface MapAdapter {
  readonly provider: string;
  render(el: unknown, camera: MapCamera): void;
  setMarkers(markers: MapMarker[]): void;
  setPolygons(polygons: MapPolygon[]): void;
  onTapMarker(cb: (marker: MapMarker) => void): void;
  navigateTo(lat: number, lng: number, name: string): void;
}

export const STATUS_GLYPHS: Record<string, string> = {
  ALLOWED: "✔ 可进入",
  CONDITIONAL: "△ 有条件",
  RESTRICTED: "◼ 限制",
  UNKNOWN: "? 信息不足",
  CONFLICT: "⚠ 冲突",
  STALE: "⟳ 待复核",
};

export function synthDemoCamera(): MapCamera {
  return { lat: 31.23, lng: 121.47, zoom: 14 };
}

/* ------------------------------------------------------------------- clusters */

export interface MapCluster {
  id: string;
  count: number;
  lat: number;
  lng: number;
  /** dominant neutral status of the members (never a moral colour) */
  status: MapMarker["status"];
  memberIds: string[];
}

/** Priority used to pick a cluster's representative status (most actionable first). */
const STATUS_PRIORITY: MapMarker["status"][] = [
  "CONFLICT",
  "RESTRICTED",
  "CONDITIONAL",
  "ALLOWED",
  "UNKNOWN",
  "STALE",
];

/**
 * Deterministic grid clustering.
 *
 * Above `unclusterAt` zoom every marker stands alone (the user is close enough
 * to read them). Below it, markers are bucketed into a grid whose cell size
 * shrinks with zoom, and each non-empty cell becomes one cluster. Deterministic
 * and provider-independent so the same data always clusters the same way.
 */
export function clusterMarkers(
  markers: MapMarker[],
  zoom: number,
  opts: { unclusterAt?: number; baseCellDeg?: number } = {},
): MapCluster[] {
  const unclusterAt = opts.unclusterAt ?? 15;
  const baseCellDeg = opts.baseCellDeg ?? 0.02;

  if (zoom >= unclusterAt) {
    return markers.map((m) => ({
      id: `m:${m.id}`,
      count: 1,
      lat: m.lat,
      lng: m.lng,
      status: m.status,
      memberIds: [m.id],
    }));
  }

  const cell = baseCellDeg * Math.pow(2, unclusterAt - zoom);
  const buckets = new Map<string, MapMarker[]>();
  for (const m of markers) {
    const key = `${Math.floor(m.lat / cell)}:${Math.floor(m.lng / cell)}`;
    const list = buckets.get(key);
    if (list) list.push(m);
    else buckets.set(key, [m]);
  }

  const clusters: MapCluster[] = [];
  for (const [key, members] of buckets) {
    const lat = members.reduce((s, m) => s + m.lat, 0) / members.length;
    const lng = members.reduce((s, m) => s + m.lng, 0) / members.length;
    let status: MapMarker["status"] = "UNKNOWN";
    for (const candidate of STATUS_PRIORITY) {
      if (members.some((m) => m.status === candidate)) {
        status = candidate;
        break;
      }
    }
    clusters.push({
      id: `c:${key}`,
      count: members.length,
      lat,
      lng,
      status,
      memberIds: members.map((m) => m.id),
    });
  }
  // stable order so screenshots and tests do not flake
  clusters.sort((a, b) => a.id.localeCompare(b.id));
  return clusters;
}

/* ------------------------------------------------------------------ coverage */

export interface CoverageHint {
  /** markers carrying a resolved answer in the current viewport */
  covered: number;
  /** markers whose answer is UNKNOWN / CONFLICT — shown, never filtered away */
  unknown: number;
  /** honest one-liner: coverage is a sample of what is recorded, not a promise */
  text: string;
}

/**
 * The coverage hint answers "how much of what I see is actually resolved?".
 * Unknown markers are counted, never hidden (spec §2.2: do not filter Unknown
 * out by default) — the product never implies "no rule" means "allowed".
 */
export function coverageHint(markers: MapMarker[]): CoverageHint {
  const unknown = markers.filter((m) => m.status === "UNKNOWN" || m.status === "CONFLICT").length;
  const covered = markers.length - unknown;
  const text =
    markers.length === 0
      ? "当前视野内暂无已收录场所。未收录不代表该场所没有规则。"
      : `当前视野 ${markers.length} 个场所：${covered} 个已有结论，` +
        `${unknown} 个信息不足或存在不一致。信息不足 ≠ 允许。`;
  return { covered, unknown, text };
}

/* ------------------------------------------------------------- mock geometry */

/**
 * Deterministic synthetic position for the Mock provider.
 *
 * The pilot's `nearby` response carries a distance but no coordinate (the real
 * provider resolves coordinates client-side). The Mock provider derives a stable
 * offset from the place id so a place always lands in the same spot — which
 * keeps clustering, screenshots and tests reproducible. Swapping in Tencent
 * replaces this with the provider's own coordinates.
 */
export function synthMarkerPosition(id: string, camera: MapCamera): { lat: number; lng: number } {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) % 100000;
  const dx = ((h % 41) - 20) / 20; // -1..1
  const dy = ((Math.floor(h / 41) % 37) - 18) / 18; // -1..1
  const span = 0.02 / Math.max(1, camera.zoom / 14);
  return { lat: camera.lat + dy * span * 0.3, lng: camera.lng + dx * span * 0.45 };
}

/* ------------------------------------------------------------------ location */
/**
 * One-shot location state (ADR-012: no continuous location history).
 * The UI maps these to the page-state vocabulary so the user always knows why
 * the map is centred where it is.
 */
export type LocationState = "IDLE" | "REQUESTING" | "GRANTED" | "DENIED" | "UNAVAILABLE";

export const LOCATION_LABELS: Record<LocationState, string> = {
  IDLE: "尚未定位（使用默认中心）",
  REQUESTING: "正在定位…",
  GRANTED: "已定位到当前位置（一次性）",
  DENIED: "定位权限被拒绝（使用默认中心）",
  UNAVAILABLE: "本设备不支持定位（使用默认中心）",
};
