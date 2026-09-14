<script setup lang="ts">
/**
 * Loading placeholder (Master Goal §5.5 — skeleton state).
 *
 * Shape-matched placeholders reduce layout shift compared with a spinner, and
 * the shimmer is disabled under `prefers-reduced-motion` (see styles.css).
 */
withDefaults(
  defineProps<{
    /** How many placeholder rows to draw. */
    rows?: number;
    /** `card` mirrors a list item, `line` is a bare text line. */
    variant?: "card" | "line";
  }>(),
  { rows: 3, variant: "card" },
);
</script>

<template>
  <div class="skeleton-list" :data-testid="'skeleton-' + variant" aria-busy="true" aria-live="polite">
    <div v-for="i in rows" :key="i" class="skeleton" :class="'skeleton--' + variant">
      <span class="visually-hidden">加载中</span>
    </div>
  </div>
</template>
