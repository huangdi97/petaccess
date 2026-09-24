<script setup lang="ts">
/**
 * ToastHost —renders the global toast stack (V020_APP_SHELL_SPEC §toast-host).
 * ConsumerAppShell mounts exactly one ToastHost; pages use `useUi().toast()`
 * and never render their own toast/alert stack.
 */
import { useUi } from "../../composables/useUi";
import PaIcon from "../ui/PaIcon.vue";
import { type IconName } from "@petaccess/design-tokens";

const { toasts, dismissToast } = useUi();

const KIND_ICONS: Record<string, IconName> = {
  success: "check-circle",
  info: "info",
  warning: "warning",
  error: "x-circle",
};
</script>

<template>
  <div class="toast-host" data-testid="toast-host" aria-live="polite" aria-atomic="false">
    <transition-group name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="toast-host__item"
        :class="`toast-host__item--${t.kind}`"
        :role="t.kind === 'error' ? 'alert' : 'status'"
      >
        <PaIcon :name="KIND_ICONS[t.kind] ?? 'info'" class="toast-host__icon" size="sm" />
        <span class="toast-host__message">{{ t.message }}</span>
        <button
          class="toast-host__close"
          type="button"
          aria-label="关闭提示"
          @click="dismissToast(t.id)"
        >
          <PaIcon name="close" size="sm" />
        </button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  bottom: calc(var(--pa-safe-bottom) + var(--pa-space-5));
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--pa-z-toast);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--pa-space-2);
  width: min(calc(100vw - var(--pa-space-6)), var(--pa-layout-content-narrow));
  pointer-events: none;
}

.toast-host__item {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  max-width: 100%;
  padding: var(--pa-space-3) var(--pa-space-4);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-raised);
  border: var(--pa-border-width) solid var(--pa-color-border);
  box-shadow: var(--pa-elevation-3);
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
  pointer-events: auto;
}

.toast-host__icon {
  flex: none;
}

.toast-host__item--success .toast-host__icon {
  color: var(--pa-color-status-allowed);
}

.toast-host__item--info .toast-host__icon {
  color: var(--pa-color-accent);
}

.toast-host__item--warning .toast-host__icon {
  color: var(--pa-color-status-conditional);
}

.toast-host__item--error .toast-host__icon {
  color: var(--pa-color-status-restricted);
}

.toast-host__message {
  flex: 1;
  line-height: var(--pa-line-height-base);
}

.toast-host__close {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-layout-touch-target);
  height: var(--pa-layout-touch-target);
  border: none;
  background: transparent;
  color: var(--pa-color-text-muted);
  cursor: pointer;
  border-radius: var(--pa-radius-control);
}

.toast-host__close:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}

/* motion */
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity var(--pa-motion-base) var(--pa-motion-ease),
    transform var(--pa-motion-base) var(--pa-motion-ease);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(var(--pa-space-2));
}
</style>
