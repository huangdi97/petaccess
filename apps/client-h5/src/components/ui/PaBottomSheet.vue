<script setup lang="ts">
/**
 * PaBottomSheet — mobile bottom-anchored sheet (V020 catalog #19).
 * Teleported into <body> and always mounted: the overlay is v-show driven and
 * the panel slides with a token-driven transform (translateY 100% ↔ 0). Escape
 * closes; the overlay is tap-to-close like the legacy BottomSheet.
 */
import { onBeforeUnmount, onMounted } from "vue";

const props = withDefaults(
  defineProps<{ open: boolean; title?: string | null; ui?: string | null }>(),
  {
    title: null,
    ui: null,
  },
);

const emit = defineEmits<{ close: [] }>();

defineOptions({ name: "PaBottomSheet" });

/** Close on Escape whether focus is inside the sheet or still in the page. */
function onWindowKey(e: KeyboardEvent) {
  if (props.open && e.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", onWindowKey));
onBeforeUnmount(() => window.removeEventListener("keydown", onWindowKey));
</script>

<template>
  <Teleport to="body">
    <div class="pa-sheet" data-state="sheet" :data-ui="props.ui ?? undefined">
      <!-- v-show so the panel keeps its transform transition while closed. -->
      <div v-show="open" class="pa-sheet__overlay" @click.self="emit('close')"></div>
      <section
        class="pa-sheet__panel"
        :class="{ 'pa-sheet__panel--open': open }"
        role="dialog"
        aria-modal="true"
        :aria-label="title ?? undefined"
        :aria-hidden="open ? undefined : 'true'"
        @keydown.esc.stop="emit('close')"
      >
        <div class="pa-sheet__handle" aria-hidden="true"></div>
        <header v-if="title" class="pa-sheet__header">
          <h2 class="pa-sheet__title">{{ title }}</h2>
        </header>
        <div class="pa-sheet__body">
          <slot />
        </div>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.pa-sheet {
  position: fixed;
  inset: 0;
  z-index: var(--pa-z-sheet);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  /* The wrapper itself must never swallow page taps while the sheet is closed. */
  pointer-events: none;
}

.pa-sheet__overlay {
  position: absolute;
  inset: 0;
  background: var(--pa-color-bg-overlay);
  pointer-events: auto;
}

.pa-sheet__panel {
  position: relative;
  width: 100%;
  max-width: 720px;
  background: var(--pa-color-surface-raised);
  border-radius: var(--pa-radius-lg) var(--pa-radius-lg) 0 0;
  box-shadow: var(--pa-elevation-3);
  padding: var(--pa-space-3) var(--pa-space-4);
  padding-bottom: calc(var(--pa-space-4) + var(--pa-safe-bottom));
  transform: translateY(100%);
  transition: transform var(--pa-motion-base) var(--pa-motion-ease);
  pointer-events: auto;
}

.pa-sheet__panel--open {
  transform: translateY(0);
}

.pa-sheet__handle {
  width: var(--pa-space-40);
  height: var(--pa-space-1);
  margin: 0 auto var(--pa-space-3);
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-border-strong);
}

.pa-sheet__title {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-bold);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}
</style>
