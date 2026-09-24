<script setup lang="ts">
/**
 * PaSkeleton — tokenised loading placeholder (V020 catalog #22). The sheen is
 * the same pa-shimmer used by the app stylesheet; scoped keyframes get
 * rewritten per component, so it never collides with the global animation.
 */
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    variant: "line" | "card" | "circle";
    /** CSS width; a number is treated as px. Defaults to 100%. */
    width?: string | number;
    /** CSS height; a number is treated as px. */
    height?: string | number;
  }>(),
  { width: undefined, height: undefined },
);

defineOptions({ name: "PaSkeleton" });

function cssSize(v: string | number): string {
  return typeof v === "number" ? `${v}px` : v;
}

const style = computed(() => ({
  width: props.width != null ? cssSize(props.width) : "100%",
  height:
    props.height != null ? cssSize(props.height) : props.variant === "card" ? "64px" : undefined,
}));
</script>

<template>
  <div
    class="pa-skeleton"
    :class="`pa-skeleton--${variant}`"
    :style="style"
    aria-hidden="true"
  ></div>
</template>

<style scoped>
.pa-skeleton {
  position: relative;
  overflow: hidden;
  background: var(--pa-color-bg-sunken);
  border-radius: var(--pa-radius-sm);
}

.pa-skeleton--card {
  border-radius: var(--pa-radius-md);
}

.pa-skeleton--circle {
  border-radius: 50%;
}

.pa-skeleton::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, var(--pa-color-skeleton-sheen), transparent);
  animation: pa-shimmer var(--pa-motion-slow) var(--pa-motion-ease) infinite;
}

@keyframes pa-shimmer {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(100%);
  }
}

/* The shimmer is decorative; freeze it for reduced-motion users. */
@media (prefers-reduced-motion: reduce) {
  .pa-skeleton::after {
    animation: none;
  }
}
</style>
