import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  clusterMarkers,
  session,
  synthDemoCamera,
  type CoexistenceSnapshot,
  type MapCamera,
  type MapMarker,
  type PlaceSummary,
} from "@petaccess/client-core";

import {
  mapLensCoverage,
  mapLensLabel,
  mapLensTone,
  parseMapLens,
  type MapLensKey,
} from "../consumer/mapLens";
import {
  createEpoch,
  currentQueryContext,
  enrichRows,
  nearbyPlaces,
  snapshotFor,
  type RowFacts,
} from "../consumer/repository";
import { presentDescription } from "../errors";
import { mapMarkersFor, visibleMapPlaces } from "../consumer/mapSpatialProjection";
import { useBreakpoint } from "./useBreakpoint";
import { useMapClusterSelection } from "./useMapClusterSelection";
import { useMapDeepLink } from "./useMapDeepLink";
import { useMapLensRoute } from "./useMapLensRoute";
import { useMapSearch } from "./useMapSearch";
import { useOneShotMapLocation } from "./useOneShotMapLocation";
import { usePlaceSceneMedia } from "./usePlaceSceneMedia";

export interface PreviewState {
  snapshot: CoexistenceSnapshot | null;
  loading: boolean;
  error: string;
}

export function useMapWorkspace() {
  const router = useRouter();
  const route = useRoute();

  const camera = ref<MapCamera>(synthDemoCamera());
  const places = ref<PlaceSummary[]>([]);
  const facts = ref<Map<string, RowFacts>>(new Map());
  const lens = ref<MapLensKey>(parseMapLens(route.query.lens));
  const loading = ref(true);
  const error = ref("");
  const view = ref<"map" | "list">("map");
  const selected = ref<PlaceSummary | null>(null);
  const { desktop: isDesktop } = useBreakpoint();
  const preview = ref<PreviewState>({ snapshot: null, loading: false, error: "" });
  const selectedSceneMedia = usePlaceSceneMedia(computed(() => selected.value?.id ?? null));
  const loadEpoch = createEpoch();
  const previewEpoch = createEpoch();
  const activeFilters = ref<string[]>([]);
  const statuses = computed<Record<string, MapMarker["status"]>>(() => {
    const out: Record<string, MapMarker["status"]> = {};
    for (const p of places.value) out[p.id] = mapLensTone(lens.value, facts.value.get(p.id));
    return out;
  });
  const lensLabels = computed<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    for (const p of places.value) out[p.id] = mapLensLabel(lens.value, facts.value.get(p.id));
    return out;
  });
  const unavailablePlaces = computed<Record<string, boolean>>(() => {
    const out: Record<string, boolean> = {};
    for (const place of places.value) {
      const row = facts.value.get(place.id);
      out[place.id] =
        !row ||
        (lens.value === "rule"
          ? row.answerError
          : lens.value === "reality" || lens.value === "facility"
            ? row.realityError
            : row.answerError || row.realityError);
    }
    return out;
  });
  const markers = computed<MapMarker[]>(() => mapMarkersFor(places.value, statuses.value));

  const visiblePlaces = computed(() =>
    visibleMapPlaces(lens.value, activeFilters.value, places.value, statuses.value),
  );

  const visiblePlaceIds = computed(() => new Set(visiblePlaces.value.map((place) => place.id)));
  const visibleMarkers = computed(() =>
    markers.value.filter((marker) => visiblePlaceIds.value.has(marker.id)),
  );
  const visibleMissingSpatialCount = computed(
    () =>
      visiblePlaces.value.filter((place) => place.latitude == null || place.longitude == null)
        .length,
  );

  const clusters = computed(() => clusterMarkers(visibleMarkers.value, camera.value.zoom));
  const coverage = computed(() => {
    const base = mapLensCoverage(lens.value, facts.value, visibleMarkers.value);
    if (!visibleMissingSpatialCount.value) return base;
    return {
      ...base,
      text: `${base.text} 另有 ${visibleMissingSpatialCount.value} 个场所缺少可用位置坐标，仅在列表显示。`,
    };
  });

  async function load() {
    const epoch = loadEpoch.begin();
    loading.value = true;
    error.value = "";
    try {
      const res = await nearbyPlaces(camera.value);
      if (!loadEpoch.isCurrent(epoch)) return;
      const nextPlaces = res.items;
      const nextFacts = await enrichRows(nextPlaces);
      if (!loadEpoch.isCurrent(epoch)) return;
      places.value = nextPlaces;
      facts.value = nextFacts;
      resolveSelection();
    } catch (e) {
      if (loadEpoch.isCurrent(epoch)) error.value = presentDescription(e);
    } finally {
      if (loadEpoch.isCurrent(epoch)) loading.value = false;
    }
  }

  let queryContextReady = false;

  onMounted(async () => {
    try {
      await session.restore();
    } catch {}
    await load();
    queryContextReady = true;
  });

  function open(id: string) {
    router.push({ name: "place", params: { id } });
  }

  const { onSelectCluster, selectResult } = useMapClusterSelection({
    camera,
    places,
    selected,
    preview,
    syncRoutePlace,
    selectPlace,
    reload: load,
  });

  function syncRoutePlace(id: string | null) {
    const current = typeof route.query.place === "string" ? route.query.place : null;
    if (current === id) return;
    void router.push({ query: { ...route.query, place: id || undefined } });
  }

  function resolveSelection() {
    const fromQuery = typeof route.query.place === "string" ? route.query.place : null;
    if (fromQuery) {
      const p = places.value.find((x) => x.id === fromQuery) ?? null;
      selected.value = p;
      if (p) void selectPlace(p);
      else requestDeepLinkedPlace(fromQuery);
      return;
    }
    if (!selected.value || !places.value.some((p) => p.id === selected.value?.id)) {
      selected.value = isDesktop.value && places.value.length ? places.value[0] : null;
      if (selected.value) void selectPlace(selected.value);
    }
  }

  async function selectPlace(p: PlaceSummary) {
    const epoch = previewEpoch.begin();
    preview.value = { snapshot: null, loading: true, error: "" };
    try {
      const { snapshot } = await snapshotFor(p.id);
      if (!previewEpoch.isCurrent(epoch) || selected.value?.id !== p.id) return;
      preview.value = { snapshot, loading: false, error: "" };
    } catch (e) {
      if (!previewEpoch.isCurrent(epoch) || selected.value?.id !== p.id) return;
      preview.value = { snapshot: null, loading: false, error: presentDescription(e) };
    }
  }

  const { state: locationState, locate } = useOneShotMapLocation({
    camera,
    reload: load,
  });

  const {
    loading: mapSearchLoading,
    error: mapSearchError,
    search: searchMap,
  } = useMapSearch({
    camera,
    places,
    facts,
    view,
    isDesktop,
    loadNearby: load,
    selectTarget: async (place) => {
      selected.value = place;
      syncRoutePlace(place.id);
      await selectPlace(place);
    },
  });
  const { request: requestDeepLinkedPlace, invalidate: invalidateDeepLink } = useMapDeepLink({
    route,
    camera,
    places,
    facts,
    view,
    isDesktop,
    error: mapSearchError,
    loadNearby: load,
    select: async (place) => {
      selected.value = place;
      await selectPlace(place);
    },
  });

  useMapLensRoute(lens, activeFilters);

  watch(
    () => route.query.place,
    (v) => {
      const next = typeof v === "string" ? v : null;
      invalidateDeepLink();
      const cur = selected.value?.id ?? null;
      if (next === cur) return;
      const p = places.value.find((x) => x.id === next) ?? null;
      selected.value = p;
      if (p) void selectPlace(p);
      else if (next) requestDeepLinkedPlace(next);
    },
  );

  watch(visiblePlaces, (list) => {
    if (!selected.value || list.some((place) => place.id === selected.value?.id)) return;
    const next = isDesktop.value && list.length ? list[0] : null;
    selected.value = next;
    syncRoutePlace(next?.id ?? null);
    if (next) void selectPlace(next);
    else preview.value = { snapshot: null, loading: false, error: "" };
  });

  watch(currentQueryContext, () => {
    if (!queryContextReady) return;
    void (async () => {
      await load();
      if (selected.value) await selectPlace(selected.value);
    })();
  });

  return {
    camera,
    places,
    facts,
    lens,
    lensLabels,
    statuses,
    unavailablePlaces,
    loading,
    error,
    locationState,
    mapSearchLoading,
    mapSearchError,
    view,
    selected,
    isDesktop,
    preview,
    selectedSceneMedia,
    activeFilters,
    clusters,
    coverage,
    visiblePlaces,
    locate,
    load,
    open,
    selectResult,
    onSelectCluster,
    searchMap,
    syncRoutePlace,
  };
}
