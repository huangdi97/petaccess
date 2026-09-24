<script setup lang="ts">
/**
 * PlaceSkeleton — loading shape for a Place detail page (M2 §27).
 * Mirrors the detail layout (header + answer block + zones + sections) to
 * avoid layout shift while the detail fans out across its endpoints.
 */
defineOptions({ name: "PlaceSkeleton" });
</script>

<template>
  <div class="place-skeleton" aria-busy="true" role="status">
    <div class="skeleton skeleton--line place-skeleton__title" />
    <div class="skeleton skeleton--line place-skeleton__address" />
    <div class="skeleton skeleton--card place-skeleton__answer" />
    <div v-for="i in 3" :key="i" class="skeleton skeleton--card place-skeleton__row" />
  </div>
</template>

<style scoped>
.place-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-4);
}

.place-skeleton__title {
  width: 55%;
  height: 24px;
}

.place-skeleton__address {
  width: 70%;
  height: 14px;
}

.place-skeleton__answer {
  height: 120px;
}

.place-skeleton__row {
  height: 64px;
}
</style>
