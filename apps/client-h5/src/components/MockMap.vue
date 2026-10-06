<script setup lang="ts">
/**
 * Mock map renderer (MapProvider adapter, ADR-008).
 *
 * Renders provider-neutral clusters/markers projected around the camera. It is
 * a *renderer only*: clustering, coverage and location state live in
 * `@petaccess/client-core` so switching to the Tencent SDK replaces this
 * component and nothing else.
 *
 * Spatial language (contract MAP_MOCK_*): the surface carries an abstract
 * urban spatial canvas — primary/secondary road hierarchy, block polygons,
 * district edge, open-space patches, subtle building mass hints and a river
 * ribbon — all very light, cool, low-contrast, so the PetAccess overlay
 * (markers, selected preview) is always the visual focus. v0.2.7 §8/§9:
 * the canvas must read as a place, never as a grey grid with a few dots.
 *
 * Marker system (v0.2.7 §10): UNKNOWN = neutral fill, CONDITIONAL = subtle
 * amber ring, ALLOWED = subtle positive fill, RESTRICTED = subtle restriction
 * fill, SELECTED = scale + halo + elevation. No big coloured pins, no emoji.
 */
import { computed } from "vue";
import type { MapCamera, MapCluster, MapMarker } from "@petaccess/client-core";
import { STATUS_GLYPHS } from "@petaccess/client-core";

const props = withDefaults(
  defineProps<{
    camera: MapCamera;
    clusters: MapCluster[];
    selectedId?: string | null;
    lens?: string;
    lensLabels?: Record<string, string>;
  }>(),
  { selectedId: null, lens: "rule", lensLabels: () => ({}) },
);

const emit = defineEmits<{ select: [cluster: MapCluster]; zoom: [delta: number] }>();

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

function markerLabel(cluster: MapCluster): string {
  if (cluster.count > 1) return `${cluster.count} 个场所`;
  const id = cluster.memberIds[0];
  return id ? (props.lensLabels[id] ?? glyph(cluster.status)) : glyph(cluster.status);
}

function isSelectedCluster(cluster: MapCluster): boolean {
  return props.selectedId ? cluster.memberIds.includes(props.selectedId) : false;
}

/* ---- Abstract urban spatial canvas (v0.2.7 §8) -------------------------
 * Everything is pure decoration; no data semantics live here. The palette
 * stays very light cool neutral and low-contrast so the map never competes
 * with rule/reality/selected place. */
const DISTRICT =
  "M 12 12 H 248 A 10 10 0 0 1 258 22 V 238 A 10 10 0 0 1 248 248 H 12 A 10 10 0 0 1 2 238 V 22 A 10 10 0 0 1 12 2 Z";
const RIVER = "M 0 40 Q 130 60 260 40 L 260 84 Q 130 104 0 84 Z";
/** Soft open-space patch (park/green), very low opacity. */
const OPEN_SPACE =
  "M 100 96 Q 114 88 130 96 Q 146 88 160 98 L 160 130 Q 146 140 130 132 Q 114 140 100 128 Z";
const BLOCKS = [
  "96,96 180,96 180,208 96,208",
  "20,150 76,150 76,224 20,224",
  "196,96 260,96 260,208 196,208",
  "20,96 76,96 76,138 20,138",
  "180,208 260,208 260,248 180,248",
  "96,60 180,60 180,84 96,84",
];
/** Road hierarchy: wider primary, narrower secondary. */
const ROADS_PRIMARY = ["M 0 128 L 260 96", "M 180 0 L 196 260"];
const ROADS_SECONDARY = [
  "M 0 224 L 260 208",
  "M 76 0 L 96 260",
  "M 20 138 L 76 138 L 76 150",
  "M 196 84 L 196 96",
  "M 96 96 L 96 60",
];
/** Building mass hints: faint rectangles clustered inside blocks. Each entry is
 * "x,y,width,height" (rect geometry, not polygon points — the <rect> below
 * binds these fields directly). */
const MASS = [
  "104,104,16,12",
  "128,104,16,12",
  "152,104,16,12",
  "104,124,16,12",
  "128,124,16,12",
  "152,124,16,12",
  "104,168,20,16",
  "132,168,20,16",
  "28,158,16,12",
  "52,158,16,12",
  "204,104,20,16",
  "232,104,16,12",
];
</script>
<template>
  <div
    class="map-surface"
    :class="`map-surface--${lens}`"
    data-testid="map-surface"
    data-ui="mock-map"
  >
    <!-- 空间基底：道路层级/街区/开放空间/建筑体块/水系（SVG，纯表现，不承载数据语义） -->
    <svg
      class="map-basemap"
      viewBox="0 0 260 260"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <path class="basemap-district" :d="DISTRICT" />
      <path class="basemap-open" :d="OPEN_SPACE" />
      <path class="basemap-river" :d="RIVER" />
      <rect
        v-for="m in MASS"
        :key="m"
        class="basemap-mass"
        :x="m.split(',')[0]"
        :y="m.split(',')[1]"
        :width="m.split(',')[2]"
        :height="m.split(',')[3]"
      />
      <polygon v-for="b in BLOCKS" :key="b" class="basemap-block" :points="b" />
      <path v-for="r in ROADS_PRIMARY" :key="r" class="basemap-road basemap-road--primary" :d="r" />
      <path
        v-for="r in ROADS_SECONDARY"
        :key="r"
        class="basemap-road basemap-road--secondary"
        :d="r"
      />
    </svg>

    <span class="map-provider muted" data-testid="map-provider-fallback"> 简化空间底图 </span>

    <div class="map-zoom" data-testid="map-zoom" data-ui="map-zoom" role="group" aria-label="缩放">
      <button
        type="button"
        aria-label="放大"
        :disabled="camera.zoom >= 18"
        @click="emit('zoom', 1)"
      >
        ＋
      </button>
      <button
        type="button"
        aria-label="缩小"
        :disabled="camera.zoom <= 8"
        @click="emit('zoom', -1)"
      >
        －
      </button>
    </div>

    <div
      v-for="c in clusters"
      :key="c.id"
      class="map-pin"
      :class="{ 'map-pin--selected': isSelectedCluster(c) }"
      :data-selected="isSelectedCluster(c) ? 'true' : undefined"
      :data-ui="
        c.count > 1 ? (isSelectedCluster(c) ? 'map-marker-selected' : 'map-marker') : undefined
      "
      :style="project(c.lat, c.lng)"
      :data-testid="c.count > 1 ? 'cluster-' + c.id : 'pin-' + c.memberIds[0]"
      :aria-label="`${c.count} 个场所，${markerLabel(c)}`"
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
        <div v-if="isSelectedCluster(c)" class="lbl" :class="'s-' + c.status">
          {{ markerLabel(c) }}
        </div>
        <!-- v0.2.7 §10：dot 是 marker 本体（含语义形状），data-ui 供几何 gate 测量：
             map-marker / map-marker-selected（scale + halo + elevation）。 -->
        <div
          class="dot"
          :class="['s-' + c.status, { 'dot--selected': isSelectedCluster(c) }]"
          :data-ui="isSelectedCluster(c) ? 'map-marker-selected' : 'map-marker'"
        ></div>
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

/* 空间基底：轻量抽象城市画布 —— 不是灰网格+数字（v0.2.7 §8）。 */
.map-basemap {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  /* 画布基底 = 极浅冷中性色，SVG 元素在其上分层。 */
  background: var(--pa-color-map-grid-a);
}

.basemap-district {
  fill: none;
  stroke: var(--pa-color-border);
  stroke-width: 2;
  opacity: 0.55;
}

.basemap-open {
  fill: var(--pa-color-status-allowed-bg);
  opacity: 0.45;
}

.basemap-river {
  fill: var(--pa-color-reality-observed-bg);
  opacity: 0.5;
}

.basemap-block {
  fill: var(--pa-color-surface);
  opacity: 0.55;
  stroke: var(--pa-color-border-subtle);
  stroke-width: 1;
}

/* 建筑体块提示：极弱，仅提供密度感。 */
.basemap-mass {
  fill: var(--pa-color-text-muted);
  opacity: 0.08;
}

/* 道路层级：primary 更宽更明确，secondary 更细更弱。 */
.basemap-road {
  fill: none;
  stroke: var(--pa-color-map-grid-b);
}
.basemap-road--primary {
  stroke-width: 5;
  opacity: 0.9;
}
.basemap-road--secondary {
  stroke-width: 2;
  opacity: 0.65;
}

/* 缩放控件：mock fallback 也保持真实交互，不展示道具按钮。 */
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
  cursor: pointer;
}

.map-zoom button:disabled {
  cursor: default;
  opacity: 0.45;
}

.map-provider {
  position: absolute;
  left: var(--pa-space-3);
  bottom: var(--pa-space-2);
  z-index: 2;
  padding: 2px var(--pa-space-1);
  border-radius: var(--pa-radius-sm);
  background: color-mix(in srgb, var(--pa-color-surface) 88%, transparent);
  font-size: var(--pa-font-size-xs);
  pointer-events: none;
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

/* v0.2.7 §10 marker 系统：
 * - UNKNOWN      = neutral fill
 * - CONDITIONAL  = subtle amber ring（空心圆 + 琥珀描边）
 * - ALLOWED      = subtle positive fill
 * - RESTRICTED   = subtle restriction fill
 * - SELECTED     = scale 1.33x + halo + elevation（dot--selected）
 */
.dot {
  width: 12px;
  height: 12px;
  border-radius: var(--pa-radius-pill);
  border: 2px solid var(--pa-color-map-pin-border);
  transition: box-shadow var(--pa-motion-fast) var(--pa-motion-ease);
}

.dot.s-CONDITIONAL {
  background: transparent;
  border-width: 3px;
  border-color: var(--pa-color-status-conditional);
}

.dot--selected {
  width: 16px;
  height: 16px;
  box-shadow:
    0 0 0 4px var(--pa-color-accent-weak),
    var(--pa-elevation-2);
  border-color: var(--pa-color-surface);
}
/* 选中聚合（cluster）：与单点选中一致 —— halo + elevation（v0.2.7 §10）。 */
.map-pin--selected .map-cluster {
  box-shadow:
    0 0 0 4px var(--pa-color-accent-weak),
    var(--pa-elevation-2);
}

/* 选中 + 有条件：保留琥珀环，不覆盖为白边。 */
.dot--selected.s-CONDITIONAL {
  border-color: var(--pa-color-status-conditional);
}

/* status fills mirror the app's status tokens (s-* classes from app sheet). */
.s-ALLOWED,
.s-MATCH {
  background: var(--pa-color-status-allowed);
}

.s-STALE {
  background: var(--pa-color-status-stale);
}

/* Non-rule lenses reuse marker state keys only as an internal carrier for
 * clustering/selection. Their visible palette must express the active fact
 * dimension, never access morality ("green = allowed"). */
.map-surface--reality .s-ALLOWED,
.map-surface--reality .s-MATCH {
  background: var(--pa-color-reality-observed);
}

.map-surface--reality .s-STALE {
  background: var(--pa-color-reality-historical);
}

.map-surface--reality .s-UNKNOWN {
  background: var(--pa-color-reality-insufficient);
}

.map-surface--reality .s-CONFLICT {
  background: var(--pa-color-reality-disputed);
}

.map-surface--facility .s-ALLOWED,
.map-surface--facility .s-MATCH {
  background: var(--pa-color-facility-confirmed);
}

.map-surface--facility .s-UNKNOWN,
.map-surface--facility .s-STALE {
  background: var(--pa-color-facility-unverified);
}

.map-surface--facility .dot.s-CONDITIONAL {
  background: transparent;
  border-color: var(--pa-color-facility-unverified);
}

.map-surface--facility .map-cluster.s-CONDITIONAL {
  background: var(--pa-color-facility-unverified);
}

.map-surface--divergence .s-ALLOWED,
.map-surface--divergence .s-MATCH {
  background: var(--pa-color-reality-observed);
}

/* Cluster（数字聚合）保留实心语义填充；dot 的 CONDITIONAL 是环（见上）。 */
.map-cluster.s-CONDITIONAL {
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
