<script setup lang="ts">
/**
 * PaIcon — the single renderer for the fixed icon family
 * (V020_DESIGN_SYSTEM_SPEC §14). Glyph data lives in @petaccess/design-tokens
 * (ICONS); this component is the only place that draws them, so a page can
 * never hand-roll a one-off SVG or fall back to emoji.
 */
import { computed } from "vue";
import { ICONS, ICON_SIZES, type IconName, type IconSize } from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{
    name: IconName;
    size?: IconSize | number;
    /** Accessible name overrides aria-hidden; omit for purely decorative icons. */
    label?: string;
  }>(),
  { size: "md", label: undefined },
);

const glyph = computed(() => ICONS[props.name]);

const pixelSize = computed(() =>
  typeof props.size === "number" ? `${props.size}px` : `var(${ICON_SIZES[props.size]})`,
);
</script>

<template>
  <svg
    class="pa-icon"
    :style="{ width: pixelSize, height: pixelSize }"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    :aria-hidden="label ? undefined : 'true'"
    :aria-label="label"
    data-icon-name
  >
    <path v-for="(d, i) in glyph.paths" :key="i" :d="d" />
  </svg>
</template>
