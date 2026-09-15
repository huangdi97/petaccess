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

function project(lat: number, lng: number): { left: string; top: string } {
  const relX = 0.5 + (lng - props.camera.lng) / spanDeg.value;
  const relY = 0.5 - (lat - props.camera.lat) / (spanDeg.value * 0.62);
  return {
    left: `${Math.min(0.94, Math.max(0.06, relX)) * 100}%`,
    top: `${Math.min(0.88, Math.max(0.08, relY)) * 100}%`,
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
        <div class="dot" :class="'s-' + c.status"></div>
        <div class="lbl">{{ glyph(c.status) }}</div>
      </template>
    </div>
    <div v-if="!clusters.length" class="map-empty muted">当前视野内暂无已收录场所</div>
  </div>
</template>
