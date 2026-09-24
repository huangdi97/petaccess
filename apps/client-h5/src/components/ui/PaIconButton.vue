<script setup lang="ts">
import PaIcon from "./PaIcon.vue";
import type { IconName } from "@petaccess/design-tokens";

defineOptions({ name: "PaIconButton" });

type IconButtonSize = "sm" | "md" | "lg";
type IconButtonTone = "tonal" | "plain";

withDefaults(
  defineProps<{
    icon: IconName;
    /** Accessible name; the icon itself is decorative. */
    label: string;
    size?: IconButtonSize;
    tone?: IconButtonTone;
    disabled?: boolean;
  }>(),
  { size: "lg", tone: "plain", disabled: false },
);

const emit = defineEmits<{ click: [event: MouseEvent] }>();
</script>

<template>
  <button
    type="button"
    class="pa-icon-button"
    :class="[`pa-icon-button--${tone}`, `pa-icon-button--${size}`]"
    :disabled="disabled"
    :aria-disabled="disabled || undefined"
    :aria-label="label"
    @click="emit('click', $event)"
  >
    <PaIcon :name="icon" :size="size" aria-hidden="true" />
  </button>
</template>

<style scoped>
.pa-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--pa-radius-control);
  cursor: pointer;
  transition:
    background-color var(--pa-motion-fast) var(--pa-motion-ease),
    color var(--pa-motion-fast) var(--pa-motion-ease);
}

.pa-icon-button:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.pa-icon-button--sm {
  min-width: var(--pa-size-control-sm);
  min-height: var(--pa-size-control-sm);
}
.pa-icon-button--md {
  min-width: var(--pa-size-control-md);
  min-height: var(--pa-size-control-md);
}
.pa-icon-button--lg {
  min-width: var(--pa-size-control-lg);
  min-height: var(--pa-size-control-lg);
}

.pa-icon-button--plain {
  background: transparent;
  color: var(--pa-color-text-secondary);
}
.pa-icon-button--plain:hover:not(:disabled) {
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-primary);
}

.pa-icon-button--tonal {
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-primary);
}
.pa-icon-button--tonal:hover:not(:disabled) {
  background: var(--pa-color-surface-interactive);
}

.pa-icon-button:disabled {
  cursor: not-allowed;
  color: var(--pa-color-text-disabled);
  opacity: 0.5;
}
</style>
