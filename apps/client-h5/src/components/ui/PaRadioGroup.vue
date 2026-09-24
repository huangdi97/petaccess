<script setup lang="ts">
import PaRadio from "./PaRadio.vue";

defineOptions({ name: "PaRadioGroup" });

export interface PaRadioGroupOption {
  value: string;
  label: string;
  disabled?: boolean;
}

withDefaults(
  defineProps<{
    modelValue: string;
    options: PaRadioGroupOption[];
    inline?: boolean;
    ariaLabel?: string;
    disabled?: boolean;
  }>(),
  { inline: false, disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <fieldset class="pa-radio-group" :class="{ 'pa-radio-group--inline': inline }">
    <legend class="visually-hidden">{{ ariaLabel }}</legend>
    <PaRadio
      v-for="option in options"
      :key="option.value"
      :model-value="modelValue"
      :value="option.value"
      :label="option.label"
      :disabled="disabled || option.disabled"
      @update:model-value="emit('update:modelValue', $event)"
    />
  </fieldset>
</template>

<style scoped>
.pa-radio-group {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin: 0;
  padding: 0;
  border: none;
}

.pa-radio-group--inline {
  flex-direction: row;
  flex-wrap: wrap;
  gap: var(--pa-space-3);
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
