<script setup lang="ts">
/**
 * DesktopContentContainer — the three desktop content layouts
 * (V020_APP_SHELL_SPEC §17). Replaces the "390px mobile column centered on a
 * 1440px screen" anti-pattern:
 *   - single-column: readable narrow column for detail pages
 *   - wide: content flows to the desktop max width (home, search results)
 *   - split: two panes sharing the row (search list + preview, map + detail)
 */
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    mode?: "single-column" | "wide" | "split";
  }>(),
  { mode: "single-column" },
);

const cls = computed(() => `desktop-content desktop-content--${props.mode}`);
</script>

<template>
  <div :class="cls">
    <slot />
  </div>
</template>

<style scoped>
.desktop-content {
  width: 100%;
  margin: 0 auto;
  padding-inline: var(--pa-layout-content-gutter);
}

.desktop-content--single-column {
  max-width: var(--pa-layout-content-narrow);
}

.desktop-content--wide {
  max-width: var(--pa-layout-content-max);
}

.desktop-content--split {
  max-width: var(--pa-layout-content-max);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--pa-space-6);
  align-items: start;
}

@media (max-width: 767px) {
  .desktop-content {
    padding-inline: 0;
  }
}
</style>
