<script setup lang="ts">
/**
 * PaDialog — focused confirmation / action dialog (V020 catalog #17).
 * Teleported into <body>; role=dialog labelled by the title. Escape closes.
 * Overlay clicks intentionally do NOT close here — use PaModal when
 * dismissal-by-overlay-tap is wanted.
 */
import { onBeforeUnmount, onMounted } from "vue";
import { useDialogFocus } from "../../composables/useDialogFocus";

const props = withDefaults(
  defineProps<{
    open: boolean;
    title?: string | null;
    description?: string | null;
    /** Panel max-width: "sm" → content-narrow, "md" → content-max. */
    width?: "sm" | "md";
  }>(),
  { title: null, description: null, width: "sm" },
);

const emit = defineEmits<{ close: [] }>();

defineOptions({ name: "PaDialog" });

const { panel, keepFocusInside } = useDialogFocus(() => props.open);

/** Close on Escape whether focus is inside the dialog or still in the page. */
function onWindowKey(e: KeyboardEvent) {
  if (props.open && e.key === "Escape") emit("close");
}

function keepFocusInside(e: KeyboardEvent) {
  if (e.key !== "Tab" || !panel.value) return;
  const items = [...panel.value.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
    (item) => item.offsetParent !== null,
  );
  if (!items.length) {
    e.preventDefault();
    panel.value.focus();
    return;
  }
  const first = items[0]!;
  const last = items[items.length - 1]!;
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault();
    first.focus();
  }
}

onMounted(() => window.addEventListener("keydown", onWindowKey));
onBeforeUnmount(() => window.removeEventListener("keydown", onWindowKey));
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="pa-dialog" data-state="dialog">
      <div class="pa-dialog__overlay" aria-hidden="true"></div>
      <div
        ref="panel"
        class="pa-dialog__panel"
        :class="`pa-dialog__panel--${width}`"
        role="dialog"
        aria-modal="true"
        tabindex="-1"
        :aria-label="title ?? undefined"
        @keydown.esc.stop="emit('close')"
        @keydown="keepFocusInside"
      >
        <header v-if="title || description" class="pa-dialog__header">
          <h2 v-if="title" class="pa-dialog__title">{{ title }}</h2>
          <p v-if="description" class="pa-dialog__description">{{ description }}</p>
        </header>
        <div class="pa-dialog__body">
          <slot />
        </div>
        <footer v-if="$slots.actions" class="pa-dialog__actions">
          <slot name="actions" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.pa-dialog {
  position: fixed;
  inset: 0;
  z-index: var(--pa-z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--pa-space-4);
}

.pa-dialog__overlay {
  position: absolute;
  inset: 0;
  background: var(--pa-color-bg-overlay);
}

.pa-dialog__panel {
  position: relative;
  width: 100%;
  max-width: var(--pa-layout-content-narrow);
  max-height: calc(100vh - 2 * var(--pa-space-5));
  overflow-y: auto;
  background: var(--pa-color-surface-raised);
  border-radius: var(--pa-radius-lg);
  box-shadow: var(--pa-elevation-3);
  padding: var(--pa-space-5);
}

.pa-dialog__panel--md {
  max-width: var(--pa-layout-content-max);
}

.pa-dialog__header {
  margin-bottom: var(--pa-space-3);
}

.pa-dialog__title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-bold);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-dialog__description {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-muted);
}

.pa-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-5);
}
</style>
