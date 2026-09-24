<script setup lang="ts">
/**
 * MapLoadingOverlay — loading affordance over the map surface (M2 §27).
 * The map frame stays mounted (stable structure); only the data layer shows
 * the loading state, so markers can fade in instead of replacing the page.
 */
defineOptions({ name: "MapLoadingOverlay" });

withDefaults(defineProps<{ label?: string }>(), { label: "正在加载地图" });
</script>

<template>
  <div class="map-loading-overlay" aria-busy="true" role="status">
    <span class="map-loading-overlay__spinner" aria-hidden="true" />
    <span class="map-loading-overlay__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.map-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--pa-space-2);
  background: var(--pa-color-bg-overlay);
  color: var(--pa-color-text-inverse);
  z-index: var(--pa-z-sticky);
}

.map-loading-overlay__spinner {
  width: var(--pa-size-icon-lg);
  height: var(--pa-size-icon-lg);
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: pa-rotate 0.8s linear infinite;
}

@keyframes pa-rotate {
  to {
    transform: rotate(360deg);
  }
}

.map-loading-overlay__label {
  font-size: var(--pa-font-size-md);
}

@media (prefers-reduced-motion: reduce) {
  .map-loading-overlay__spinner {
    animation: none;
  }
}
</style>