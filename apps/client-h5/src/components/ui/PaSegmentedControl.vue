<script setup lang="ts">
defineOptions({ name: "PaSegmentedControl" });

type SegmentedSize = "sm" | "md" | "lg";

export interface PaSegmentedOption {
  value: number | string;
  label: string;
}

withDefaults(
  defineProps<{
    modelValue: number | string;
    options: PaSegmentedOption[];
    ariaLabel?: string;
    disabled?: boolean;
    size?: SegmentedSize;
  }>(),
  { size: "md", disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: number | string] }>();
</script>

<template>
  <div class="pa-segmented" :class="`pa-segmented--${size}`" role="group" :aria-label="ariaLabel">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="pa-segmented__option"
      :class="{ 'pa-segmented__option--active': option.value === modelValue }"
      :aria-pressed="option.value === modelValue"
      :disabled="disabled"
      :aria-disabled="disabled || undefined"
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<style scoped>
.pa-segmented {
  display: flex;
  padding: var(--pa-space-1);
  background: var(--pa-color-surface-muted);
  border-radius: var(--pa-radius-pill);
}

.pa-segmented__option {
  flex: 1;
  min-height: var(--pa-size-control-md);
  padding-inline: var(--pa-space-3);
  border: none;
  border-radius: var(--pa-radius-pill);
  background: transparent;
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-secondary);
  cursor: pointer;
  transition:
    background-color var(--pa-motion-fast) var(--pa-motion-ease),
    box-shadow var(--pa-motion-fast) var(--pa-motion-ease),
    color var(--pa-motion-fast) var(--pa-motion-ease);
}

.pa-segmented__option:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-segmented__option--active {
  background: var(--pa-color-surface-raised);
  box-shadow: var(--pa-elevation-1);
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-medium);
}

.pa-segmented__option:disabled {
  cursor: not-allowed;
  color: var(--pa-color-text-disabled);
}

.pa-segmented--sm .pa-segmented__option {
  min-height: var(--pa-size-control-sm);
  font-size: var(--pa-font-size-sm);
}

.pa-segmented--lg .pa-segmented__option {
  min-height: var(--pa-size-control-lg);
}
</style>
