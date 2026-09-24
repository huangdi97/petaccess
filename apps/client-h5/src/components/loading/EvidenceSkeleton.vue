<script setup lang="ts">
/**
 * EvidenceSkeleton — loading shape for the evidence section (M2 §27).
 * Mirrors evidence rows (label + value + verification chip) so the section
 * keeps its height while evidence loads.
 */
defineOptions({ name: "EvidenceSkeleton" });

withDefaults(defineProps<{ rows?: number }>(), { rows: 4 });
</script>

<template>
  <div class="evidence-skeleton" aria-busy="true" role="status">
    <div v-for="i in rows" :key="i" class="evidence-skeleton__row">
      <div class="skeleton skeleton--line evidence-skeleton__label" />
      <div class="skeleton skeleton--line evidence-skeleton__value" />
      <div class="skeleton skeleton--line evidence-skeleton__chip" />
    </div>
  </div>
</template>

<style scoped>
.evidence-skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
}

.evidence-skeleton__row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  padding: var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
}

.evidence-skeleton__label {
  width: 20%;
  height: 12px;
  flex: none;
}

.evidence-skeleton__value {
  width: 50%;
  height: 14px;
}

.evidence-skeleton__chip {
  width: 64px;
  height: 16px;
  border-radius: var(--pa-radius-pill);
  margin-left: auto;
}
</style>