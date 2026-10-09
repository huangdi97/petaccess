/**
 * MapProvider adapter interface (ADR-008). Implementations per platform:
 * - H5/Tauri current renderer: provider-neutral spatial surface (apps/client-h5)
 *   driven by the REAL representative coordinates returned by PlaceSummary.
 * - A Tencent GL renderer remains an external-key integration boundary; swapping
 *   the visual basemap must not change clustering, lenses, selection or facts.
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
 * Merge clusters whose anchors collide on a typical map canvas at this zoom.
 * It is important to do this in the shared projection, not by offsetting
 * displayed pins away from their actual WGS84 position. A merged anchor is the
 * count-weighted centroid of recorded positions; all member IDs are retained.
 * At higher zoom the proximity threshold shrinks and nearby places separate.
 */
function mergeCrowdedClusters(clusters: MapCluster[], zoom: number): MapCluster[] {
  const spanLng = 0.08 * Math.pow(2, 14 - zoom);
  const gapLng = spanLng * 0.055;
  const gapLat = spanLng * 0.62 * 0.055;
  const ordered = [...clusters].sort((a, b) => a.id.localeCompare(b.id));
  const roots = ordered.map((_, i) => i);

  function find(i: number): number {
    while (roots[i] !== i) {
      roots[i] = roots[roots[i]];
      i = roots[i];
    }
    return i;
  }

  for (let i = 0; i < ordered.length; i++) {
    for (let j = i + 1; j < ordered.length; j++) {
      if (
        Math.abs(ordered[i].lng - ordered[j].lng) <= gapLng &&
        Math.abs(ordered[i].lat - ordered[j].lat) <= gapLat
      ) {
        roots[find(j)] = find(i);
      }
    }
  }

  const groups = new Map<number, MapCluster[]>();
  ordered.forEach((cluster, i) => {
    const key = find(i);
    const members = groups.get(key) ?? [];
    members.push(cluster);
    groups.set(key, members);
  });

  return [...groups.values()]
    .map((group) => {
      if (group.length === 1) return group[0];
      const count = group.reduce((sum, cluster) => sum + cluster.count, 0);
      const memberIds = group.flatMap((cluster) => cluster.memberIds).sort();
      return {
        id: `near:${memberIds[0]}`,
        count,
        lat: group.reduce((sum, cluster) => sum + cluster.lat * cluster.count, 0) / count,
        lng: group.reduce((sum, cluster) => sum + cluster.lng * cluster.count, 0) / count,
        status:
          STATUS_PRIORITY.find((status) => group.some((cluster) => cluster.status === status)) ??
          "UNKNOWN",
        memberIds,
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
}

/**
 * Deterministic grid clustering.
 *
 * Above `unclusterAt` the renderer keeps one anchor per place except
 * for collision groups. Below it, larger spatial grid buckets form clusters.
 * Both routes merge near-overlapping anchors without fabricating geometry.
 * The grouping is deterministic and provider-independent.
 */
export function clusterMarkers(
  markers: MapMarker[],
  zoom: number,
  opts: { unclusterAt?: number; baseCellDeg?: number } = {},
): MapCluster[] {
  const unclusterAt = opts.unclusterAt ?? 14;
  const baseCellDeg = opts.baseCellDeg ?? 0.02;

  if (zoom >= unclusterAt) {
    return mergeCrowdedClusters(
      markers.map((m) => ({
        id: `m:${m.id}`,
        count: 1,
        lat: m.lat,
        lng: m.lng,
        status: m.status,
        memberIds: [m.id],
      })),
      zoom,
    );
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
  return mergeCrowdedClusters(clusters, zoom);
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
      ? "当前查询没有可显示的位置点。无地图点位不代表场所没有规则或现场事实。"
      : `当前查询中 ${markers.length} 个可定位场所：${covered} 个已有结论，` +
        `${unknown} 个信息不足或存在不一致。信息不足不等于允许。`;
  return { covered, unknown, text };
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
