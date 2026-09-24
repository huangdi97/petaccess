<script setup lang="ts">
import { useId } from "vue";

defineOptions({ name: "PaTextInput" });

withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    label?: string;
    helper?: string;
    error?: string;
    disabled?: boolean;
    type?: string;
  }>(),
  { type: "text", disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const inputId = useId();
const messageId = useId();

function onInput(event: Event) {
  emit("update:modelValue", (event.target as HTMLInputElement).value);
}
</script>

<template>
  <div class="pa-field">
    <label v-if="label" class="pa-field__label" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      class="pa-field__control"
      :class="{ 'pa-field__control--error': !!error }"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :aria-disabled="disabled || undefined"
      :aria-invalid="error ? true : undefined"
      :aria-describedby="error || helper ? messageId : undefined"
      @input="onInput"
    />
    <p v-if="error" :id="messageId" class="pa-field__message pa-field__message--error">
      {{ error }}
    </p>
    <p v-else-if="helper" :id="messageId" class="pa-field__message">{{ helper }}</p>
  </div>
</template>

<style scoped>
.pa-field {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.pa-field__label {
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-secondary);
}

.pa-field__control {
  min-height: var(--pa-size-control-lg);
  padding-inline: var(--pa-space-3);
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
}

.pa-field__control::placeholder {
  color: var(--pa-color-text-muted);
}

.pa-field__control:hover:not(:disabled):not(:focus) {
  border-color: var(--pa-color-border-strong);
}

.pa-field__control:focus {
  border-color: var(--pa-color-border-focus);
}

.pa-field__control:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-field__control--error {
  border-color: var(--pa-color-status-restricted);
}

.pa-field__control:disabled {
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-disabled);
  cursor: not-allowed;
}

.pa-field__message {
  margin: 0;
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-muted);
}

.pa-field__message--error {
  color: var(--pa-color-status-restricted);
}
</style>
