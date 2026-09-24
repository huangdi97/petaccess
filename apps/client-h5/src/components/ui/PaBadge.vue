<script setup lang="ts">
/**
 * PaBadge — small read-only label (V020 catalog #13). `outline` swaps the tint
 * fill for a transparent fill with a currentColor border.
 */
import { computed } from "vue";

type BadgeTone = "neutral" | "info" | "success" | "warn";

const TONE_STYLE: Record<BadgeTone, { color: string; background: string }> = {
  neutral: {
    color: "var(--pa-color-text-secondary)",
    background: "var(--pa-color-surface-muted)",
  },
  info: {
    color: "var(--pa-color-accent)",
    background: "var(--pa-color-accent-weak)",
  },
  success: {
    color: "var(--pa-color-status-allowed)",
    background: "var(--pa-color-status-allowed-bg)",
  },
  warn: {
    color: "var(--pa-color-status-conditional)",
    background: "var(--pa-color-status-conditional-bg)",
  },
};

const props = withDefaults(
  defineProps<{
    text: string | number;
    tone?: BadgeTone;
    outline?: boolean;
  }>(),
  { tone: "neutral", outline: false },
);

defineOptions({ name: "PaBadge" });

const style = computed(() =>
  props.outline ? { color: TONE_STYLE[props.tone].color } : TONE_STYLE[props.tone],
);
</script>

<template>
  <span class="pa-badge" :class="{ 'pa-badge--outline': outline }" :style="style">
    {{ text }}
  </span>
</template>

<style scoped>
.pa-badge {
  display: inline-flex;
  align-items: center;
  border: none;
  border-radius: var(--pa-radius-sm);
  padding: var(--pa-space-1) var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  white-space: nowrap;
}

.pa-badge--outline {
  background: transparent;
  border: var(--pa-border-width) solid currentColor;
}
</style>
