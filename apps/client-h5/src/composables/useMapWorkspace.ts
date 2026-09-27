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
  coverageHint,
  LOCATION_LABELS,
  session,
  synthDemoCamera,
  synthMarkerPosition,
  type CoexistenceSnapshot,
  type LocationState,
  type MapCamera,
  type MapMarker,
  type PlaceSummary,
} from "@petaccess/client-core";

import { answerStatusKey } from "../answer";
import { enrichRows, nearbyPlaces, snapshotFor } from "../consumer/repository";
import { presentDescription } from "../errors";
import { useBreakpoint } from "./useBreakpoint";

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
  const statuses = ref<Record<string, MapMarker["status"]>>({});
  const loading = ref(true);
  const error = ref("");
  const locationState = ref<LocationState>("IDLE");
  const view = ref<"map" | "list">("map");
  const selected = ref<PlaceSummary | null>(null);
  const { desktop: isDesktop } = useBreakpoint();
  const preview = ref<PreviewState>({ snapshot: null, loading: false, error: "" });
  const activeFilters = ref<string[]>([]);

  const markers = computed<MapMarker[]>(() =>
    places.value.map((p) => {
      const pos = synthMarkerPosition(p.id, camera.value);
      return {
        id: p.id,
        lat: pos.lat,
        lng: pos.lng,
        label: p.canonical_name,
        status: statuses.value[p.id] ?? "UNKNOWN",
      };
    }),
  );

  const clusters = computed(() => clusterMarkers(markers.value, camera.value.zoom));
  const coverage = computed(() => coverageHint(markers.value));

  const visiblePlaces = computed(() => {
    if (!activeFilters.value.length) return places.value;
    return places.value.filter((p) =>
      activeFilters.value.includes(statuses.value[p.id] ?? "UNKNOWN"),
    );
  });

  /** One-shot geolocation (ADR-012: no continuous location history). */
  function locate() {
    if (!("geolocation" in navigator)) {
      locationState.value = "UNAVAILABLE";
      return;
    }
    locationState.value = "REQUESTING";
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        camera.value = {
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          zoom: camera.value.zoom,
        };
        locationState.value = "GRANTED";
        void load();
      },
      () => {
        // Permission refused is not a dead end: the map falls back to a manual
        // area (Consumer UX §20) instead of an empty screen.
        locationState.value = "DENIED";
      },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 60000 },
    );
  }

  /**
   * Marker statuses, derived from the SAME CoexistenceSnapshot rows the other
   * surfaces read (SSOT) via the consumer repository's bounded-concurrency
   * enrichment. Never a second resolver.
   */
  async function deriveStatuses(list: PlaceSummary[]) {
    const facts = await enrichRows(list);
    const out: Record<string, MapMarker["status"]> = {};
    for (const [id, row] of facts) out[id] = answerStatusKey(row.answer);
    statuses.value = out;
  }

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      const res = await nearbyPlaces();
      places.value = res.items;
      await deriveStatuses(places.value);
      resolveSelection();
    } catch (e) {
      error.value = presentDescription(e);
    } finally {
      loading.value = false;
    }
  }

  onMounted(async () => {
    await session.restore();
    await load();
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

  function goSearch() {
    router.push({ name: "search" });
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
    if (!isDesktop.value) return;
    preview.value = { snapshot: null, loading: true, error: "" };
    try {
      const { snapshot } = await snapshotFor(p.id);
      preview.value = { snapshot, loading: false, error: "" };
    } catch (e) {
      preview.value = { snapshot: null, loading: false, error: presentDescription(e) };
    }
  }

  // Back/forward or an external deep link changes ?place= → update the selection
  // (guard keeps this from looping when it was our own push).
  watch(
    () => route.query.place,
    (v) => {
      const next = typeof v === "string" ? v : null;
      const cur = selected.value?.id ?? null;
      if (next === cur) return;
      const p = places.value.find((x) => x.id === next) ?? null;
      selected.value = p;
      if (p) void selectPlace(p);
    },
  );

  return {
    camera,
    places,
    statuses,
    loading,
    error,
    locationState,
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
    goSearch,
    syncRoutePlace,
  };
}
