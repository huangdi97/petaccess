<script setup lang="ts">
/**
 * PaModal — scrollable body dialog with an explicit footer (V020 catalog #18).
 * Teleported into <body>; closes via Escape, overlay tap (@click.self, so taps
 * inside the panel never close it) or the host driving `open` down.
 */
import { onBeforeUnmount, onMounted } from "vue";

const props = withDefaults(defineProps<{ open: boolean; title?: string | null }>(), {
  title: null,
});

const emit = defineEmits<{ close: [] }>();

defineOptions({ name: "PaModal" });

/** Close on Escape whether focus is inside the modal or still in the page. */
function onWindowKey(e: KeyboardEvent) {
  if (props.open && e.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", onWindowKey));
onBeforeUnmount(() => window.removeEventListener("keydown", onWindowKey));
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="pa-modal">
      <div class="pa-modal__overlay" @click.self="emit('close')"></div>
      <section
        class="pa-modal__panel"
        role="dialog"
        aria-modal="true"
        :aria-label="title ?? undefined"
        @keydown.esc.stop="emit('close')"
      >
        <header v-if="title" class="pa-modal__header">
          <h2 class="pa-modal__title">{{ title }}</h2>
        </header>
        <div class="pa-modal__body">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="pa-modal__footer">
          <slot name="footer" />
        </footer>
      </section>
    </div>
  </Teleport>
</template>

<style scoped>
.pa-modal {
  position: fixed;
  inset: 0;
  z-index: var(--pa-z-modal);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--pa-space-4);
}

.pa-modal__overlay {
  position: absolute;
  inset: 0;
  background: var(--pa-color-bg-overlay);
}

.pa-modal__panel {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: var(--pa-layout-content-narrow);
  max-height: 85vh;
  overflow: hidden;
  background: var(--pa-color-surface-raised);
  border-radius: var(--pa-radius-lg);
  box-shadow: var(--pa-elevation-3);
}

.pa-modal__header {
  padding: var(--pa-space-5) var(--pa-space-5) 0;
}

.pa-modal__title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-bold);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-modal__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: var(--pa-space-4) var(--pa-space-5);
}

.pa-modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--pa-space-2);
  padding: var(--pa-space-4) var(--pa-space-5) var(--pa-space-5);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
</style>
