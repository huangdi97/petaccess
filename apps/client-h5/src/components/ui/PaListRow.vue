<script setup lang="ts">
/**
 * PaListRow — tappable list row (V020 catalog #27). Renders a RouterLink when
 * `to` is set, a native button (emits `activate`) otherwise, or an inert div
 * when disabled. min-height 56px keeps the touch target well above 44px.
 */
import { computed } from "vue";
import { RouterLink } from "vue-router";
import type { Component } from "vue";
import PaIcon from "./PaIcon.vue";

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string | null;
    meta?: string | null;
    /** Route to navigate to on click; disables the `activate` emit. */
    to?: string;
    disabled?: boolean;
  }>(),
  { description: null, meta: null, to: undefined, disabled: false },
);

const emit = defineEmits<{ activate: [] }>();

defineOptions({ name: "PaListRow" });

const rowTag = computed<Component | "button" | "div">(() => {
  if (props.to && !props.disabled) return RouterLink;
  return props.disabled ? "div" : "button";
});

const showChevron = computed(() => Boolean(props.to) && !props.disabled);

function onActivate() {
  if (props.disabled || props.to) return;
  emit("activate");
}
</script>

<template>
  <li
    class="pa-list-row"
    :class="{ 'pa-list-row--disabled': disabled }"
    :aria-disabled="disabled ? 'true' : undefined"
  >
    <component
      :is="rowTag"
      :to="to ?? undefined"
      :type="rowTag === 'button' ? 'button' : undefined"
      class="pa-list-row__main"
      @click="onActivate"
    >
      <span v-if="$slots.leading" class="pa-list-row__leading">
        <slot name="leading" />
      </span>
      <span class="pa-list-row__content">
        <span class="pa-list-row__title">{{ title }}</span>
        <span v-if="description" class="pa-list-row__description">{{ description }}</span>
      </span>
      <span v-if="meta" class="pa-list-row__meta">{{ meta }}</span>
      <span v-if="$slots.trailing" class="pa-list-row__trailing">
        <slot name="trailing" />
      </span>
      <PaIcon
        v-if="showChevron"
        name="chevron-down"
        size="sm"
        class="pa-list-row__chevron"
        aria-hidden="true"
      />
    </component>
  </li>
</template>

<style scoped>
.pa-list-row {
  list-style: none;
  margin: 0;
}

.pa-list-row__main {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  width: 100%;
  min-height: 56px;
  padding: var(--pa-space-3);
  border: none;
  border-radius: var(--pa-radius-control);
  background: transparent;
  font: inherit;
  text-align: left;
  text-decoration: none;
  color: var(--pa-color-text-primary);
  cursor: pointer;
}

.pa-list-row__main:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-list-row__content {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 0;
}

.pa-list-row__title {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-list-row__description {
  margin-top: var(--pa-space-1);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-muted);
}

.pa-list-row__meta {
  flex-shrink: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
  white-space: nowrap;
}

.pa-list-row__chevron {
  flex-shrink: 0;
  transform: rotate(-90deg);
  color: var(--pa-color-text-muted);
}

.pa-list-row--disabled .pa-list-row__main {
  cursor: default;
}

.pa-list-row--disabled .pa-list-row__title {
  color: var(--pa-color-text-disabled);
}

.pa-list-row--disabled .pa-list-row__description,
.pa-list-row--disabled .pa-list-row__meta {
  color: var(--pa-color-text-disabled);
}
</style>
