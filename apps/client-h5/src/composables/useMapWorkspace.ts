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
  client,
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
  searchPlaces,
  snapshotFor,
  type RowFacts,
} from "../consumer/repository";
import { presentDescription } from "../errors";
import { mapMarkersFor, visibleMapPlaces } from "../consumer/mapSpatialProjection";
import { useBreakpoint } from "./useBreakpoint";
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
  const deepLinkEpoch = createEpoch();
  let lastRequestedPlaceId: string | null = null;
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
      text: `${base.text} 另有 ${visibleMissingSpatialCount.value} 个场所缺少已核验坐标，仅在列表显示。`,
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
    // zooming in splits the cluster; the user asked to see the members
    camera.value = { ...camera.value, zoom: Math.min(18, camera.value.zoom + 1) };
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

  /**
   * A Place → "地图定位" deep link must work beyond the default pilot camera.
   * PlaceOut does not expose geography; resolve the exact ID through its
   * canonical name's PlaceSummary projection, which carries governed WGS84.
   * Never guess position from a similar name or from a UUID.
   */
  function requestDeepLinkedPlace(id: string) {
    if (lastRequestedPlaceId === id) return;
    lastRequestedPlaceId = id;
    void focusDeepLinkedPlace(id);
  }

  async function focusDeepLinkedPlace(id: string) {
    const epoch = deepLinkEpoch.begin();
    try {
      const detail = await client.place(id);
      if (!deepLinkEpoch.isCurrent(epoch) || route.query.place !== id) return;
      const matches = await searchPlaces(detail.canonical_name);
      if (!deepLinkEpoch.isCurrent(epoch) || route.query.place !== id) return;
      const target = matches.items.find((place) => place.id === id);
      if (!target) {
        mapSearchError.value = "无法定位当前场所：精确场所记录尚未包含在搜索结果中。";
        return;
      }
      if (target.latitude != null && target.longitude != null) {
        view.value = "map";
        camera.value = {
          ...camera.value,
          lat: target.latitude,
          lng: target.longitude,
          zoom: Math.max(camera.value.zoom, 15),
        };
        await load();
        if (!deepLinkEpoch.isCurrent(epoch) || route.query.place !== id) return;
      }
      const inNearby = places.value.find((place) => place.id === id);
      if (!inNearby) {
        const newFacts = await enrichRows([target]);
        if (!deepLinkEpoch.isCurrent(epoch) || route.query.place !== id) return;
        places.value = [target, ...places.value];
        facts.value = new Map([...facts.value, ...newFacts]);
      }
      if (target.latitude == null || target.longitude == null) {
        view.value = isDesktop.value ? "map" : "list";
        mapSearchError.value = "该场所缺少已核验坐标，仅可在列表中查看，未生成地图点位。";
      }
      selected.value = inNearby ?? target;
      await selectPlace(selected.value);
    } catch (cause) {
      if (deepLinkEpoch.isCurrent(epoch) && route.query.place === id) {
        mapSearchError.value = presentDescription(cause);
      }
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
  // Back/forward or an external deep link changes ?place= → update the selection
  // (guard keeps this from looping when it was our own push).
  watch(lens, (value) => {
    activeFilters.value = [];
    const routeValue = typeof route.query.lens === "string" ? route.query.lens : "rule";
    if (routeValue === value || (value === "rule" && routeValue === "rule")) return;
    void router.replace({
      query: { ...route.query, lens: value === "rule" ? undefined : value },
    });
  });

  watch(
    () => route.query.lens,
    (value) => {
      const next = parseMapLens(value);
      if (next !== lens.value) lens.value = next;
    },
  );

  watch(
    () => route.query.place,
    (v) => {
      const next = typeof v === "string" ? v : null;
      const cur = selected.value?.id ?? null;
      if (next === cur) return;
      if (!next) {
        deepLinkEpoch.begin();
        lastRequestedPlaceId = null;
      }
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
