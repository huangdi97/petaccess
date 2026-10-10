<script setup lang="ts">
import { type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

interface LensEntry {
  key: string;
  label: string;
  hint: string;
  icon: IconName;
}

defineProps<{ entries: LensEntry[] }>();

const emit = defineEmits<{ select: [key: string] }>();
</script>

<template>
  <div class="home-entries" role="list" data-ui="home-lens">
    <button
      v-for="e in entries"
      :key="e.key"
      type="button"
      class="entry"
      :data-testid="'entry-' + e.key"
      @click="emit('select', e.key)"
    >
      <span class="entry-icon-shell" aria-hidden="true">
        <PaIcon :name="e.icon" size="md" class="entry-icon" />
      </span>
      <span class="entry-copy">
        <span class="entry-label">{{ e.label }}</span>
        <span class="entry-hint">{{ e.hint }}</span>
      </span>
      <span class="entry-arrow" aria-hidden="true">↗</span>
    </button>
  </div>
</template>

<style scoped>
.home-entries {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--pa-space-3);
  margin: var(--pa-space-3) 0 0;
}

.entry {
  position: relative;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  gap: var(--pa-space-3);
  align-items: center;
  min-height: 92px;
  padding: var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background: var(--pa-color-surface-raised);
  color: inherit;
  cursor: pointer;
  text-align: left;
  font: inherit;
  box-shadow: 0 1px 0 color-mix(in srgb, var(--pa-color-text-primary) 4%, transparent);
  transition:
    transform var(--pa-motion-fast) var(--pa-motion-ease),
    border-color var(--pa-motion-fast) var(--pa-motion-ease),
    box-shadow var(--pa-motion-fast) var(--pa-motion-ease);
}

.entry:hover {
  transform: translateY(-1px);
  border-color: var(--pa-color-border-strong);
  box-shadow: var(--pa-elevation-1);
}

.entry:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.entry-icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
}

.entry-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.entry-label {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-primary);
}

.entry-hint {
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-muted);
}

.entry-arrow {
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-lg);
}

@media (min-width: 768px) {
  .home-entries {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .entry {
    grid-template-columns: 40px minmax(0, 1fr);
    grid-template-rows: auto auto;
    align-content: start;
    min-height: 128px;
    padding: var(--pa-space-4);
  }

  .entry-icon-shell {
    grid-column: 1;
    grid-row: 1;
  }

  .entry-copy {
    grid-column: 1 / -1;
    grid-row: 2;
    margin-top: var(--pa-space-2);
  }

  .entry-arrow {
    position: absolute;
    top: var(--pa-space-4);
    right: var(--pa-space-4);
  }
}

@media (max-width: 520px) {
  .home-entries {
    grid-template-columns: 1fr;
  }

  .entry {
    min-height: 78px;
  }
}
</style>
