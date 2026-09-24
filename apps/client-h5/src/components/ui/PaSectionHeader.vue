<script setup lang="ts">
/**
 * PaSectionHeader —section heading with an optional link-style action
 * (V020 catalog #29). The action renders only when actionLabel is provided.
 */
import PaButton from "./PaButton.vue";

withDefaults(
  defineProps<{
    title: string;
    actionLabel?: string | null;
  }>(),
  { actionLabel: null },
);

const emit = defineEmits<{ action: [] }>();

defineOptions({ name: "PaSectionHeader" });
</script>

<template>
  <div class="pa-section-header">
    <h2 class="pa-section-header__title">{{ title }}</h2>
    <PaButton
      v-if="actionLabel"
      variant="ghost"
      size="sm"
      class="pa-section-header__action"
      @click="emit('action')"
    >
      {{ actionLabel }}
    </PaButton>
  </div>
</template>

<style scoped>
.pa-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0;
}

.pa-section-header__title {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: 600;
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-section-header__action {
  flex-shrink: 0;
}
</style>
