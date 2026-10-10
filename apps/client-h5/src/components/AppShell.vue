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
    <DesktopContentContainer mode="wide">
      <main class="secondary-page">
        <slot />
      </main>
    </DesktopContentContainer>
  </div>
</template>

<style scoped>
.secondary-workspace {
  min-height: 100%;
}

.secondary-page {
  width: min(100%, var(--pa-layout-content-960));
  margin: 0 auto;
  padding: var(--pa-space-6) 0 var(--pa-space-64);
}

/* Secondary pages are reading/task workspaces, not narrow settings forms.
 * Keep the same page-identity hierarchy as the core consumer surfaces while
 * retaining bounded line lengths inside each section. */
.secondary-page :deep(h1) {
  margin: 0;
  font-size: var(--pa-font-size-30);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-36);
  color: var(--pa-color-text-primary);
}

@media (max-width: 767px) {
  .secondary-page {
    width: 100%;
    padding: var(--pa-space-4);
  }

  .secondary-page :deep(h1) {
    font-size: var(--pa-font-size-24);
    line-height: var(--pa-line-height-32);
  }
}
</style>
