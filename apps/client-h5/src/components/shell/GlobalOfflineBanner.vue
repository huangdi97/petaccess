<script setup lang="ts">
/**
 * GlobalOfflineBanner — app-shell offline affordance (V020_EMPTY_ERROR_OFFLINE_SPEC
 * §29). One banner for the whole app, hosted by ConsumerAppShell, so pages stop
 * re-implementing offline copy. Retry re-runs the network check and lets the
 * active page reload its data; cached content stays visible and is never
 * presented as fresh.
 */
import { useOnline } from "../../composables/useOnline";
import { Z_INDEX } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

const { online } = useOnline();

function reconnect() {
  // navigator.onLine can be stale (captive portal); bounce the check and let
  // the active page observe the change instead of faking success.
  window.dispatchEvent(new Event("offline"));
  window.dispatchEvent(new Event("online"));
}
</script>

<template>
  <div
    v-if="!online"
    class="global-offline-banner"
    data-testid="global-offline-banner"
    role="status"
    :style="{ zIndex: `var(${Z_INDEX.banner})` }"
  >
    <PaIcon class="global-offline-banner__icon" name="offline" size="sm" />
    <span class="global-offline-banner__text">当前离线，部分内容可能不是最新状态。</span>
    <button class="global-offline-banner__retry" type="button" @click="reconnect">重连</button>
  </div>
</template>

<style scoped>
.global-offline-banner {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  padding: var(--pa-space-2) var(--pa-space-4);
  background: var(--pa-color-status-conditional-bg);
  color: var(--pa-color-status-conditional);
  font-size: var(--pa-font-size-sm);
  border-bottom: var(--pa-border-width) solid var(--pa-color-status-conditional);
}

.global-offline-banner__icon {
  flex: none;
}

.global-offline-banner__text {
  flex: 1;
  line-height: var(--pa-line-height-base);
}

.global-offline-banner__retry {
  flex: none;
  min-height: var(--pa-layout-touch-target);
  padding: 0 var(--pa-space-3);
  border: none;
  border-radius: var(--pa-radius-control);
  background: transparent;
  color: inherit;
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  cursor: pointer;
}

.global-offline-banner__retry:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}
</style>
