<script setup lang="ts">
defineOptions({ name: "PaSwitch" });

withDefaults(
  defineProps<{
    modelValue: boolean;
    label?: string;
    disabled?: boolean;
  }>(),
  { disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

function onChange(event: Event) {
  emit("update:modelValue", (event.target as HTMLInputElement).checked);
}
</script>

<template>
  <label class="pa-switch" :class="{ 'pa-switch--disabled': disabled }">
    <span v-if="label" class="pa-switch__label">{{ label }}</span>
    <input
      type="checkbox"
      class="pa-switch__input"
      role="switch"
      :checked="modelValue"
      :aria-checked="modelValue"
      :disabled="disabled"
      @change="onChange"
    />
    <span class="pa-switch__track" aria-hidden="true">
      <span class="pa-switch__thumb"></span>
    </span>
  </label>
</template>

<style scoped>
.pa-switch {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: var(--pa-size-control-lg);
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
  cursor: pointer;
}

.pa-switch__label {
  flex: 1;
}

.pa-switch__input {
  position: absolute;
  opacity: 0;
}

.pa-switch__track {
  position: relative;
  flex-shrink: 0;
  width: var(--pa-space-7);
  height: var(--pa-space-5);
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-surface-muted);
  transition: background-color var(--pa-motion-fast) var(--pa-motion-ease);
}

.pa-switch__thumb {
  position: absolute;
  top: var(--pa-border-width-strong);
  left: var(--pa-border-width-strong);
  width: var(--pa-size-icon-md);
  height: var(--pa-size-icon-md);
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-text-inverse);
  box-shadow: var(--pa-elevation-1);
  transition: transform var(--pa-motion-fast) var(--pa-motion-ease);
}

.pa-switch__input:checked + .pa-switch__track {
  background: var(--pa-color-accent);
}

.pa-switch__input:checked + .pa-switch__track .pa-switch__thumb {
  transform: translateX(var(--pa-space-5));
}

.pa-switch__input:focus-visible + .pa-switch__track {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-switch--disabled {
  cursor: not-allowed;
  color: var(--pa-color-text-disabled);
}

.pa-switch--disabled .pa-switch__track {
  opacity: 0.5;
}
</style>
