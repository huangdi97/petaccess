<script setup lang="ts">
/**
 * PaBanner — inline tone banner (V020 catalog #21). A coloured left border +
 * background carry the tone; the icon repeats the meaning so the tone is never
 * colour-only. Optional action button and a close control.
 */
import { computed } from "vue";
import type { IconName } from "@petaccess/design-tokens";
import PaButton from "./PaButton.vue";
import PaIcon from "./PaIcon.vue";
import PaIconButton from "./PaIconButton.vue";

type BannerTone = "info" | "warn" | "error";

const TONE_ICON: Record<BannerTone, IconName> = {
  info: "info",
  warn: "warning",
  error: "x-circle",
};

const props = withDefaults(
  defineProps<{
    tone: BannerTone;
    message: string;
    actionLabel?: string | null;
  }>(),
  { actionLabel: null },
);

const emit = defineEmits<{ action: []; close: [] }>();

defineOptions({ name: "PaBanner" });

const icon = computed<IconName>(() => TONE_ICON[props.tone]);
</script>

<template>
  <div class="pa-banner" :class="`pa-banner--${tone}`">
    <PaIcon :name="icon" size="md" class="pa-banner__icon" aria-hidden="true" />
    <p class="pa-banner__message">{{ message }}</p>
    <PaButton
      v-if="actionLabel"
      variant="ghost"
      size="sm"
      class="pa-banner__action"
      @click="emit('action')"
    >
      {{ actionLabel }}
    </PaButton>
    <PaIconButton icon="close" label="关闭提示" size="sm" @click="emit('close')" />
  </div>
</template>

<style scoped>
.pa-banner {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  border-radius: var(--pa-radius-md);
  padding: var(--pa-space-3);
  border-left: var(--pa-border-width-strong) solid var(--pa-color-accent);
  background: var(--pa-color-surface-muted);
}

.pa-banner__message {
  flex: 1 1 auto;
  margin: 0;
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
}

.pa-banner--warn {
  background: var(--pa-color-status-conditional-bg);
  border-left-color: var(--pa-color-status-conditional);
}

.pa-banner--warn .pa-banner__icon {
  color: var(--pa-color-status-conditional);
}

.pa-banner--error {
  background: var(--pa-color-status-restricted-bg);
  border-left-color: var(--pa-color-status-restricted);
}

.pa-banner--error .pa-banner__icon {
  color: var(--pa-color-status-restricted);
}

.pa-banner--info .pa-banner__icon {
  color: var(--pa-color-accent);
}

.pa-banner__action {
  flex-shrink: 0;
}
</style>
