<script setup lang="ts">
/**
 * DivergenceSummary — 规则与现场不一致的提示块.
 *
 * Warm, non-alarm wording from `../../reality` (AC8); the block renders
 * nothing when there is no divergence fact.
 */
import { computed } from "vue";
import type { RuleRealityDivergence } from "@petaccess/client-core";
import { divergenceLabel } from "../../reality";
import PaIcon from "../ui/PaIcon.vue";

const props = withDefaults(
  defineProps<{
    divergence?: RuleRealityDivergence | null;
  }>(),
  { divergence: null },
);

defineOptions({ name: "DivergenceSummary" });

const label = computed(() => divergenceLabel(props.divergence));
</script>

<template>
  <div v-if="divergence" class="divergence-summary" :data-divergence-state="divergence.state">
    <PaIcon class="divergence-summary__icon" name="warning" size="sm" aria-hidden="true" />
    <span class="divergence-summary__text">{{ label }}</span>
  </div>
</template>

<style scoped>
.divergence-summary {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-2);
  padding: var(--pa-space-3);
  border-left: var(--pa-border-width) solid var(--pa-color-status-conditional);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-status-conditional-bg);
}

.divergence-summary__icon {
  flex: none;
  color: var(--pa-color-status-conditional);
}

.divergence-summary__text {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
}
</style>
