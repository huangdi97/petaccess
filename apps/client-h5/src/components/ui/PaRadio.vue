<script setup lang="ts">
defineOptions({ name: "PaRadio" });

withDefaults(
  defineProps<{
    modelValue: string;
    value: string;
    label: string;
    disabled?: boolean;
  }>(),
  { disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: string] }>();
</script>

<template>
  <label class="pa-radio" :class="{ 'pa-radio--disabled': disabled }">
    <input
      type="radio"
      class="pa-radio__input"
      :checked="modelValue === value"
      :value="value"
      :disabled="disabled"
      :aria-disabled="disabled || undefined"
      @change="emit('update:modelValue', value)"
    />
    <span class="pa-radio__box" aria-hidden="true"></span>
    <span class="pa-radio__label">{{ label }}</span>
  </label>
</template>

<style scoped>
.pa-radio {
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

.pa-radio__input {
  position: absolute;
  opacity: 0;
}

.pa-radio__box {
  position: relative;
  flex-shrink: 0;
  width: var(--pa-size-icon-md);
  height: var(--pa-size-icon-md);
  border: var(--pa-border-width-strong) solid var(--pa-color-border-strong);
  border-radius: var(--pa-radius-pill);
  color: var(--pa-color-accent);
}

.pa-radio__box::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: var(--pa-space-2);
  height: var(--pa-space-2);
  border-radius: var(--pa-radius-pill);
  background: currentColor;
  transform: translate(-50%, -50%) scale(0);
  transition: transform var(--pa-motion-fast) var(--pa-motion-ease);
}

.pa-radio__input:checked + .pa-radio__box {
  border-color: var(--pa-color-accent);
}

.pa-radio__input:checked + .pa-radio__box::after {
  transform: translate(-50%, -50%) scale(1);
}

.pa-radio__input:focus-visible + .pa-radio__box {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-radio--disabled {
  cursor: not-allowed;
  color: var(--pa-color-text-disabled);
}

.pa-radio--disabled .pa-radio__box {
  border-color: var(--pa-color-border-subtle);
}
</style>
