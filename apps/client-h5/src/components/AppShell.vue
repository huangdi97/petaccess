<script setup lang="ts">
/**
 * Secondary consumer page shell.
 *
 * The global ConsumerAppShell already owns desktop/mobile navigation. Secondary
 * pages only need the same Current Query primitive and a bounded reading/task
 * column; they must not re-introduce the legacy mode bar or a pet-summary card.
 */
import QueryContextBar from "./domain/QueryContextBar.vue";
import DesktopContentContainer from "./layout/DesktopContentContainer.vue";
</script>

<template>
  <div class="secondary-workspace">
    <QueryContextBar />
    <DesktopContentContainer mode="single-column">
      <div class="secondary-page">
        <slot />
      </div>
    </DesktopContentContainer>
  </div>
</template>

<style scoped>
.secondary-workspace {
  min-height: 100%;
}

.secondary-page {
  padding: var(--pa-space-6) 0 var(--pa-space-8);
}

@media (max-width: 767px) {
  .secondary-page {
    padding: var(--pa-space-4);
  }
}
</style>
