<script setup lang="ts">
import PaIcon from "./PaIcon.vue";
import type { IconName } from "@petaccess/design-tokens";

defineOptions({ name: "PaButton" });

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

withDefaults(
  defineProps<{
    variant?: ButtonVariant;
    size?: ButtonSize;
    loading?: boolean;
    disabled?: boolean;
    block?: boolean;
    icon?: IconName;
    /** Accessible name for icon-only usage; slot text is used otherwise. */
    ariaLabel?: string;
  }>(),
  { variant: "primary", size: "lg", loading: false, disabled: false, block: false },
);

const emit = defineEmits<{ click: [event: MouseEvent] }>();
</script>

<template>
  <button
    type="button"
    class="pa-button"
    :class="[
      `pa-button--${variant}`,
      `pa-button--${size}`,
      { 'pa-button--block': block, 'pa-button--loading': loading },
    ]"
    :disabled="disabled || loading"
    :aria-disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :aria-label="ariaLabel"
    @click="emit('click', $event)"
  >
    <span v-if="loading" class="pa-button__spinner" aria-hidden="true"></span>
    <PaIcon v-if="icon && !loading" :name="icon" class="pa-button__icon" aria-hidden="true" />
    <span class="pa-button__label"><slot /></span>
  </button>
</template>

<style scoped src="./PaButton.css"></style>
