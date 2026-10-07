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

  async function search(query: string) {
    const q = query.trim();
    if (!q) return;
    loading.value = true;
    error.value = "";

    try {
      const result = await searchPlaces(q);
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
        const spatialTarget = deps.places.value.find((place) => place.id === target.id) ?? target;
        await deps.selectTarget(spatialTarget);
        return;
      }

      deps.places.value = result.items;
      deps.facts.value = await enrichRows(result.items);
      deps.view.value = "list";
      await deps.selectTarget(target);
      error.value = "已找到场所，但缺少已核验坐标；当前仅在列表显示。";
    } catch (cause) {
      error.value = presentDescription(cause);
    } finally {
      loading.value = false;
    }
  }

  return { loading, error, search };
}
