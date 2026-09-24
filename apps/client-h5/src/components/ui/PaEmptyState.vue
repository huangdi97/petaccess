<script setup lang="ts">
/**
 * PaEmptyState —unified empty state (V020 catalog #24). Folded-in successor of
 * the legacy StateMessage; buttons render only when their label is provided.
 */
import type { IconName } from "@petaccess/design-tokens";
import PaButton from "./PaButton.vue";
import PaIcon from "./PaIcon.vue";

withDefaults(
  defineProps<{
    icon?: IconName;
    title: string;
    description?: string | null;
    primaryLabel?: string | null;
    secondaryLabel?: string | null;
  }>(),
  { icon: "info", description: null, primaryLabel: null, secondaryLabel: null },
);

const emit = defineEmits<{ primary: []; secondary: [] }>();

defineOptions({ name: "PaEmptyState" });
</script>

<template>
  <div class="pa-empty" data-state="EMPTY">
    <span class="pa-empty__icon">
      <PaIcon :name="icon" size="lg" aria-hidden="true" />
    </span>
    <h2 class="pa-empty__title">{{ title }}</h2>
    <p v-if="description" class="pa-empty__description">{{ description }}</p>
    <div v-if="primaryLabel || secondaryLabel" class="pa-empty__actions">
      <PaButton v-if="primaryLabel" variant="primary" @click="emit('primary')">
        {{ primaryLabel }}
      </PaButton>
      <PaButton v-if="secondaryLabel" variant="secondary" @click="emit('secondary')">
        {{ secondaryLabel }}
      </PaButton>
    </div>
  </div>
</template>

<style scoped>
.pa-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--pa-space-6) var(--pa-space-4);
}

.pa-empty__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-space-7);
  height: var(--pa-space-7);
  border-radius: 50%;
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-secondary);
}

.pa-empty__title {
  margin: var(--pa-space-4) 0 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-empty__description {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-muted);
}

.pa-empty__actions {
  display: flex;
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-5);
}
</style>
