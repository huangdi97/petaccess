<script setup lang="ts">
/**
 * ConsumerAppShell — the one true app root (V020_APP_SHELL_SPEC §14).
 *
 * Responsibilities, and nothing more:
 *   • navigation (mobile bottom tabs < 768px, desktop rail ≥ 768px)
 *   • route frame (RouterView inside a content container)
 *   • safe area (bottom tabs / rail consume safe-area insets)
 *   • network state (global offline banner)
 *   • global toast + dialog hosts
 *   • theme (data-theme attribute hook)
 *   • global loading + error boundary
 *   • version info (desktop rail footer)
 * Deliberately contains NO Rule/Reality calculations and no API queries —
 * pages own their data; the shell owns only chrome.
 */
import { onMounted, ref } from "vue";
import { useBreakpoint } from "../../composables/useBreakpoint";
import { bootStage } from "../../config/bootTrace";
import AppBoundary from "./AppBoundary.vue";
import DesktopRail from "../nav/DesktopRail.vue";
import MobileTabbar from "../nav/MobileTabbar.vue";
import GlobalOfflineBanner from "./GlobalOfflineBanner.vue";
import ToastHost from "./ToastHost.vue";
import DialogHost from "./DialogHost.vue";

defineOptions({ name: "ConsumerAppShell" });

const { desktop } = useBreakpoint();

/** theme hook: light is the shipped theme (tokens.css). */
const theme = ref<"light" | "dark">("light");

onMounted(() => {
  document.documentElement.dataset.theme = theme.value;
  bootStage("APP_SHELL_MOUNTED");
});
</script>

<template>
  <div class="consumer-app-shell" data-testid="consumer-app-shell">
    <GlobalOfflineBanner />

    <DesktopRail v-if="desktop" />

    <main class="consumer-app-shell__main">
      <AppBoundary>
        <RouterView v-slot="{ Component }">
          <component :is="Component" />
        </RouterView>
      </AppBoundary>
    </main>

    <MobileTabbar v-if="!desktop" />

    <ToastHost />
    <DialogHost />
  </div>
</template>

<style scoped>
.consumer-app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.consumer-app-shell__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: 0;
  padding-bottom: calc(var(--pa-safe-bottom) + var(--pa-layout-tabbar-height));
}

/* Desktop: content area sits to the right of the rail and no longer reserves
 * tabbar space at the bottom. */
@media (min-width: 768px) {
  .consumer-app-shell__main {
    margin-left: var(--pa-layout-rail-width);
    padding-bottom: 0;
  }
}
</style>
