<script setup lang="ts">
/**
 * PaMetadataRow —one key/value line (V020 catalog #28). A border-bottom
 * divider separates stacked rows; the divider is dropped on the last row.
 * `mono` switches numeric values to the numeric font family.
 */
withDefaults(
  defineProps<{
    label: string;
    value?: string | number | null;
    mono?: boolean;
  }>(),
  { value: null, mono: false },
);

defineOptions({ name: "PaMetadataRow" });
</script>

<template>
  <div class="pa-metadata">
    <span class="pa-metadata__label">{{ label }}</span>
    <span
      v-if="value !== null && value !== undefined"
      class="pa-metadata__value"
      :class="{ 'pa-metadata__value--mono': mono }"
    >
      {{ value }}
    </span>
  </div>
</template>

<style scoped>
.pa-metadata {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.pa-metadata:last-child {
  border-bottom: none;
}

.pa-metadata__label {
  flex-shrink: 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.pa-metadata__value {
  font-size: var(--pa-font-size-md);
  text-align: right;
  color: var(--pa-color-text-primary);
}

.pa-metadata__value--mono {
  font-family: var(--pa-font-family-numeric);
}
</style>
