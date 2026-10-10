<script setup lang="ts">
/**
 * MapResultPane — the map workspace's result pane (freeze §9): location row,
 * in-workspace spatial search, status filters (筛选 N toggle + panel, never a pill wall),
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
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";
import type { MapLensKey } from "../../consumer/mapLens";

const props = defineProps<{
  places: PlaceSummary[];
  lens: MapLensKey;
  lensLabels: Record<string, string>;
  statuses: Record<string, MapMarker["status"]>;
  unavailablePlaces: Record<string, boolean>;
  selectedId?: string | null;
  visiblePlaces: PlaceSummary[];
  loading: boolean;
  error: string;
  coverageText: string;
  locationState: LocationState;
  filters: string[];
  searchLoading?: boolean;
  searchError?: string;
}>();

const emit = defineEmits<{
  "update:filters": [value: string[]];
  locate: [];
  search: [query: string];
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
const searchQuery = ref("");

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
      <form
        class="map-pane__search"
        data-testid="map-search-form"
        @submit.prevent="emit('search', searchQuery)"
      >
        <label class="visually-hidden" for="map-search-input">搜索场所、商圈或地址</label>
        <input
          id="map-search-input"
          v-model="searchQuery"
          data-testid="map-search-input"
          placeholder="搜索场所、商圈或地址"
          autocomplete="off"
        />
        <button
          type="submit"
          class="primary"
          data-testid="map-search-submit"
          :disabled="props.searchLoading || !searchQuery.trim()"
        >
          {{ props.searchLoading ? "搜索中…" : "搜索" }}
        </button>
      </form>
      <p
        v-if="props.searchError"
        class="notice map-pane__search-feedback"
        data-testid="map-search-feedback"
      >
        {{ props.searchError }}
      </p>
      <p v-if="props.locationState === 'DENIED'" class="notice" data-testid="location-denied">
        未获得定位权限。地图会保留当前区域；你仍可直接搜索场所、商圈或地址。
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
        <p class="muted map-filter__hint">筛选只影响规则镜头；信息不足的场所默认仍然显示。</p>
      </div>
    </div>
    <p v-else class="muted map-lens-note" data-testid="map-lens-note">
      <template v-if="props.lens === 'reality'">
        当前镜头展示经核验现场事实；没有记录不代表现场没有动物。
      </template>
      <template v-else-if="props.lens === 'facility'">
        当前镜头展示动物设施事实；设施存在不等于允许进入。
      </template>
      <template v-else>
        当前镜头对照规则与现场的差异；“不一致”只提示需要复核，不会自动改写正式规则。
      </template>
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
            :class="{ 'map-place-row--selected': props.selectedId === p.id }"
            :data-selected="props.selectedId === p.id ? 'true' : undefined"
          >
            <button
              type="button"
              class="map-place-row__button"
              :aria-current="props.selectedId === p.id ? 'true' : undefined"
              :data-selected="props.selectedId === p.id ? 'true' : undefined"
              :data-testid="'place-' + p.id"
              @click="emit('open', p.id)"
            >
              <div class="map-place-row__head">
                <div class="map-place-row__identity-wrap">
                  <PlaceTypeGlyph :place-type="p.place_type" size="sm" />
                  <div class="map-place-row__identity">
                    <strong>{{ p.canonical_name }}</strong>
                    <span class="muted">
                      {{ placeTypeLabel(p.place_type) }}
                      <span v-if="p.distance_m != null"> · {{ Math.round(p.distance_m) }}m</span>
                    </span>
                  </div>
                </div>
                <span
                  v-if="props.unavailablePlaces[p.id]"
                  class="map-place-row__lens-fact map-place-row__lens-fact--unavailable"
                >
                  {{ props.lensLabels[p.id] ?? "信息暂时无法取得" }}
                </span>
                <StatusBadge
                  v-else-if="props.lens === 'rule'"
                  :semantic="props.statuses[p.id] ?? 'UNKNOWN'"
                />
                <span v-else class="map-place-row__lens-fact">
                  {{ props.lensLabels[p.id] ?? "信息不足" }}
                </span>
              </div>
            </button>
          </li>
        </ul>
      </template>
    </template>
  </section>
</template>

<style scoped>
.map-pane {
  min-width: 0;
  padding: var(--pa-space-4);
  background: var(--pa-color-surface);
}

.map-pane__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-bottom: var(--pa-space-3);
  padding: var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-raised);
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--pa-space-1);
  align-items: center;
  padding: var(--pa-space-1);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
}

.map-pane__search input {
  min-width: 0;
  min-height: var(--pa-size-control-md);
  border: 0;
  background: transparent;
}

.map-pane__search button {
  min-height: var(--pa-size-control-md);
}

.map-pane__search-feedback {
  margin: 0;
  font-size: var(--pa-font-size-sm);
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
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface-raised);
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
  padding: var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-raised);
  box-shadow: var(--pa-elevation-1);
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
  position: relative;
  margin-bottom: var(--pa-space-2);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-raised);
  overflow: hidden;
  transition:
    transform var(--pa-motion-fast) var(--pa-motion-ease),
    border-color var(--pa-motion-fast) var(--pa-motion-ease),
    box-shadow var(--pa-motion-fast) var(--pa-motion-ease);
}

.map-place-row__button {
  width: 100%;
  min-height: var(--pa-size-control-lg);
  display: block;
  cursor: pointer;
  padding: var(--pa-space-4);
  border: 0;
  border-radius: inherit;
  background: transparent;
  box-shadow: none;
  color: inherit;
  font: inherit;
  text-align: left;
}

.map-place-row__button:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}

.map-place-row:hover,
.map-place-row:focus-within {
  transform: translateY(-1px);
  border-color: var(--pa-color-border-strong);
  box-shadow: var(--pa-elevation-1);
}

.map-place-row--selected {
  border-color: color-mix(in srgb, var(--pa-color-accent) 32%, var(--pa-color-border-subtle));
  background: color-mix(in srgb, var(--pa-color-accent-weak) 62%, var(--pa-color-surface-raised));
}

.map-place-row--selected::before {
  content: "";
  position: absolute;
  left: 0;
  top: var(--pa-space-3);
  bottom: var(--pa-space-3);
  width: 3px;
  border-radius: 999px;
  background: var(--pa-color-accent);
}

.map-place-row__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--pa-space-3);
}

.map-place-row__identity-wrap {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-3);
  min-width: 0;
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

.map-place-row__lens-fact--unavailable {
  color: var(--pa-color-text-muted);
}
</style>
