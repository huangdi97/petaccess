<script setup lang="ts">
defineOptions({ name: "PaTabs" });

export interface PaTabItem {
  value: number | string;
  label: string;
}

defineProps<{
  modelValue: number | string;
  tabs: PaTabItem[];
  ariaLabel?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: number | string] }>();
</script>

<template>
  <div class="pa-tabs" role="tablist" :aria-label="ariaLabel">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      type="button"
      class="pa-tabs__tab"
      :class="{ 'pa-tabs__tab--active': tab.value === modelValue }"
      role="tab"
      :aria-selected="tab.value === modelValue"
      @click="emit('update:modelValue', tab.value)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.pa-tabs {
  display: flex;
  gap: var(--pa-space-5);
  overflow-x: auto;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.pa-tabs__tab {
  flex-shrink: 0;
  min-height: var(--pa-size-control-lg);
  margin-bottom: calc(var(--pa-border-width) * -1);
  padding-inline: var(--pa-space-1);
  border: none;
  border-bottom: var(--pa-border-width) solid transparent;
  background: none;
  font-family: var(--pa-font-family);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-secondary);
  cursor: pointer;
  transition:
    color var(--pa-motion-fast) var(--pa-motion-ease),
    border-color var(--pa-motion-fast) var(--pa-motion-ease);
}

.pa-tabs__tab:hover:not(.pa-tabs__tab--active) {
  color: var(--pa-color-text-primary);
}

.pa-tabs__tab--active {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-bold);
  border-bottom-color: var(--pa-color-accent);
  border-bottom-width: var(--pa-border-width-focus);
}

.pa-tabs__tab:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}
</style>
