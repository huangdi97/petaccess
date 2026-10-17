import { type MapMarker, type PlaceSummary } from "@petaccess/client-core";
import type { MapLensKey } from "./mapLens";

export function mapMarkersFor(
  places: PlaceSummary[],
  statuses: Record<string, MapMarker["status"]>,
): MapMarker[] {
  // Do not turn a database identifier into a geographic claim, even in
  // development. A place without real coordinates belongs in the list only.
  return places.flatMap((place) => {
    if (place.latitude == null || place.longitude == null) return [];

    return [
      {
        id: place.id,
        lat: place.latitude,
        lng: place.longitude,
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
