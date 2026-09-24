<script setup lang="ts">
/**
 * PaOfflineState — page-level offline state (V020 catalog #26). Title and
 * default description come from the design-tokens page-state dictionary so the
 * wording stays in one place; a reconnect button renders only when a handler
 * is provided.
 */
import { PAGE_STATES } from "@petaccess/design-tokens";
import PaButton from "./PaButton.vue";
import PaIcon from "./PaIcon.vue";

const props = withDefaults(
  defineProps<{
    description?: string | null;
    onReconnect?: (() => void) | null;
  }>(),
  { description: null, onReconnect: null },
);

defineOptions({ name: "PaOfflineState" });

function handleReconnect() {
  props.onReconnect?.();
}
</script>

<template>
  <div class="pa-offline" data-state="OFFLINE">
    <span class="pa-offline__icon">
      <PaIcon name="offline" size="lg" aria-hidden="true" />
    </span>
    <h2 class="pa-offline__title">{{ PAGE_STATES.OFFLINE.title }}</h2>
    <p class="pa-offline__description">{{ description ?? PAGE_STATES.OFFLINE.description }}</p>
    <PaButton
      v-if="onReconnect"
      variant="primary"
      class="pa-offline__action"
      @click="handleReconnect"
    >
      重新连接
    </PaButton>
  </div>
</template>

<style scoped>
.pa-offline {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--pa-space-6) var(--pa-space-4);
}

.pa-offline__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-space-7);
  height: var(--pa-space-7);
  border-radius: 50%;
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-secondary);
}

.pa-offline__title {
  margin: var(--pa-space-4) 0 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-offline__description {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-muted);
}

.pa-offline__action {
  margin-top: var(--pa-space-5);
}
</style>
