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
  session,
  synthDemoCamera,
  synthMarkerPosition,
  type CoexistenceSnapshot,
  type LocationState,
  type MapCamera,
  type MapMarker,
  type PlaceSummary,
} from "@petaccess/client-core";

import { answerStatusKey, answerVerdictLabel } from "../answer";
import { divergenceLabel, realityStateLabel } from "../reality";
import { enrichRows, nearbyPlaces, snapshotFor, type RowFacts } from "../consumer/repository";
import { presentDescription } from "../errors";
import { useBreakpoint } from "./useBreakpoint";

/** Load state of the floating preview for the selected place. */
export interface PreviewState {
  snapshot: CoexistenceSnapshot | null;
  loading: boolean;
  error: string;
}

export type MapLensKey = "rule" | "reality" | "facility" | "divergence";

export function useMapWorkspace() {
  const router = useRouter();
  const route = useRoute();

  const camera = ref<MapCamera>(synthDemoCamera());
  const places = ref<PlaceSummary[]>([]);
  const facts = ref<Map<string, RowFacts>>(new Map());
  const lens = ref<MapLensKey>("rule");
  const loading = ref(true);
  const error = ref("");
  const locationState = ref<LocationState>("IDLE");
  const view = ref<"map" | "list">("map");
  const selected = ref<PlaceSummary | null>(null);
  const { desktop: isDesktop } = useBreakpoint();
  const preview = ref<PreviewState>({ snapshot: null, loading: false, error: "" });
  const activeFilters = ref<string[]>([]);

  function toneFor(row: RowFacts | undefined): MapMarker["status"] {
    if (!row) return "UNKNOWN";
    if (lens.value === "rule") return answerStatusKey(row.answer);

    if (lens.value === "reality") {
      switch (row.reality?.state) {
        case "OBSERVED_RECENTLY":
        case "MULTI_EVIDENCE_OBSERVED":
          return "ALLOWED";
        case "OBSERVED_HISTORICALLY":
          return "STALE";
        case "DISPUTED":
          return "CONFLICT";
        default:
          return "UNKNOWN";
      }
    }

    if (lens.value === "facility") {
      const facilities = row.snapshot?.facility_summary ?? [];
      if (facilities.some((item) => item.operational_state === "active" && item.count > 0))
        return "ALLOWED";
      if (facilities.some((item) => item.count > 0)) return "CONDITIONAL";
      return "UNKNOWN";
    }

    const state = row.snapshot?.divergence?.state;
    if (state === "RULE_REALITY_ALIGNED") return "ALLOWED";
    if (state === "RULE_ALLOWS_BUT_NO_RECENT_RECORD") return "STALE";
    if (state && state !== "INSUFFICIENT_DATA") return "CONFLICT";
    return "UNKNOWN";
  }

  function lensLabelFor(row: RowFacts | undefined): string {
    if (!row) return "信息不足";
    if (lens.value === "rule") return answerVerdictLabel(row.answer);
    if (lens.value === "reality") return realityStateLabel(row.reality);
    if (lens.value === "facility") {
      const facilities = row.snapshot?.facility_summary ?? [];
      const total = facilities.reduce((sum, item) => sum + item.count, 0);
      const active = facilities
        .filter((item) => item.operational_state === "active")
        .reduce((sum, item) => sum + item.count, 0);
      if (active > 0) return `${active} 处已核验动物设施`;
      if (total > 0) return `${total} 处动物设施记录`;
      return "暂无已核验动物设施";
    }
    return divergenceLabel(row.snapshot?.divergence ?? null);
  }

  const statuses = computed<Record<string, MapMarker["status"]>>(() => {
    const out: Record<string, MapMarker["status"]> = {};
    for (const p of places.value) out[p.id] = toneFor(facts.value.get(p.id));
    return out;
  });

  const lensLabels = computed<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    for (const p of places.value) out[p.id] = lensLabelFor(facts.value.get(p.id));
    return out;
  });

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
  const coverage = computed(() => {
    if (lens.value === "rule") return coverageHint(markers.value);
    if (lens.value === "reality") {
      const count = [...facts.value.values()].filter(
        (row) => (row.reality?.evidence_count ?? 0) > 0,
      ).length;
      return {
        covered: count,
        unknown: Math.max(0, places.value.length - count),
        text: `当前视野 ${places.value.length} 个场所：${count} 个有现场证据。暂无记录不代表现场没有动物。`,
      };
    }
    if (lens.value === "facility") {
      const count = [...facts.value.values()].filter((row) =>
        (row.snapshot?.facility_summary ?? []).some((item) => item.count > 0),
      ).length;
      return {
        covered: count,
        unknown: Math.max(0, places.value.length - count),
        text: `当前视野 ${places.value.length} 个场所：${count} 个有动物设施记录。设施存在不等于允许进入。`,
      };
    }
    const count = [...facts.value.values()].filter((row) => {
      const state = row.snapshot?.divergence?.state;
      return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
    }).length;
    return {
      covered: count,
      unknown: Math.max(0, places.value.length - count),
      text: `当前视野 ${places.value.length} 个场所：${count} 个存在规则与现场差异。`,
    };
  });

  const visiblePlaces = computed(() => {
    if (lens.value !== "rule" || !activeFilters.value.length) return places.value;
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

  /** Load the same CoexistenceSnapshot rows used by Home/Search/Place. */
  async function loadFacts(list: PlaceSummary[]) {
    facts.value = await enrichRows(list);
  }

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      const res = await nearbyPlaces();
      places.value = res.items;
      await loadFacts(places.value);
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
    // v0.2.5 §24：mobile selected sheet 需要 key condition + 最近现场，
    // snapshot 不再只给 desktop 取。
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
  watch(lens, () => {
    activeFilters.value = [];
  });

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
    facts,
    lens,
    lensLabels,
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
