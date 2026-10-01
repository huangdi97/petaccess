<script setup lang="ts">
/**
 * Mock map renderer (MapProvider adapter, ADR-008).
 *
 * Renders provider-neutral clusters/markers projected around the camera. It is
 * a *renderer only*: clustering, coverage and location state live in
 * `@petaccess/client-core` so switching to the Tencent SDK replaces this
 * component and nothing else.
 *
 * Spatial language (contract MAP_MOCK_*): the surface carries a light SVG
 * basemap — road-like lines, block polygons, a subtle river/green area —
 * plus a zoom affordance, so the map reads as a space, never a grey grid with
 * a single number. Markers stay provider-neutral divs with semantic glyphs.
 */
import { computed } from "vue";
import type { MapCamera, MapCluster, MapMarker } from "@petaccess/client-core";
import { STATUS_GLYPHS } from "@petaccess/client-core";

const props = withDefaults(
  defineProps<{
    camera: MapCamera;
    clusters: MapCluster[];
    selectedId?: string | null;
  }>(),
  { selectedId: null },
);

const emit = defineEmits<{ select: [cluster: MapCluster] }>();

/** Degrees of longitude visible at this zoom (deterministic, provider-free). */
const spanDeg = computed(() => 0.02 / Math.max(1, props.camera.zoom / 14));

/** Projection, clamped so the whole pin box stays inside the surface. */
const PIN_HEIGHT_PX = 44;
const PIN_HALF_WIDTH_PX = 32;
/** Keeps pins off the bottom edge, where the surface border sits. */
const MAX_Y_PCT = 88;

function project(lat: number, lng: number): { left: string; top: string } {
  const relX = 0.5 + (lng - props.camera.lng) / spanDeg.value;
  const relY = 0.5 - (lat - props.camera.lat) / (spanDeg.value * 0.62);
  return {
    left: `clamp(${PIN_HALF_WIDTH_PX}px, ${relX * 100}%, calc(100% - ${PIN_HALF_WIDTH_PX}px))`,
    top: `clamp(${PIN_HEIGHT_PX}px, ${relY * 100}%, ${MAX_Y_PCT}%)`,
  };
}

const glyph = (status: MapMarker["status"]) => STATUS_GLYPHS[status] ?? STATUS_GLYPHS.UNKNOWN;

/** Deterministic spatial skeleton: roads, blocks, a river/green ribbon. */
const ROADS = ["M 0 128 L 260 96", "M 0 224 L 260 208", "M 76 0 L 96 260", "M 180 0 L 196 260"];
const BLOCKS = [
  "96,96 180,96 180,208 96,208",
  "20,150 76,150 76,224 20,224",
  "196,96 260,96 260,208 196,208",
];
const RIVER = "M 0 40 Q 130 60 260 40 L 260 84 Q 130 104 0 84 Z";
</script>

<template>
  <div class="map-surface" data-testid="map-surface" data-ui="mock-map">
    <!-- 空间基底：道路/街区/水系（SVG，纯表现，不承载数据语义） -->
    <svg
      class="map-basemap"
      viewBox="0 0 260 260"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <path class="basemap-river" :d="RIVER" />
      <polygon v-for="b in BLOCKS" :key="b" class="basemap-block" :points="b" />
      <path v-for="r in ROADS" :key="r" class="basemap-road" :d="r" />
    </svg>

    <div class="map-zoom" data-testid="map-zoom" data-ui="map-zoom" role="group" aria-label="缩放">
      <button type="button" aria-label="放大" disabled>＋</button>
      <button type="button" aria-label="缩小" disabled>－</button>
    </div>

    <div
      v-for="c in clusters"
      :key="c.id"
      class="map-pin"
      :class="{ 'map-pin--selected': selectedId === c.memberIds[0] }"
      :data-selected="selectedId === c.memberIds[0] ? 'true' : undefined"
      :data-ui="selectedId === c.memberIds[0] ? 'map-marker-selected' : 'map-marker'"
      :style="project(c.lat, c.lng)"
      :data-testid="c.count > 1 ? 'cluster-' + c.id : 'pin-' + c.memberIds[0]"
      :aria-label="`${c.count} 个场所，${glyph(c.status)}`"
      role="button"
      tabindex="0"
      @click="emit('select', c)"
      @keydown.enter="emit('select', c)"
    >
      <template v-if="c.count > 1">
        <div class="map-cluster" :class="'s-' + c.status">{{ c.count }}</div>
      </template>
      <template v-else>
        <!-- v0.2.5 §26：未选中 marker 只显示小 symbol，不永久铺满状态字；
             只有选中的（或 hover）才上 label。 -->
        <div v-if="selectedId === c.memberIds[0]" class="lbl" :class="'s-' + c.status">
          {{ glyph(c.status) }}
        </div>
        <div class="dot" :class="'s-' + c.status"></div>
      </template>
    </div>
    <div v-if="!clusters.length" class="map-empty muted">当前视野内暂无已收录场所</div>
  </div>
</template>

<style scoped>
.map-surface {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 480px;
  overflow: hidden;
}

/* 空间基底：轻量道路/街区/水系 —— 不是灰网格+数字。 */
.map-basemap {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.basemap-road {
  fill: none;
  stroke: var(--pa-color-map-grid-b);
  stroke-width: 4;
}

.basemap-block {
  fill: var(--pa-color-map-grid-a);
  stroke: var(--pa-color-border-subtle);
  stroke-width: 1;
}

.basemap-river {
  fill: var(--pa-color-reality-observed-bg);
  opacity: 0.55;
}

/* 缩放控件：空间感 affordance（mock 阶段为展示性控件）。 */
.map-zoom {
  position: absolute;
  right: var(--pa-space-3);
  top: var(--pa-space-3);
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  z-index: 2;
}

.map-zoom button {
  width: var(--pa-size-control-lg);
  height: var(--pa-size-control-lg);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-lg);
  cursor: default;
}

/* ---- pins ---- */
.map-pin {
  position: absolute;
  transform: translate(-50%, -100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
  min-height: var(--pa-size-control-lg);
  min-width: 32px;
  cursor: pointer;
  z-index: 1;
}

.map-pin--selected {
  z-index: 3;
}

.map-cluster {
  min-width: 24px;
  height: 24px;
  border-radius: var(--pa-radius-pill);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--pa-space-1);
}

.lbl {
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  white-space: nowrap;
  background: var(--pa-color-map-label-bg);
  border-radius: var(--pa-radius-sm);
  padding: 0 var(--pa-space-1);
  color: var(--pa-color-text-primary);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: var(--pa-radius-pill);
  border: 2px solid var(--pa-color-map-pin-border);
}

.map-pin--selected .dot {
  /* v0.2.5 §26：selected marker 1.3x + halo（未选中 12px → 选中 ~15.6px）。 */
  width: 16px;
  height: 16px;
  box-shadow:
    0 0 0 4px var(--pa-color-accent-weak),
    var(--pa-elevation-2);
  border-color: var(--pa-color-surface);
}
/* status fills mirror the app's status tokens (s-* classes from app sheet). */
.s-ALLOWED,
.s-MATCH {
  background: var(--pa-color-status-allowed);
}

.s-CONDITIONAL {
  background: var(--pa-color-status-conditional);
}

.s-RESTRICTED {
  background: var(--pa-color-status-restricted);
}

.s-UNKNOWN {
  background: var(--pa-color-status-unknown);
}

.s-CONFLICT {
  background: var(--pa-color-status-conflict);
}

.map-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}
</style>
