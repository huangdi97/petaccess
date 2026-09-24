<script setup lang="ts">
/**
 * DialogHost — one global confirm dialog (V020_APP_SHELL_SPEC §dialog-host).
 * ConsumerAppShell mounts it; pages open it with `useUi().confirm(...)`.
 */
import { useUi } from "../../composables/useUi";
import PaIcon from "../ui/PaIcon.vue";

const { dialog, closeDialog } = useUi();

function confirm() {
  closeDialog(true);
}

function cancel() {
  closeDialog(false);
}
</script>

<template>
  <Teleport to="body">
    <div v-if="dialog" class="dialog-host" data-testid="dialog-host">
      <div class="dialog-host__overlay" @click="cancel" />
      <div class="dialog-host__panel" role="dialog" aria-modal="true" :aria-label="dialog.options.title">
        <div class="dialog-host__title">
          <PaIcon class="dialog-host__title-icon" name="warning" size="md" />
          {{ dialog.options.title }}
        </div>
        <p v-if="dialog.options.message" class="dialog-host__message">
          {{ dialog.options.message }}
        </p>
        <div class="dialog-host__actions">
          <button class="dialog-host__btn dialog-host__btn--ghost" type="button" @click="cancel">
            {{ dialog.options.cancelLabel ?? "取消" }}
          </button>
          <button
            class="dialog-host__btn"
            :class="{ 'dialog-host__btn--danger': dialog.options.danger }"
            type="button"
            @click="confirm"
          >
            {{ dialog.options.confirmLabel ?? "确认" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog-host {
  position: fixed;
  inset: 0;
  z-index: var(--pa-z-modal);
  display: grid;
  place-items: center;
  padding: var(--pa-space-5);
}

.dialog-host__overlay {
  position: absolute;
  inset: 0;
  background: var(--pa-color-bg-overlay);
}

.dialog-host__panel {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--pa-color-surface-raised);
  border-radius: var(--pa-radius-lg);
  padding: var(--pa-space-5);
  box-shadow: var(--pa-elevation-3);
}

.dialog-host__title {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-medium);
}

.dialog-host__title-icon {
  color: var(--pa-color-status-conditional);
}

.dialog-host__message {
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-secondary);
  line-height: var(--pa-line-height-base);
}

.dialog-host__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-5);
}

.dialog-host__btn {
  min-height: var(--pa-layout-touch-target);
  padding: 0 var(--pa-space-5);
  border: none;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-accent);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-base);
  cursor: pointer;
}

.dialog-host__btn--ghost {
  background: var(--pa-color-surface-muted);
  border: var(--pa-border-width) solid var(--pa-color-border);
  color: var(--pa-color-text-primary);
}

.dialog-host__btn--danger {
  background: var(--pa-color-status-restricted);
  color: var(--pa-color-text-inverse);
}

.dialog-host__btn:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}
</style>