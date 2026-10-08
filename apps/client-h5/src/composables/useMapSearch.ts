import { ref, type Ref } from "vue";
import type { MapCamera, PlaceSummary } from "@petaccess/client-core";

import { enrichRows, searchPlaces, type RowFacts } from "../consumer/repository";
import { presentDescription } from "../errors";

interface MapSearchDeps {
  camera: Ref<MapCamera>;
  places: Ref<PlaceSummary[]>;
  facts: Ref<Map<string, RowFacts>>;
  view: Ref<"map" | "list">;
  loadNearby: () => Promise<void>;
  selectTarget: (place: PlaceSummary) => Promise<void>;
}

/**
 * Search inside the Spatial Workspace.
 *
 * Search never invents coordinates. A hit with a governed representative point
 * recenters the map and reloads nearby places; a real hit without coordinates
 * remains a list-only result and says so explicitly.
 */
export function useMapSearch(deps: MapSearchDeps) {
  const loading = ref(false);
  const error = ref("");
  // Map search is a user-driven task. A slow earlier search must never move
  // the camera, replace the list, or select a place after a newer search.
  let searchGeneration = 0;

  async function search(query: string) {
    const q = query.trim();
    if (!q) return;
    const generation = ++searchGeneration;
    loading.value = true;
    error.value = "";

    try {
      const result = await searchPlaces(q);
      if (generation !== searchGeneration) return;
      if (!result.items.length) {
        error.value = "没有找到已收录场所。试试其他名称、商圈或地址。";
        return;
      }

      const target =
        result.items.find((place) => place.latitude != null && place.longitude != null) ??
        result.items[0]!;

      if (target.latitude != null && target.longitude != null) {
        deps.camera.value = {
          ...deps.camera.value,
          lat: target.latitude,
          lng: target.longitude,
          zoom: Math.max(deps.camera.value.zoom, 15),
        };
        await deps.loadNearby();
        if (generation !== searchGeneration) return;

        // A named hit can be absent from the nearby response (pagination,
        // independent server filters). Keep the selected search result in
        // the same visible list rather than displaying an orphan inspector.
        const inNearby = deps.places.value.find((place) => place.id === target.id);
        if (!inNearby) {
          const facts = await enrichRows([target]);
          if (generation !== searchGeneration) return;
          deps.places.value = [target, ...deps.places.value];
          deps.facts.value = new Map([...deps.facts.value, ...facts]);
        }
        if (generation !== searchGeneration) return;
        deps.view.value = "map";
        await deps.selectTarget(inNearby ?? target);
        return;
      }

      const facts = await enrichRows(result.items);
      if (generation !== searchGeneration) return;
      deps.places.value = result.items;
      deps.facts.value = facts;
      deps.view.value = "list";
      await deps.selectTarget(target);
      if (generation === searchGeneration) {
        error.value = "已找到场所，但缺少已核验坐标；当前仅在列表显示。";
      }
    } catch (cause) {
      if (generation === searchGeneration) error.value = presentDescription(cause);
    } finally {
      if (generation === searchGeneration) loading.value = false;
    }
  }

  return { loading, error, search };
}
