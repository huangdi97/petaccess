<script setup lang="ts">
/**
 * Map Tab — the full interaction shell (spec §2.1).
 *
 * Consumer UX Baseline v1 moved this off the home screen: the home is the
 * Decision Home (search-first), and the map is a first-class tab of its own.
 * The shell itself is unchanged — header (location + search) → filters →
 * body (map | list, with clustering, coverage hint and a bottom sheet).
 *
 * Everything the shell needs beyond rendering is provider-neutral and lives in
 * @petaccess/client-core: clustering, coverage, location state. The Mock map and
 * a real Tencent map therefore behave identically.
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  client,
  clusterMarkers,
  coverageHint,
  LOCATION_LABELS,
  placeTypeLabel,
  session,
  synthDemoCamera,
  synthMarkerPosition,
  type BoundaryProfile,
  type LocationState,
  type MapCamera,
  type MapMarker,
  type PlaceSummary,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import BottomSheet from "../components/BottomSheet.vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import FilterChips from "../components/FilterChips.vue";
import MockMap from "../components/MockMap.vue";
import PlacePreview from "../components/domain/PlacePreview.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import { answerStatusKey } from "../answer";
import { useBreakpoint } from "../composables/useBreakpoint";
import { presentDescription } from "../errors";
import { enrichRows, nearbyPlaces, snapshotFor } from "../consumer/repository";

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
const preview = ref<{
  snapshot: import("@petaccess/client-core").CoexistenceSnapshot | null;
  loading: boolean;
  error: string;
}>({ snapshot: null, loading: false, error: "" });
const boundary = ref<BoundaryProfile | null>(null);

/** Status filters, applied to the neutral marker statuses (never a ranking). */
const STATUS_FILTERS = [
  { key: "MATCH", label: "明确允许" },
  { key: "CONDITIONAL", label: "有条件" },
  { key: "RESTRICTED", label: "明确限制" },
  { key: "UNKNOWN", label: "信息不足" },
  { key: "CONFLICT", label: "来源不一致" },
];
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

const boundarySummary = computed(() => {
  if (!boundary.value) return "未设置共处边界（可逐条设置，不做总评分）";
  const n = boundary.value.preferences.length;
  return `共处边界「${boundary.value.name}」：已设置 ${n} 条偏好`;
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
 * surfaces read (SSOT, UI_RECONSTRUCTION_GOAL §8.1) via the consumer
 * repository's bounded-concurrency enrichment. Never a second resolver.
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
  await session.restore();
  // `/boundary-profiles/default` is account-scoped: asking for it while signed
  // out is a guaranteed 401, not a "no boundary yet" answer. Skip the call
  // instead of provoking an error the UI then has to swallow.
  if (session.signedIn) void loadBoundary();
  await load();
});

async function loadBoundary() {
  try {
    boundary.value = (await client.defaultBoundaryProfile()).profile;
  } catch {
    boundary.value = null; // signed-out users simply have no stored boundary
  }
}

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

/** M4 A1 — desktop pane fetches the ONE CoexistenceSnapshot for the place
 *  via the consumer repository (SSOT, same cache as rows). */
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
</script>

<template>
  <AppShell>
    <DesktopContentContainer :mode="isDesktop ? 'split' : 'single-column'">
      <div class="map-pane">
        <!-- header: location + search -->
        <div class="panel">
          <div class="row" style="justify-content: space-between">
            <strong data-testid="location-label">{{ LOCATION_LABELS[locationState] }}</strong>
            <button
              class="pill"
              data-testid="locate-btn"
              :disabled="locationState === 'REQUESTING'"
              @click="locate"
            >
              {{ locationState === "REQUESTING" ? "定位中…" : "定位" }}
            </button>
          </div>
          <button class="block" style="margin-top: 8px; text-align: left" @click="goSearch">
            🔍 搜索场所 / 类别 / 附近
          </button>
          <p v-if="locationState === 'DENIED'" class="notice" data-testid="location-denied">
            未获得定位权限。你仍可手动选择区域，或直接搜索场所名。
          </p>
        </div>

        <!-- secondary: filters + profile summary -->
        <FilterChips
          v-model="activeFilters"
          :options="STATUS_FILTERS"
          hint="筛选是可选的：信息不足的场所默认仍然显示（信息不足 ≠ 允许）。"
        />
        <div class="panel">
          <div class="muted">
            {{ session.activePet ? `本次：${session.activePet.display_name}` : "未设置宠物档案" }}
          </div>
          <div class="muted">{{ boundarySummary }}</div>
          <RouterLink class="btn" style="margin-top: 8px" to="/boundary">设置共处边界</RouterLink>
        </div>

        <!-- view toggle -->
        <div class="row" style="margin: 4px 0 8px">
          <button
            class="pill"
            :class="{ active: view === 'map' }"
            data-testid="view-map"
            @click="view = 'map'"
          >
            地图
          </button>
          <button
            class="pill"
            :class="{ active: view === 'list' }"
            data-testid="view-list"
            @click="view = 'list'"
          >
            列表
          </button>
        </div>

        <SkeletonList v-if="loading" :rows="3" />
        <StateMessage v-else-if="error" kind="ERROR" title="未能取得附近场所" :description="error">
          <template #action>
            <button class="primary" @click="load">重试</button>
          </template>
        </StateMessage>

        <template v-else>
          <StateMessage
            v-if="!places.length"
            kind="PARTIAL"
            :title="EMPTY_STATE_COPY.MAP.title"
            :description="EMPTY_STATE_COPY.MAP.description"
            data-testid="map-empty"
          >
            <template #action>
              <button class="primary" @click="router.push({ name: 'home' })">返回首页</button>
            </template>
          </StateMessage>
          <template v-else>
            <!-- map failure is never a dead end: the list below is the fallback -->
            <div v-if="view === 'map'" class="map-mock" data-testid="map">
              <MockMap
                :camera="camera"
                :clusters="clusters"
                :selected-id="selected?.id ?? null"
                @select="onSelectCluster"
              />
            </div>

            <!-- coverage hint: honest about how much is actually resolved -->
            <p class="notice" data-testid="coverage-hint">{{ coverage.text }}</p>

            <StateMessage
              v-if="!visiblePlaces.length"
              kind="PARTIAL"
              description="当前筛选下没有场所。清除筛选可查看全部（含信息不足的场所）。"
            >
              <template #action>
                <button class="primary" @click="activeFilters = []">清除筛选</button>
              </template>
            </StateMessage>

            <template v-else>
              <h1>规则地图</h1>
              <h2>附近场所</h2>
              <div
                v-for="p in visiblePlaces"
                :key="p.id"
                class="panel"
                :data-testid="'place-' + p.id"
                style="cursor: pointer"
                @click="open(p.id)"
              >
                <div class="row" style="justify-content: space-between">
                  <div>
                    <strong>{{ p.canonical_name }}</strong>
                    <div class="muted">
                      {{ placeTypeLabel(p.place_type) }}
                      <span v-if="p.distance_m"> · {{ Math.round(p.distance_m) }}m</span>
                    </div>
                  </div>
                  <StatusBadge :semantic="statuses[p.id] ?? 'UNKNOWN'" />
                </div>
              </div>
            </template>
          </template>
        </template>
      </div>

      <!-- M4 A1 — desktop split pane: the selected place's summary. -->
      <div class="map-preview">
        <PlacePreview
          :place="selected"
          :status="selected ? (statuses[selected.id] ?? null) : null"
          :snapshot="preview.snapshot"
          :loading="preview.loading"
          :error="preview.error"
        />
      </div>
    </DesktopContentContainer>

    <!-- selected place bottom sheet -->
    <BottomSheet
      :open="Boolean(selected) && !isDesktop"
      :title="selected?.canonical_name ?? null"
      @close="
        selected = null;
        syncRoutePlace(null);
      "
    >
      <template v-if="selected">
        <div class="muted">
          {{ placeTypeLabel(selected.place_type) }} ·
          {{ selected.canonical_address ?? "地址未收录" }}
        </div>
        <div style="margin: 8px 0">
          <StatusBadge :semantic="statuses[selected.id] ?? 'UNKNOWN'" block />
        </div>
        <div class="row">
          <button class="primary" data-testid="sheet-open-detail" @click="open(selected.id)">
            查看场所详情
          </button>
          <button
            @click="
              selected = null;
              syncRoutePlace(null);
            "
          >
            返回地图
          </button>
        </div>
      </template>
    </BottomSheet>
  </AppShell>
</template>

<style scoped>
/* M4 A1 — split layout: the left pane wraps, the preview sticks to the top. */
.map-pane {
  min-width: 0;
}

.map-preview {
  position: sticky;
  top: var(--pa-space-4);
}
</style>
