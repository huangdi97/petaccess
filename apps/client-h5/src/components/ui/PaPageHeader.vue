<script setup lang="ts">
/**
 * PaPageHeader —sticky page header (V020 catalog #30). Back button renders
 * only when `back` is true and emits `back`. The header sticks below the top
 * of the page with the app background, so scrolled content never bleeds
 * through it.
 */
import PaIconButton from "./PaIconButton.vue";

withDefaults(
  defineProps<{
    title: string;
    description?: string | null;
    back?: boolean;
  }>(),
  { description: null, back: false },
);

const emit = defineEmits<{ back: [] }>();

defineOptions({ name: "PaPageHeader" });
</script>

<template>
  <header class="pa-page-header">
    <div class="pa-page-header__row">
      <PaIconButton
        v-if="back"
        icon="arrow-left"
        label="返回"
        class="pa-page-header__back"
        @click="emit('back')"
      />
      <h1 class="pa-page-header__title">{{ title }}</h1>
    </div>
    <p v-if="description" class="pa-page-header__description">{{ description }}</p>
  </header>
</template>

<style scoped>
.pa-page-header {
  position: sticky;
  top: 0;
  z-index: var(--pa-z-sticky);
  background: var(--pa-color-bg-app);
  padding: var(--pa-space-3) var(--pa-space-4);
}

.pa-page-header__row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
}

.pa-page-header__title {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-bold);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-page-header__description {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-muted);
}
</style>
