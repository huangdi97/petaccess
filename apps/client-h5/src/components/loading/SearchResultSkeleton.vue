<script setup lang="ts">
/**
 * SearchResultSkeleton — loading shape for Search results (M2 §27).
 * Rows match PlaceListItem's height so results don't jump on arrival.
 */
defineOptions({ name: "SearchResultSkeleton" });

withDefaults(defineProps<{ rows?: number }>(), { rows: 5 });
</script>

<template>
  <div class="search-result-skeleton" aria-busy="true" role="status">
    <div v-for="i in rows" :key="i" class="search-result-skeleton__row">
      <div class="skeleton skeleton--card search-result-skeleton__title" />
      <div class="skeleton skeleton--line search-result-skeleton__meta" />
      <div class="skeleton skeleton--line search-result-skeleton__meta search-result-skeleton__meta--short" />
    </div>
  </div>
</template>

<style scoped>
.search-result-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
}

.search-result-skeleton__row {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  padding: var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
}

.search-result-skeleton__title {
  height: 20px;
  width: 60%;
}

.search-result-skeleton__meta {
  height: 14px;
  width: 80%;
}

.search-result-skeleton__meta--short {
  width: 40%;
}
</style>