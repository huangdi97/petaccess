/**
 * useMapWorkspace — Map page data and selection state (freeze §9).
 *
 * Marker statuses derive from the SAME CoexistenceSnapshot rows the other
 * surfaces read (SSOT) via the consumer repository's bounded-concurrency
 * enrichment — never a second resolver. The selected place's floating preview
 * fetches one snapshot through snapshotFor() (same cache as the rows).
 * Geolocation is a one-shot read (ADR-012: no continuous location history).
 */
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
import { useMapDeepLink } from "./useMapDeepLink";
import { useMapLensRoute } from "./useMapLensRoute";
import { useMapSearch } from "./useMapSearch";
import { useOneShotMapLocation } from "./useOneShotMapLocation";

/** Load state of the floating preview for the selected place. */
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
    await session.restore();
    await load();
    queryContextReady = true;
  });

  function open(id: string) {
    router.push({ name: "place", params: { id } });
  }

  function onSelectCluster(cluster: { memberIds: string[]; count: number }) {
    if (cluster.count === 1) {
      const p = places.value.find((x) => x.id === cluster.memberIds[0]) ?? null;
      selected.value = p;
      if (p) {
        syncRoutePlace(p.id);
        void selectPlace(p);
      }
      return;
    }
    // A cluster is a spatial target, not only a zoom button. Recenter the
    // governed WGS84 query on the cluster and reload nearby facts; otherwise
    // the canvas can move visually while the result pane still describes the
    // previous query center.
    selected.value = null;
    syncRoutePlace(null);
    preview.value = { snapshot: null, loading: false, error: "" };
    camera.value = {
      ...camera.value,
      lat: cluster.lat,
      lng: cluster.lng,
      zoom: Math.min(18, camera.value.zoom + 1),
    };
    void load();
  }

  /** M4 A4 — the selected place is a route query so deep links and history work. */
  function syncRoutePlace(id: string | null) {
    const current = typeof route.query.place === "string" ? route.query.place : null;
    if (current === id) return;
    void router.push({ query: { ...route.query, place: id || undefined } });
  }

  /** Pick the previewed place from the deep link, else keep a valid selection. */
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

  /** M4 A1 — the floating preview fetches the ONE CoexistenceSnapshot for the
   *  place via the consumer repository (SSOT, same cache as rows). */
  async function selectPlace(p: PlaceSummary) {
    // v0.2.5 §24：mobile selected sheet 需要 key condition + 最近现场，
    // snapshot 不再只给 desktop 取。
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

  // Back/forward or an external deep link changes ?place= → update the selection
  // (guard keeps this from looping when it was our own push).
  useMapLensRoute(lens, activeFilters);

  watch(
    () => route.query.place,
    (v) => {
      const next = typeof v === "string" ? v : null;
      // Invalidate even if both the new route and selection are null.
      invalidateDeepLink();
      const cur = selected.value?.id ?? null;
      if (next === cur) return;
      const p = places.value.find((x) => x.id === next) ?? null;
      selected.value = p;
      if (p) void selectPlace(p);
      else if (next) requestDeepLinkedPlace(next);
    },
  );

  // A Rule-lens filter is a real spatial filter: a hidden result cannot
  // remain selected in the preview after its row and marker disappear.
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
    loading,
    error,
    locationState,
    mapSearchLoading,
    mapSearchError,
    view,
    selected,
    isDesktop,
    preview,
    activeFilters,
    clusters,
    coverage,
    visiblePlaces,
    locate,
    load,
    open,
    onSelectCluster,
    searchMap,
    syncRoutePlace,
  };
}
