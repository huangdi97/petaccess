<script setup lang="ts">
import { computed } from "vue";
import PaIcon from "./PaIcon.vue";
import PaIconButton from "./PaIconButton.vue";

defineOptions({ name: "PaSearchInput" });

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    clearable?: boolean;
    loading?: boolean;
    autofocus?: boolean;
    ariaLabel?: string;
  }>(),
  { clearable: false, loading: false, autofocus: false },
);

const emit = defineEmits<{ "update:modelValue": [value: string]; submit: [] }>();

const inputAriaLabel = computed(() => props.ariaLabel ?? props.placeholder ?? undefined);

function onInput(event: Event) {
  emit("update:modelValue", (event.target as HTMLInputElement).value);
}
</script>

<template>
  <div class="pa-search">
    <PaIcon name="search" class="pa-search__leading" aria-hidden="true" />
    <input
      type="text"
      class="pa-search__input"
      :value="modelValue"
      :placeholder="placeholder"
      :aria-label="inputAriaLabel"
      :autofocus="autofocus"
      enterkeyhint="search"
      @input="onInput"
      @keyup.enter="emit('submit')"
    />
    <PaIcon v-if="loading" name="refresh" class="pa-search__spinner" aria-hidden="true" />
    <PaIconButton
      v-else-if="clearable && modelValue.length > 0"
      icon="close"
      label="清除搜索"
      tone="plain"
      class="pa-search__clear"
      @click="emit('update:modelValue', '')"
    />
  </div>
</template>

<style scoped>
.pa-search {
  position: relative;
}

.pa-search__leading {
  position: absolute;
  top: 50%;
  left: var(--pa-space-3);
  color: var(--pa-color-text-muted);
  transform: translateY(-50%);
  pointer-events: none;
}

.pa-search__input {
  width: 100%;
  min-height: var(--pa-size-control-lg);
  padding-left: calc(var(--pa-space-4) + var(--pa-size-icon-md) + var(--pa-space-1));
  padding-right: calc(var(--pa-space-7) + var(--pa-space-1));
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
}

.pa-search__input::placeholder {
  color: var(--pa-color-text-muted);
}

.pa-search__input:focus {
  outline: none;
}

.pa-search__input:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-search:focus-within .pa-search__input {
  border-color: var(--pa-color-border-focus);
}

.pa-search__clear {
  position: absolute;
  top: 50%;
  right: var(--pa-space-1);
  transform: translateY(-50%);
}

.pa-search__spinner {
  position: absolute;
  top: 50%;
  right: var(--pa-space-3);
  width: var(--pa-size-icon-md);
  height: var(--pa-size-icon-md);
  color: var(--pa-color-text-muted);
  animation: pa-rotate 0.8s linear infinite;
}

@keyframes pa-rotate {
  to {
    transform: translateY(-50%) rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pa-search__spinner {
    animation-duration: 1.5s;
  }
}
</style>
