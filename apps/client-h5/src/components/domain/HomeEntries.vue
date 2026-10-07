<script setup lang="ts">
/**
 * HomeEntries — the secondary lens entries (freeze §9): a quiet divider list
 * (presence / indoor / dining / rules), never colourful feature cards.
 */
import { type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

interface LensEntry {
  key: string;
  label: string;
  hint: string;
  icon: IconName;
}

defineProps<{
  entries: LensEntry[];
}>();

const emit = defineEmits<{
  select: [key: string];
}>();
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
      <span class="entry-label">{{ e.label }}</span>
      <span class="entry-hint">{{ e.hint }}</span>
      <span class="entry-arrow" aria-hidden="true">→</span>
    </button>
  </div>
</template>

<style scoped>
/* Secondary lens entries — divider-led rows, radius 0, no card skin. */
.home-entries {
  display: grid;
  grid-template-columns: 1fr;
  margin: var(--pa-space-4) 0;
}

.entry {
  display: flex;
  align-items: baseline;
  gap: var(--pa-space-2);
  padding: var(--pa-space-3) 0;
  border: none;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: 0;
  background: none;
  cursor: pointer;
  text-align: left;
  font: inherit;
}

.entry:last-child {
  border-bottom: none;
}

.entry:hover {
  color: var(--pa-color-accent);
}

.entry-icon-shell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
}

.entry-icon {
  color: currentColor;
  flex-shrink: 0;
}

.entry-label {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.entry-hint {
  margin-left: auto;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.entry-arrow {
  margin-left: var(--pa-space-2);
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-lg);
  flex-shrink: 0;
}

@media (min-width: 768px) {
  .home-entries {
    grid-template-columns: repeat(4, 1fr);
    column-gap: var(--pa-space-4);
  }

  .entry {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--pa-space-1);
    border-bottom: none;
    border-right: var(--pa-border-width) solid var(--pa-color-border-subtle);
    padding-right: var(--pa-space-4);
  }

  .entry:last-child {
    border-right: none;
  }

  .entry-hint {
    margin-left: 0;
  }
}
</style>
