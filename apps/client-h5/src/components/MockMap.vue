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
import { computed, ref } from "vue";
import {
  MAP_MAX_ZOOM,
  MAP_MIN_ZOOM,
  type MapCamera,
  type MapCluster,
  type MapMarker,
} from "@petaccess/client-core";
import { mapLensGlyph } from "../consumer/mapLens";

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

const emit = defineEmits<{
  select: [cluster: MapCluster];
  zoom: [delta: number];
  pan: [lat: number, lng: number];
}>();

/** Approximate longitude span of a ~desktop map viewport.
 * Web maps scale by 2× per zoom level; keeping the fallback on the same
 * exponential model prevents nearby results from collapsing onto the edge and
 * makes +/- a real spatial zoom rather than a decorative control. */
const spanDeg = computed(() => 0.08 * Math.pow(2, 14 - props.camera.zoom));

// The fallback background is illustrative, not a surveyed basemap.
// Showing a metric scale bar on synthetic streets would imply unsupported
// positional/measurement accuracy.
const scaleLabel = computed(() => `缩放 ${Math.round(props.camera.zoom)} 级 · 示意比例`);

/** Only on-viewport clusters receive marker DOM; no out-of-range point can
 * be clamped into a false edge location. The list still contains all nearby
 * locations even when they are beyond this zoom's current view. */
const visibleClusters = computed(() =>
  props.clusters.filter(
    (cluster) =>
      Math.abs(cluster.lng - props.camera.lng) <= spanDeg.value / 2 &&
      Math.abs(cluster.lat - props.camera.lat) <= (spanDeg.value * 0.62) / 2,
  ),
);

/** Projection, clamped only for an actually visible edge point. */
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

const dragStart = ref<{ x: number; y: number; pointerId: number } | null>(null);
const dragging = ref(false);

function startPan(event: PointerEvent) {
  if (event.button !== 0) return;
  if ((event.target as HTMLElement).closest(".map-pin, .map-zoom, button, input")) return;
  dragStart.value = { x: event.clientX, y: event.clientY, pointerId: event.pointerId };
  (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
}

function updatePan(event: PointerEvent) {
  if (dragStart.value?.pointerId !== event.pointerId) return;
  dragging.value =
    Math.hypot(event.clientX - dragStart.value.x, event.clientY - dragStart.value.y) > 8;
}

function endPan(event: PointerEvent) {
  const start = dragStart.value;
  if (!start || start.pointerId !== event.pointerId) return;
  const el = event.currentTarget as HTMLElement;
  if (el.hasPointerCapture(event.pointerId)) el.releasePointerCapture(event.pointerId);
  dragStart.value = null;
  dragging.value = false;
  const dx = event.clientX - start.x;
  const dy = event.clientY - start.y;
  if (Math.hypot(dx, dy) <= 8) return;
  const bounds = el.getBoundingClientRect();
  if (!bounds.width || !bounds.height) return;

  const lat = Math.max(
    -90,
    Math.min(90, props.camera.lat + (dy / bounds.height) * spanDeg.value * 0.62),
  );
  const lng = props.camera.lng - (dx / bounds.width) * spanDeg.value;
  emit("pan", lat, ((((lng + 180) % 360) + 360) % 360) - 180);
}

function cancelPan() {
  dragStart.value = null;
  dragging.value = false;
}

const glyph = (status: MapMarker["status"]) => mapLensGlyph(props.lens, status);

function markerLabel(cluster: MapCluster): string {
  if (cluster.count > 1) return `${cluster.count} 个场所`;
  const id = cluster.memberIds[0];
  return id ? (props.lensLabels[id] ?? "信息不足") : "信息不足";
}

function isSelectedCluster(cluster: MapCluster): boolean {
  return props.selectedId ? cluster.memberIds.includes(props.selectedId) : false;
}

/* ---- Abstract urban spatial canvas (v0.2.7 §8) -------------------------
 * Everything is pure decoration; no data semantics live here. The palette
 * stays very light cool neutral and low-contrast so the map never competes
 * with rule/reality/selected place. */
const DISTRICT =
  "M 10 10 Q 58 2 108 12 T 208 8 Q 248 10 254 42 L 252 214 Q 244 250 204 254 L 48 252 Q 12 246 8 208 Z";
const RIVER =
  "M -8 54 C 42 42 86 64 132 56 S 216 36 270 54 L 270 78 C 214 62 176 82 132 82 S 42 68 -8 84 Z";
/** Soft open-space patches are illustrative only; they carry no venue facts. */
const OPEN_SPACES = [
  "M 154 118 C 170 102 198 104 210 122 C 222 140 212 162 190 168 C 168 174 146 158 144 138 C 142 130 146 124 154 118 Z",
  "M 24 26 C 38 18 58 20 68 34 C 76 46 68 62 52 66 C 36 70 20 60 18 46 C 16 38 18 32 24 26 Z",
  "M 214 132 C 226 124 244 126 250 140 C 256 152 248 166 234 170 C 220 172 208 162 208 150 C 208 142 210 136 214 132 Z",
];
const PLAZAS = ["100,30 134,28 138,52 104,56", "158,34 190,32 194,54 160,58"];
const BLOCKS = [
  "18,94 66,88 72,126 24,132",
  "84,88 126,84 130,122 88,126",
  "18,146 72,140 76,184 22,190",
  "88,144 132,140 136,184 92,188",
  "16,204 78,198 82,238 22,244",
  "96,202 142,198 146,238 100,242",
  "154,88 202,84 208,112 160,118",
  "218,84 252,82 254,118 222,120",
  "158,182 202,178 208,218 164,224",
  "218,178 252,176 254,218 222,222",
  "154,232 202,228 204,250 158,252",
  "216,230 252,228 252,250 218,252",
];
/** Road hierarchy: broad curved arterials plus quieter local streets. */
const ROADS_PRIMARY = [
  "M -10 136 C 54 126 102 132 150 118 S 220 96 270 104",
  "M 146 -10 C 150 54 144 104 152 156 S 174 224 170 270",
];
const ROADS_SECONDARY = [
  "M -8 196 C 54 188 104 192 150 184 S 220 160 270 166",
  "M 72 -8 C 74 44 78 86 82 128 S 86 220 92 270",
  "M 214 -8 C 212 44 214 86 218 128 S 222 220 228 270",
  "M 10 76 C 70 72 122 74 166 66 S 222 52 260 58",
  "M 12 238 C 60 232 106 234 144 228",
];
const ROADS_LOCAL = [
  "M 22 118 L 68 114",
  "M 92 112 L 126 108",
  "M 28 174 L 70 170",
  "M 96 172 L 132 168",
  "M 166 104 L 200 100",
  "M 166 206 L 202 202",
  "M 230 102 L 250 100",
  "M 230 206 L 250 204",
  "M 46 88 L 50 126",
  "M 108 84 L 112 122",
  "M 48 142 L 52 184",
  "M 112 140 L 116 184",
  "M 180 84 L 184 114",
  "M 182 180 L 186 220",
  "M 236 82 L 238 118",
  "M 238 178 L 240 218",
];
/** Building mass hints: many small footprints create city texture without
 * claiming a surveyed street/building plan. */
const MASS = [
  "28,102,12,9",
  "46,99,12,9",
  "94,96,12,10",
  "112,94,10,10",
  "30,154,14,10",
  "52,150,12,12",
  "98,150,12,10",
  "116,148,12,12",
  "30,214,14,10",
  "52,210,14,11",
  "106,210,12,10",
  "124,208,10,12",
  "166,94,14,9",
  "186,91,12,10",
  "228,92,12,10",
  "168,192,14,11",
  "188,188,12,12",
  "228,190,14,10",
  "168,238,12,8",
  "188,236,12,9",
  "228,236,12,9",
];
</script>
<template>
  <div
    class="map-surface"
    :class="[`map-surface--${lens}`, { 'map-surface--dragging': dragging }]"
    data-testid="map-surface"
    data-ui="mock-map"
    aria-label="简化空间底图，可拖动调整附近查询区域"
    @pointerdown="startPan"
    @pointermove="updatePan"
    @pointerup="endPan"
    @pointercancel="cancelPan"
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
      <path class="basemap-river" :d="RIVER" />
      <path v-for="p in OPEN_SPACES" :key="'open-' + p" class="basemap-open" :d="p" />
      <polygon v-for="p in PLAZAS" :key="'plaza-' + p" class="basemap-plaza" :points="p" />
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
      <path
        v-for="r in ROADS_PRIMARY"
        :key="'primary-casing-' + r"
        class="basemap-road basemap-road--primary-casing"
        :d="r"
      />
      <path
        v-for="r in ROADS_PRIMARY"
        :key="'primary-fill-' + r"
        class="basemap-road basemap-road--primary"
        :d="r"
      />
      <path
        v-for="r in ROADS_SECONDARY"
        :key="'secondary-casing-' + r"
        class="basemap-road basemap-road--secondary-casing"
        :d="r"
      />
      <path
        v-for="r in ROADS_SECONDARY"
        :key="'secondary-fill-' + r"
        class="basemap-road basemap-road--secondary"
        :d="r"
      />
      <path
        v-for="r in ROADS_LOCAL"
        :key="'local-' + r"
        class="basemap-road basemap-road--local"
        :d="r"
      />
    </svg>

    <span class="map-provider muted" data-testid="map-provider-fallback">
      示意底图（非真实街道） · 拖动查看周边
    </span>

    <div class="map-spatial-aids" aria-hidden="true">
      <span class="map-compass">N</span>
      <span class="map-scale">{{ scaleLabel }}</span>
    </div>

    <div class="map-zoom" data-testid="map-zoom" data-ui="map-zoom" role="group" aria-label="缩放">
      <button
        type="button"
        aria-label="放大"
        :disabled="camera.zoom >= MAP_MAX_ZOOM"
        @click="emit('zoom', 1)"
      >
        ＋
      </button>
      <button
        type="button"
        aria-label="缩小"
        :disabled="camera.zoom <= MAP_MIN_ZOOM"
        @click="emit('zoom', -1)"
      >
        －
      </button>
    </div>

    <div
      v-for="c in visibleClusters"
      :key="c.id"
      class="map-pin"
      :class="{ 'map-pin--selected': isSelectedCluster(c) }"
      :data-selected="isSelectedCluster(c) ? 'true' : undefined"
      :data-ui="c.count > 1 ? 'map-marker' : undefined"
      :style="project(c.lat, c.lng)"
      :data-testid="c.count > 1 ? 'cluster-' + c.id : 'pin-' + c.memberIds[0]"
      :aria-label="
        c.count > 1
          ? `${c.count} 个场所；准入结论需分别查看，放大可展开`
          : `1 个场所，${markerLabel(c)}`
      "
      role="button"
      tabindex="0"
      @click="emit('select', c)"
      @keydown.enter="emit('select', c)"
      @keydown.space.prevent="emit('select', c)"
    >
      <template v-if="c.count > 1">
        <!-- Aggregate counts have no single policy state. Always neutral;
             a priority status must not be attributed to all member places. -->
        <div
          class="map-cluster"
          :class="{ 'map-cluster--selected': isSelectedCluster(c) }"
          :data-ui="isSelectedCluster(c) ? 'map-marker-selected' : 'map-marker'"
          :data-selected="isSelectedCluster(c) ? 'true' : undefined"
        >
          {{ c.count }}
        </div>
      </template>
      <template v-else>
        <!-- Status is never color-only: the compact marker carries a single
             shape glyph; full semantic copy stays horizontal in the label,
             results pane and selected preview. Never put words inside the dot. -->
        <div class="lbl" :class="'s-' + c.status">
          {{ markerLabel(c) }}
        </div>
        <div
          class="dot"
          :class="['s-' + c.status, { 'dot--selected': isSelectedCluster(c) }]"
          :data-ui="isSelectedCluster(c) ? 'map-marker-selected' : 'map-marker'"
        >
          <span class="dot__glyph" aria-hidden="true">{{ glyph(c.status) }}</span>
        </div>
      </template>
    </div>
    <div v-if="!visibleClusters.length" class="map-empty muted">
      当前画面暂无点位；附近结果仍可在列表查看
    </div>
  </div>
</template>

<style scoped>
.map-surface {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 480px;
  overflow: hidden;
  cursor: grab;
  touch-action: none;
}

.map-surface--dragging {
  cursor: grabbing;
}

/* 空间基底：轻量抽象城市画布 —— 不是灰网格+数字（v0.2.7 §8）。 */
.map-basemap {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  /*
   * The fallback must still read as a city-space product. Keep it quieter than
   * a real provider, but give blocks, open space and road hierarchy enough
   * contrast that the canvas does not collapse into a pale test grid.
   */
  background: color-mix(in srgb, var(--pa-color-map-grid-a) 82%, var(--pa-discovery-v10-paper));
}

.basemap-district {
  fill: color-mix(in srgb, var(--pa-color-surface) 42%, transparent);
  stroke: var(--pa-color-border);
  stroke-width: 1.5;
  opacity: 0.9;
}

.basemap-open {
  fill: var(--pa-color-status-allowed-bg);
  opacity: 0.62;
}

.basemap-plaza {
  fill: var(--pa-discovery-v10-secondary-bg);
  stroke: var(--pa-color-border-subtle);
  stroke-width: 0.8;
  opacity: 0.92;
}

.basemap-river {
  fill: var(--pa-color-reality-observed-bg);
  opacity: 0.66;
}

.basemap-block {
  fill: var(--pa-color-surface);
  opacity: 0.9;
  stroke: var(--pa-color-border);
  stroke-width: 0.75;
}

/* Building mass hints add urban density without claiming surveyed geometry. */
.basemap-mass {
  fill: var(--pa-color-text-muted);
  opacity: 0.13;
}

/* 道路层级：primary 更宽更明确，secondary 更细更弱。 */
.basemap-road {
  fill: none;
  vector-effect: non-scaling-stroke;
}

.basemap-road--primary-casing {
  stroke: var(--pa-color-border-strong);
  stroke-width: 8;
  opacity: 0.48;
}

.basemap-road--primary {
  stroke: var(--pa-color-surface);
  stroke-width: 5;
  opacity: 1;
}

.basemap-road--secondary-casing {
  stroke: var(--pa-color-border);
  stroke-width: 4;
  opacity: 0.58;
}

.basemap-road--secondary {
  stroke: var(--pa-color-surface);
  stroke-width: 2;
  opacity: 0.96;
}

.basemap-road--local {
  stroke: var(--pa-color-border-subtle);
  stroke-width: 1;
  opacity: 0.9;
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

.map-spatial-aids {
  position: absolute;
  right: var(--pa-space-3);
  bottom: var(--pa-space-3);
  z-index: 2;
  display: flex;
  align-items: flex-end;
  gap: var(--pa-space-3);
  color: var(--pa-color-text-secondary);
  pointer-events: none;
}

.map-compass {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-pill);
  background: color-mix(in srgb, var(--pa-color-surface) 92%, transparent);
  font-family: var(--pa-font-family-numeric);
  font-size: var(--pa-font-size-xs);
  font-weight: var(--pa-font-weight-650);
}

.map-scale {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  padding: 2px var(--pa-space-1);
  border-radius: var(--pa-radius-sm);
  background: color-mix(in srgb, var(--pa-color-surface) 88%, transparent);
  font-family: var(--pa-font-family-numeric);
  font-size: var(--pa-font-size-xs);
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
  /* The visible label must not cover another nearby dot's hit target.
     Only the actual marker glyph receives the pointer; keyboard users
     can still focus the parent as a single labelled control. */
  pointer-events: none;
}

.map-pin .dot,
.map-pin .map-cluster {
  pointer-events: auto;
}

.map-pin:focus-visible,
.map-pin:hover {
  z-index: 4;
}

.map-pin--selected {
  z-index: 3;
}

.map-cluster {
  background: var(--pa-color-text-secondary);
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

.map-cluster--selected {
  min-width: 30px;
  height: 30px;
  box-shadow:
    0 0 0 4px var(--pa-color-accent-weak),
    var(--pa-elevation-2);
}

.lbl {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  white-space: nowrap;
  background: var(--pa-color-map-label-bg);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-sm);
  padding: 1px var(--pa-space-1);
  color: var(--pa-color-text-primary);
  opacity: 0;
  transform: translateY(2px);
  pointer-events: none;
  transition:
    opacity var(--pa-motion-fast) var(--pa-motion-ease),
    transform var(--pa-motion-fast) var(--pa-motion-ease);
}

.map-pin:hover .lbl,
.map-pin:focus-visible .lbl,
.map-pin--selected .lbl {
  opacity: 1;
  transform: translateY(0);
}

/* v0.2.7 §10 marker 系统：
 * - UNKNOWN      = neutral fill
 * - CONDITIONAL  = subtle amber ring（空心圆 + 琥珀描边）
 * - ALLOWED      = subtle positive fill
 * - RESTRICTED   = subtle restriction fill
 * - SELECTED     = scale 1.33x + halo + elevation（dot--selected）
 */
.dot {
  width: 18px;
  height: 18px;
  border-radius: var(--pa-radius-pill);
  border: 2px solid var(--pa-color-map-pin-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--pa-color-text-inverse);
  font-family: var(--pa-font-family-numeric);
  font-size: 10px;
  font-weight: var(--pa-font-weight-bold);
  line-height: 1;
  transition:
    box-shadow var(--pa-motion-fast) var(--pa-motion-ease),
    transform var(--pa-motion-fast) var(--pa-motion-ease);
}

.dot__glyph {
  transform: translateY(-0.5px);
}

.dot.s-CONDITIONAL {
  background: var(--pa-color-surface);
  border-width: 3px;
  border-color: var(--pa-color-status-conditional);
  color: var(--pa-color-status-conditional);
}

.dot.s-UNKNOWN {
  background: var(--pa-color-surface);
  color: var(--pa-color-status-unknown);
}

.dot.s-RESTRICTED {
  border-radius: 5px;
}

.dot.s-CONFLICT {
  border-radius: 4px;
  transform: rotate(45deg);
}

.dot.s-CONFLICT .dot__glyph {
  transform: rotate(-45deg) translateY(-0.5px);
}

.dot.s-STALE {
  background: var(--pa-color-surface);
  border-style: dashed;
  color: var(--pa-color-status-stale);
}

.dot--selected {
  width: 22px;
  height: 22px;
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

/* Text labels stay neutral. Semantic tone belongs to the marker shape; this
 * avoids turning hover labels into a traffic-light UI. */
.lbl.s-ALLOWED,
.lbl.s-MATCH,
.lbl.s-CONDITIONAL,
.lbl.s-RESTRICTED,
.lbl.s-UNKNOWN,
.lbl.s-CONFLICT,
.lbl.s-STALE,
.map-surface--reality .lbl,
.map-surface--facility .lbl,
.map-surface--divergence .lbl {
  background: var(--pa-color-map-label-bg);
  color: var(--pa-color-text-primary);
  border-color: var(--pa-color-border-subtle);
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
