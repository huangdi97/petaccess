<script setup lang="ts">
defineOptions({ name: "PaDivider" });

type DividerSpacing = "sm" | "md" | "lg";

withDefaults(
  defineProps<{
    spacing?: DividerSpacing;
    label?: string;
  }>(),
  { spacing: "md" },
);
</script>

<template>
  <div class="pa-divider" :class="`pa-divider--${spacing}`">
    <hr role="separator" class="pa-divider__rule" />
    <span v-if="label" class="pa-divider__label">{{ label }}</span>
  </div>
</template>

<style scoped>
.pa-divider {
  position: relative;
}

.pa-divider--sm {
  margin-block: var(--pa-space-2);
}

.pa-divider--md {
  margin-block: var(--pa-space-4);
}

.pa-divider--lg {
  margin-block: var(--pa-space-5);
}

.pa-divider__rule {
  margin: 0;
  border: none;
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.pa-divider__label {
  position: absolute;
  top: 50%;
  left: 50%;
  padding-inline: var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-muted);
  background: var(--pa-color-surface);
  transform: translate(-50%, -50%);
}
</style>
