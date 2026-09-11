/**
 * MapProvider adapter interface (ADR-008). Implementations per platform:
 * - H5: canvas/svg mock renderer (apps/client-h5)
 * - uni-app x: <map> component adapter (apps/client platform adapters)
 * A real Tencent key only swaps the provider config — business logic unchanged.
 */

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  label: string;
  /** neutral status glyph, never moral red/green coding (design #34) */
  status: "MATCH" | "CONDITIONAL" | "RESTRICTED" | "UNKNOWN" | "CONFLICT";
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
  MATCH: "✔ 可进入",
  CONDITIONAL: "△ 有条件",
  RESTRICTED: "◼ 限制",
  UNKNOWN: "? 信息不足",
  CONFLICT: "⚠ 冲突",
};

export function synthDemoCamera(): MapCamera {
  return { lat: 31.23, lng: 121.47, zoom: 14 };
}
