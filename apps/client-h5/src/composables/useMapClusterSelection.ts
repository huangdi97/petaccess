/**
 * Cluster selection for the provider-neutral map workspace.
 *
 * A cluster is a geographic query target, not a decorative zoom control:
 * opening one recentres the governed WGS84 query and reloads nearby facts.
 */
import type { Ref } from "vue";
import type {
  CoexistenceSnapshot,
  MapCamera,
  MapCluster,
  PlaceSummary,
} from "@petaccess/client-core";

interface ClusterPreviewState {
  snapshot: CoexistenceSnapshot | null;
  loading: boolean;
  error: string;
}

interface ClusterSelectionDeps {
  camera: Ref<MapCamera>;
  places: Ref<PlaceSummary[]>;
  selected: Ref<PlaceSummary | null>;
  preview: Ref<ClusterPreviewState>;
  syncRoutePlace: (id: string | null) => void;
  selectPlace: (place: PlaceSummary) => Promise<void>;
  reload: () => Promise<void>;
}

export function useMapClusterSelection(deps: ClusterSelectionDeps) {
  function onSelectCluster(cluster: MapCluster) {
    if (cluster.count === 1) {
      const place = deps.places.value.find((item) => item.id === cluster.memberIds[0]) ?? null;
      deps.selected.value = place;
      if (place) {
        deps.syncRoutePlace(place.id);
        void deps.selectPlace(place);
      }
      return;
    }

    deps.selected.value = null;
    deps.syncRoutePlace(null);
    deps.preview.value = { snapshot: null, loading: false, error: "" };
    deps.camera.value = {
      ...deps.camera.value,
      lat: cluster.lat,
      lng: cluster.lng,
      zoom: Math.min(18, deps.camera.value.zoom + 1),
    };
    void deps.reload();
  }

  return { onSelectCluster };
}
