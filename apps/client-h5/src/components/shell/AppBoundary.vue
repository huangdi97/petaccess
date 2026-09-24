<script setup lang="ts">
/**
 * AppBoundary — the app-level loading + error boundary
 * (V020_APP_SHELL_SPEC §shell-boundary).
 *
 * LOADING: the shell shows a minimal full-app loading state until the router
 * has resolved the first navigation, then streams the page. Pages keep their
 * own skeletons for data loading; this covers only app boot.
 *
 * ERROR: any uncaught render error (child component throws) is captured here
 * and surfaced as a unified error state with a reload action — never as a raw
 * stack trace or the framework's crash screen.
 */
import { computed, onErrorCaptured, ref } from "vue";
import { useRouter } from "vue-router";
import { presentError } from "../../errors";
import PaIcon from "../ui/PaIcon.vue";

const router = useRouter();
const appReady = ref(false);
const boundaryError = ref<unknown>(null);

const bootFailed = ref(false);

// Router readiness is immediate for hash history, but keep the hook so the
// boundary is honest when navigation ever starts slow (lazy route chunks).
router.isReady().then(() => (appReady.value = true)).catch(() => (bootFailed.value = true));

onErrorCaptured((err) => {
  boundaryError.value = err;
  // Swallow so Vue doesn't rethrow to its own handler.
  return false;
});

const presentation = computed(() => presentError(boundaryError.value));

function reload() {
  boundaryError.value = null;
  window.location.reload();
}

function retryBoot() {
  bootFailed.value = false;
  void router.push(router.currentRoute.value.fullPath);
}
</script>

<template>
  <div v-if="boundaryError" class="app-boundary" data-testid="app-error-boundary">
    <div class="app-boundary__panel">
      <PaIcon class="app-boundary__icon" name="warning" size="xl" />
      <h1 class="app-boundary__title">{{ presentation.title }}</h1>
      <p class="app-boundary__desc">{{ presentation.description }}</p>
      <button v-if="presentation.retryLabel" class="app-boundary__retry" type="button" @click="reload">
        {{ presentation.retryLabel }}
      </button>
    </div>
  </div>
  <div v-else-if="bootFailed" class="app-boundary" data-testid="app-boot-error">
    <div class="app-boundary__panel">
      <PaIcon class="app-boundary__icon" name="warning" size="xl" />
      <h1 class="app-boundary__title">应用加载失败</h1>
      <button class="app-boundary__retry" type="button" @click="retryBoot">重试</button>
    </div>
  </div>
  <div v-else-if="!appReady" class="app-boundary" data-testid="app-booting">
    <div class="app-boundary__panel app-boundary__panel--boot">
      <PaIcon class="app-boundary__icon" name="refresh" size="xl" />
      <span class="visually-hidden">正在加载</span>
    </div>
  </div>
  <slot v-else />
</template>

<style scoped>
.app-boundary {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--pa-space-6);
}

.app-boundary__panel {
  max-width: var(--pa-layout-content-narrow);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--pa-space-3);
}

.app-boundary__panel--boot {
  gap: 0;
}

.app-boundary__icon {
  color: var(--pa-color-text-muted);
}

.app-boundary__title {
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-bold);
  margin: 0;
}

.app-boundary__desc {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
  line-height: var(--pa-line-height-base);
  margin: 0;
}

.app-boundary__retry {
  min-height: var(--pa-layout-touch-target);
  padding: 0 var(--pa-space-5);
  border: none;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-accent);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-base);
  cursor: pointer;
}

.app-boundary__retry:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  margin: -1px;
  padding: 0;
  border: 0;
  white-space: nowrap;
}
</style>