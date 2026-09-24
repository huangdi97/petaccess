<script setup lang="ts">
/**
 * PaSpinner — indeterminate loading indicator (V020 catalog #23).
 * role="status" with a visually-hidden label; the rotation speed is fixed
 * (0.8s) because it is functional feedback, not decoration.
 */
import { computed } from "vue";
import { ICON_SIZES } from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{
    size?: "sm" | "md" | "lg";
    label?: string;
  }>(),
  { size: "md", label: "加载中" },
);

defineOptions({ name: "PaSpinner" });

const dimension = computed(() => `var(${ICON_SIZES[props.size]})`);
</script>

<template>
  <span class="pa-spinner" :style="{ width: dimension, height: dimension }" role="status">
    <span class="visually-hidden">{{ label }}</span>
  </span>
</template>

<style scoped>
.pa-spinner {
  display: inline-block;
  border: var(--pa-border-width-strong) solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: pa-rotate 0.8s linear infinite;
}

@keyframes pa-rotate {
  to {
    transform: rotate(360deg);
  }
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}
</style>
