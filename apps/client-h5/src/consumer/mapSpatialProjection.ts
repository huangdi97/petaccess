import {
  synthMarkerPosition,
  type MapCamera,
  type MapMarker,
  type PlaceSummary,
} from "@petaccess/client-core";
import type { MapLensKey } from "./mapLens";

export function mapMarkersFor(
  places: PlaceSummary[],
  camera: MapCamera,
  statuses: Record<string, MapMarker["status"]>,
  allowSynthetic: boolean,
): MapMarker[] {
  return places.flatMap((place) => {
    const hasVerifiedPoint = place.latitude != null && place.longitude != null;
    if (!hasVerifiedPoint && !allowSynthetic) return [];

    const position = hasVerifiedPoint
      ? { lat: place.latitude as number, lng: place.longitude as number }
      : synthMarkerPosition(place.id, camera);

    return [
      {
        id: place.id,
        lat: position.lat,
        lng: position.lng,
        label: place.canonical_name,
        status: statuses[place.id] ?? "UNKNOWN",
      },
    ];
  });
}

export function visibleMapPlaces(
  lens: MapLensKey,
  filters: string[],
  places: PlaceSummary[],
  statuses: Record<string, MapMarker["status"]>,
): PlaceSummary[] {
  if (lens !== "rule" || !filters.length) return places;
  return places.filter((place) => filters.includes(statuses[place.id] ?? "UNKNOWN"));
}
