<script setup lang="ts">
import PaIcon from "./PaIcon.vue";

defineOptions({ name: "PaCheckbox" });

withDefaults(
  defineProps<{
    modelValue: boolean;
    label: string;
    disabled?: boolean;
    indeterminate?: boolean;
  }>(),
  { disabled: false, indeterminate: false },
);

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

function onChange(event: Event) {
  emit("update:modelValue", (event.target as HTMLInputElement).checked);
}
</script>

<template>
  <label
    class="pa-checkbox"
    :class="{
      'pa-checkbox--disabled': disabled,
      'pa-checkbox--indeterminate': indeterminate,
    }"
  >
    <input
      type="checkbox"
      class="pa-checkbox__input"
      :checked="modelValue"
      :indeterminate="indeterminate || undefined"
      :disabled="disabled"
      :aria-disabled="disabled || undefined"
      @change="onChange"
    />
    <span class="pa-checkbox__box" aria-hidden="true">
      <PaIcon
        v-if="modelValue && !indeterminate"
        name="check"
        size="sm"
        class="pa-checkbox__check"
      />
      <span v-else-if="indeterminate" class="pa-checkbox__dash"></span>
    </span>
    <span class="pa-checkbox__label">{{ label }}</span>
  </label>
</template>

<style scoped>
.pa-checkbox {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  min-height: var(--pa-size-control-lg);
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
  cursor: pointer;
}

.pa-checkbox__input {
  position: absolute;
  opacity: 0;
}

.pa-checkbox__box {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: var(--pa-size-icon-md);
  height: var(--pa-size-icon-md);
  border: var(--pa-border-width-strong) solid var(--pa-color-border-strong);
  border-radius: var(--pa-radius-sm);
  color: var(--pa-color-text-inverse);
}

.pa-checkbox__input:checked + .pa-checkbox__box,
.pa-checkbox--indeterminate .pa-checkbox__box {
  background: var(--pa-color-accent);
  border-color: var(--pa-color-accent);
}

.pa-checkbox__input:focus-visible + .pa-checkbox__box {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-checkbox__dash {
  width: var(--pa-space-2);
  height: var(--pa-border-width-strong);
  background: currentColor;
}

.pa-checkbox--disabled {
  cursor: not-allowed;
  color: var(--pa-color-text-disabled);
}

.pa-checkbox--disabled .pa-checkbox__box {
  background: var(--pa-color-surface-muted);
  border-color: var(--pa-color-border-subtle);
}
</style>
