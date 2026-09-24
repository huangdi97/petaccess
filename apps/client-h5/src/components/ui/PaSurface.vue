<script setup lang="ts">
defineOptions({ name: "PaSurface" });

type SurfaceElevation = "none" | "raised";
type SurfacePadding = "none" | "sm" | "md" | "lg";

withDefaults(
  defineProps<{
    elevation?: SurfaceElevation;
    padding?: SurfacePadding;
    interactive?: boolean;
    setBorder?: boolean;
  }>(),
  { elevation: "none", padding: "md", interactive: false, setBorder: true },
);
</script>

<template>
  <div
    class="pa-surface"
    :class="[
      `pa-surface--elevation-${elevation}`,
      `pa-surface--padding-${padding}`,
      { 'pa-surface--interactive': interactive, 'pa-surface--no-border': !setBorder },
    ]"
  >
    <slot />
  </div>
</template>

<style scoped>
.pa-surface {
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
}

.pa-surface--no-border {
  border-color: transparent;
}

.pa-surface--elevation-raised {
  background: var(--pa-color-surface-raised);
  box-shadow: var(--pa-elevation-1);
}

.pa-surface--padding-none {
  padding: 0;
}

.pa-surface--padding-sm {
  padding: var(--pa-space-2);
}

.pa-surface--padding-md {
  padding: var(--pa-space-4);
}

.pa-surface--padding-lg {
  padding: var(--pa-space-5);
}

.pa-surface--interactive {
  cursor: pointer;
}

.pa-surface--interactive:hover {
  border-color: var(--pa-color-accent);
}

.pa-surface--interactive:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}
</style>
