<script setup lang="ts">
import { computed } from "vue";
import type { MapCamera, PlaceSummary } from "@petaccess/client-core";

const props = defineProps<{ camera: MapCamera; places: PlaceSummary[] }>();
defineEmits<{ select: [id: string] }>();

/**
 * Mock map renderer: deterministic pseudo-positions derived from place id,
 * projected around the camera. Swapping to Tencent JS SDK only replaces this
 * component (MapProvider adapter, ADR-008) — data flow and statuses identical.
 */
const spanDeg = computed(() => 0.02 / Math.max(1, props.camera.zoom / 14));

function pos(p: PlaceSummary): { left: string; top: string } {
  let h = 0;
  for (const c of p.id) h = (h * 31 + c.charCodeAt(0)) % 1000;
  const dx = ((h % 14) - 7) / 10; // -0.7..0.7
  const dy = ((Math.floor(h / 14) % 12) - 6) / 10;
  const relX = 0.5 + dx / spanDeg.value / 10;
  const relY = 0.5 - dy / (spanDeg.value * 0.6) / 10;
  return {
    left: `${Math.min(0.92, Math.max(0.08, relX)) * 100}%`,
    top: `${Math.min(0.85, Math.max(0.1, relY)) * 100}%`,
  };
}
</script>

<template>
  <div>
    <div
      v-for="p in places"
      :key="p.id"
      class="map-pin"
      :style="pos(p)"
      :data-testid="'pin-' + p.canonical_name"
      @click="$emit('select', p.id)"
    >
      <div class="dot s-UNKNOWN"></div>
      <div class="lbl">{{ p.canonical_name }}</div>
    </div>
  </div>
</template>
