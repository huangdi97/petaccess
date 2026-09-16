<script setup lang="ts">
/**
 * Mock map renderer (MapProvider adapter, ADR-008).
 *
 * Renders provider-neutral clusters/markers projected around the camera. It is
 * a *renderer only*: clustering, coverage and location state live in
 * `@petaccess/client-core` so switching to the Tencent SDK replaces this
 * component and nothing else.
 */
import { computed } from "vue";
import type { MapCamera, MapCluster, MapPolygon, MapMarker } from "@petaccess/client-core";
import { STATUS_GLYPHS } from "@petaccess/client-core";

const props = withDefaults(
  defineProps<{
    camera: MapCamera;
    clusters: MapCluster[];
    selectedId?: string | null;
    polygons?: MapPolygon[];
  }>(),
  { selectedId: null, polygons: () => [] },
);

const emit = defineEmits<{ select: [cluster: MapCluster] }>();

/** Degrees of longitude visible at this zoom (deterministic, provider-free). */
const spanDeg = computed(() => 0.02 / Math.max(1, props.camera.zoom / 14));

/**
 * Projection, clamped so the whole pin box stays inside the surface.
 *
 * A pin is drawn *above* its anchor (`.map-pin` is `translate(-50%, -100%)`),
 * so clamping the anchor to 8% of the 260px surface put the top row of pins at
 * y = -23: `overflow: hidden` cut each pin in half, and the topmost pin's centre
 * landed on the container's edge, where the topmost element at that point is
 * `.map-mock` rather than the pin. Playwright said so in as many words
 * (".map-mock intercepts pointer events") — which is exactly what a thumb aimed
 * at the middle of that marker would also hit.
 *
 * The reserve is expressed in CSS px via `clamp()`, not as a percentage: the
 * room a pin needs above its anchor is 44px regardless of how wide or tall the
 * surface happens to be, and only the browser knows that width. The two numbers
 * mirror `.map-pin { min-height: 44px }` and half of its 63px-wide label box.
 */
const PIN_HEIGHT_PX = 44;
const PIN_HALF_WIDTH_PX = 32;
/** Keeps pins off the bottom edge, where `.map-mock`'s border sits. */
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
</script>

<template>
  <div class="map-surface" data-testid="map-surface">
    <div
      v-for="c in clusters"
      :key="c.id"
      class="map-pin"
      :class="{ 'map-pin--selected': selectedId === c.memberIds[0] }"
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
        <!-- Label first, dot second. The pin is drawn above its anchor
             (`translate(-50%, -100%)`) and `.map-pin` uses
             `justify-content: flex-end`, so the *last* child ends up on the
             anchor. With the dot first, the label — not the pin tip — sat on
             the coordinate and the teardrop floated above it. -->
        <div class="lbl">{{ glyph(c.status) }}</div>
        <div class="dot" :class="'s-' + c.status"></div>
      </template>
    </div>
    <div v-if="!clusters.length" class="map-empty muted">当前视野内暂无已收录场所</div>
  </div>
</template>
