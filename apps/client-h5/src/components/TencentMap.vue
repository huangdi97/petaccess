<script setup lang="ts">
/**
 * Optional Tencent GL basemap. Rule/Reality/Facility/Divergence semantics and
 * selection remain owned by the surrounding Spatial Workspace.
 */
import type { MapCamera, MapCluster } from "@petaccess/client-core";

import { useTencentMapRenderer } from "../composables/useTencentMapRenderer";

const props = withDefaults(
  defineProps<{
    clientKey: string;
    camera: MapCamera;
    clusters: MapCluster[];
    selectedId?: string | null;
    lens?: string;
  }>(),
  { selectedId: null, lens: "rule" },
);

const emit = defineEmits<{
  select: [cluster: MapCluster];
  zoom: [delta: number];
  "zoom-absolute": [zoom: number];
  error: [message: string];
}>();

const { host, providerLabel } = useTencentMapRenderer({
  clientKey: () => props.clientKey,
  camera: () => props.camera,
  clusters: () => props.clusters,
  selectedId: () => props.selectedId ?? null,
  lens: () => props.lens,
  onSelect: (cluster) => emit("select", cluster),
  onZoom: (zoom) => {
    if (Math.abs(zoom - props.camera.zoom) > 0.01) emit("zoom-absolute", zoom);
  },
  onError: (message) => emit("error", message),
});
</script>

<template>
  <div
    class="tencent-map"
    :class="`tencent-map--${lens}`"
    data-testid="map-surface"
    data-ui="real-map"
    aria-label="真实地图。场所列表与选中详情仍可通过页面中的结果面板访问。"
  >
    <div ref="host" class="tencent-map__host" aria-hidden="true"></div>
    <div class="tencent-map__wash" aria-hidden="true"></div>
    <span class="tencent-map__provider muted">{{ providerLabel }}</span>

    <div class="map-zoom" role="group" aria-label="缩放">
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
  </div>
</template>

<style scoped src="./TencentMap.css"></style>
