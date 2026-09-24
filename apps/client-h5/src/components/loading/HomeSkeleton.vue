<script setup lang="ts">
/**
 * HomeSkeleton — loading shape for the Home page (M2 §27).
 * Structure mirrors the loaded page (header + search + entries + list rows) so
 * layout does not shift when data arrives.
 */
defineOptions({ name: "HomeSkeleton" });
</script>

<template>
  <div class="home-skeleton" aria-busy="true" role="status">
    <div class="home-skeleton__search">
      <div class="skeleton skeleton--line home-skeleton__search-field" />
    </div>
    <div class="home-skeleton__entries">
      <div v-for="i in 4" :key="i" class="skeleton skeleton--card home-skeleton__entry" />
    </div>
    <div v-for="i in 3" :key="`row-${i}`" class="skeleton skeleton--card home-skeleton__row" />
  </div>
</template>

<style scoped>
.home-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-4);
}

.home-skeleton__search {
  margin-bottom: var(--pa-space-2);
}

.home-skeleton__search-field {
  width: 100%;
  height: var(--pa-size-control-lg);
  border-radius: var(--pa-radius-control);
}

.home-skeleton__entries {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--pa-space-3);
}

.home-skeleton__entry {
  height: 72px;
}

.home-skeleton__row {
  height: 88px;
}

@media (min-width: 768px) {
  .home-skeleton__entries {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>