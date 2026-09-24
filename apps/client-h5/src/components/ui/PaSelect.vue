<script setup lang="ts">
import { useId } from "vue";
import PaIcon from "./PaIcon.vue";

defineOptions({ name: "PaSelect" });

export interface PaSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

withDefaults(
  defineProps<{
    modelValue: string;
    options: PaSelectOption[];
    label?: string;
    disabled?: boolean;
    placeholder?: string;
  }>(),
  { disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const selectId = useId();

function onChange(event: Event) {
  emit("update:modelValue", (event.target as HTMLSelectElement).value);
}
</script>

<template>
  <div class="pa-select">
    <label v-if="label" class="pa-select__label" :for="selectId">{{ label }}</label>
    <div class="pa-select__wrap">
      <select
        :id="selectId"
        class="pa-select__control"
        :value="modelValue"
        :disabled="disabled"
        :aria-disabled="disabled || undefined"
        @change="onChange"
      >
        <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
        <option
          v-for="option in options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </select>
      <PaIcon name="chevron-down" class="pa-select__chevron" aria-hidden="true" />
    </div>
  </div>
</template>

<style scoped>
.pa-select {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.pa-select__label {
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-secondary);
}

.pa-select__wrap {
  position: relative;
}

.pa-select__control {
  width: 100%;
  min-height: var(--pa-size-control-lg);
  padding-inline: var(--pa-space-3);
  padding-right: var(--pa-space-6);
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  appearance: none;
  cursor: pointer;
}

.pa-select__control:hover:not(:disabled):not(:focus) {
  border-color: var(--pa-color-border-strong);
}

.pa-select__control:focus {
  border-color: var(--pa-color-border-focus);
}

.pa-select__control:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-select__control:disabled {
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-disabled);
  cursor: not-allowed;
}

.pa-select__chevron {
  position: absolute;
  top: 50%;
  right: var(--pa-space-3);
  color: var(--pa-color-text-muted);
  transform: translateY(-50%);
  pointer-events: none;
}
</style>
