<script setup lang="ts">
/**
 * MapResultPane — the map workspace's result pane (freeze §9): location row,
 * search shortcut, status filters (筛选 N toggle + panel, never a pill wall),
 * loading/error/empty/coverage/list rows.
 *
 * Divider-led rows with radius 0 (no cards); the map canvas in the parent
 * stays the dominant surface. "信息不足" is a first-class filter that is off
 * by default — filtering never hides unknown places silently.
 */
import { ref } from "vue";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import {
  LOCATION_LABELS,
  placeTypeLabel,
  type LocationState,
  type MapMarker,
  type PlaceSummary,
} from "@petaccess/client-core";
import SkeletonList from "../SkeletonList.vue";
import StateMessage from "../StateMessage.vue";
import StatusBadge from "../StatusBadge.vue";
import type { RowFacts } from "../../consumer/repository";
import type { MapLensKey } from "../../composables/useMapWorkspace";

const props = defineProps<{
  places: PlaceSummary[];
  facts: Map<string, RowFacts>;
  lens: MapLensKey;
  lensLabels: Record<string, string>;
  statuses: Record<string, MapMarker["status"]>;
  visiblePlaces: PlaceSummary[];
  loading: boolean;
  error: string;
  coverageText: string;
  locationState: LocationState;
  filters: string[];
}>();

const emit = defineEmits<{
  "update:filters": [value: string[]];
  locate: [];
  search: [];
  open: [id: string];
  retry: [];
  clearFilters: [];
  goHome: [];
}>();
/** Status filters, applied to the neutral marker statuses (never a ranking). */
const STATUS_FILTERS = [
  { key: "ALLOWED", label: "明确允许" },
  { key: "CONDITIONAL", label: "有条件" },
  { key: "RESTRICTED", label: "明确限制" },
  { key: "UNKNOWN", label: "信息不足" },
  { key: "CONFLICT", label: "来源不一致" },
];
/** 筛选 N 面板开合（desktop popover / mobile inline panel）。 */
const filterOpen = ref(false);

function toggleFilter(key: string) {
  const next = props.filters.includes(key)
    ? props.filters.filter((k) => k !== key)
    : [...props.filters, key];
  emit("update:filters", next);
}
</script>

<template>
  <section class="map-pane" data-ui="map-result-pane" aria-label="附近场所">
    <h2 class="map-pane__title">附近场所</h2>
    <div class="map-pane__head">
      <div class="row map-pane__locate">
        <strong data-testid="location-label">{{ LOCATION_LABELS[props.locationState] }}</strong>
        <button
          type="button"
          class="map-pane__locate-button"
          data-testid="locate-btn"
          :disabled="props.locationState === 'REQUESTING'"
          @click="emit('locate')"
        >
          {{ props.locationState === "REQUESTING" ? "定位中…" : "定位" }}
        </button>
      </div>
      <button type="button" class="block map-pane__search" @click="emit('search')">
        搜索场所 / 类别 / 附近
      </button>
      <p v-if="props.locationState === 'DENIED'" class="notice" data-testid="location-denied">
        未获得定位权限。你仍可手动选择区域，或直接搜索场所名。
      </p>
    </div>

    <!-- Rule lens keeps status filtering; other lenses intentionally show the
         full set because their facts are not access verdicts. -->
    <div v-if="props.lens === 'rule'" class="map-filter" data-ui="map-filter">
      <button
        type="button"
        class="map-filter__toggle"
        data-testid="map-filter-toggle"
        data-ui="map-filter-toggle"
        :aria-expanded="filterOpen"
        @click="filterOpen = !filterOpen"
      >
        筛选{{ props.filters.length ? ` ${props.filters.length}` : "" }}
      </button>
      <div v-if="filterOpen" class="map-filter__panel" data-ui="map-filter-panel">
        <div v-for="f in STATUS_FILTERS" :key="f.key" class="map-filter__row">
          <label>
            <input
              type="checkbox"
              :checked="props.filters.includes(f.key)"
              @change="toggleFilter(f.key)"
            />
            {{ f.label }}
          </label>
        </div>
        <button
          v-if="props.filters.length"
          type="button"
          class="map-filter__clear"
          data-testid="filter-clear"
          @click="emit('clearFilters')"
        >
          清除筛选
        </button>
        <p class="muted map-filter__hint">
          筛选只影响规则镜头；信息不足的场所默认仍然显示。
        </p>
      </div>
    </div>
    <p v-else class="muted map-lens-note" data-testid="map-lens-note">
      当前镜头展示全部附近场所；切回“规则”可按准入结论筛选。
    </p>

    <SkeletonList v-if="props.loading" :rows="3" />
    <StateMessage
      v-else-if="props.error"
      kind="ERROR"
      data-testid="map-provider-error"
      title="未能取得附近场所"
      :description="props.error"
    >
      <template #action>
        <button type="button" class="primary" @click="emit('retry')">重试</button>
      </template>
    </StateMessage>

    <template v-else>
      <StateMessage
        v-if="!props.places.length"
        kind="PARTIAL"
        :title="EMPTY_STATE_COPY.MAP.title"
        :description="EMPTY_STATE_COPY.MAP.description"
        data-testid="map-empty"
      >
        <template #action>
          <button type="button" class="primary" @click="emit('goHome')">返回首页</button>
        </template>
      </StateMessage>
      <template v-else>
        <p class="notice map-pane__coverage" data-testid="coverage-hint">
          {{ props.coverageText }}
        </p>

        <StateMessage
          v-if="!props.visiblePlaces.length"
          kind="PARTIAL"
          description="当前筛选下没有场所。清除筛选可查看全部（含信息不足的场所）。"
        >
          <template #action>
            <button type="button" class="primary" @click="emit('clearFilters')">清除筛选</button>
          </template>
        </StateMessage>

        <ul v-else class="map-place-list" role="list">
          <li
            v-for="p in props.visiblePlaces"
            :key="p.id"
            class="map-place-row"
            :data-testid="'place-' + p.id"
            @click="emit('open', p.id)"
          >
            <div class="map-place-row__head">
              <div class="map-place-row__identity">
                <strong>{{ p.canonical_name }}</strong>
                <span class="muted">
                  {{ placeTypeLabel(p.place_type) }}
                  <span v-if="p.distance_m"> · {{ Math.round(p.distance_m) }}m</span>
                </span>
              </div>
              <StatusBadge
                v-if="props.lens === 'rule'"
                :semantic="props.statuses[p.id] ?? 'UNKNOWN'"
              />
              <span v-else class="map-place-row__lens-fact">
                {{ props.lensLabels[p.id] ?? "信息不足" }}
              </span>
            </div>
          </li>
        </ul>
      </template>
    </template>
  </section>
</template>

<style scoped>
.map-pane {
  min-width: 0;
}

.map-pane__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-bottom: var(--pa-space-2);
}

.map-pane__locate {
  justify-content: space-between;
  min-height: 40px;
}

.map-pane__locate-button {
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  min-height: var(--pa-size-control-md);
  padding: var(--pa-space-1) var(--pa-space-2);
}

.map-pane__locate-button:hover,
.map-pane__locate-button:focus-visible {
  background: var(--pa-color-accent-weak);
}

.map-pane__search {
  text-align: left;
}

.map-pane__coverage {
  margin-top: var(--pa-space-1);
}

.map-lens-note {
  margin: var(--pa-space-2) 0;
  padding-bottom: var(--pa-space-2);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-sm);
}

.map-pane__title {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
}

/* 筛选入口 + 面板：单入口，不铺 pill wall。 */
.map-filter {
  margin: var(--pa-space-2) 0;
}

.map-filter__toggle {
  border: none;
  border-radius: var(--pa-radius-control);
  background: transparent;
  color: var(--pa-color-accent);
  padding: var(--pa-space-1) var(--pa-space-2);
  font-size: var(--pa-font-size-md);
  cursor: pointer;
}

.map-filter__toggle:hover,
.map-filter__toggle:focus-visible {
  background: var(--pa-color-accent-weak);
}

.map-filter__panel {
  margin-top: var(--pa-space-2);
  border-top: var(--pa-border-width) solid var(--pa-color-border);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  padding: var(--pa-space-2) 0;
}

.map-filter__row {
  min-height: var(--pa-size-control-md);
  display: flex;
  align-items: center;
}

.map-filter__row input {
  width: auto;
  margin-right: var(--pa-space-2);
}

.map-filter__clear {
  border: none;
  background: none;
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-md);
  min-height: var(--pa-size-control-md);
  padding: var(--pa-space-1) var(--pa-space-2);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.map-filter__hint {
  margin: var(--pa-space-1) 0 0;
}

/* v0.2.4 §32：results = divider rows，不再 12px rounded card。 */
.map-place-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.map-place-row {
  cursor: pointer;
  padding: var(--pa-space-4) 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  margin-bottom: 0;
}

.map-place-row:last-child {
  border-bottom: none;
}

.map-place-row:hover {
  background: var(--pa-color-surface-interactive);
}

.map-place-row__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--pa-space-3);
}

.map-place-row__identity {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  min-width: 0;
}

.map-place-row__lens-fact {
  max-width: 160px;
  text-align: right;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
}
</style>
