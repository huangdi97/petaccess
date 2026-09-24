<script setup lang="ts">
/**
 * PlaceSummaryCard — 场所摘要卡片 (map / search surfaces).
 *
 * Keeps the rule dimension (RuleStatus) and the reality dimension
 * (RealityStatus) structurally separate so one can never be mistaken for
 * the other. Whole card navigates to `to` when given.
 */
import { computed } from "vue";
import { RouterLink } from "vue-router";
import type { Component } from "vue";
import { type AccessAnswer, type PlaceSummary, type RealityAnswer } from "@petaccess/client-core";
import { answerStatusKey } from "../../answer";
import PaIcon from "../ui/PaIcon.vue";
import RuleStatus from "./RuleStatus.vue";
import RealityStatus from "./RealityStatus.vue";
import EvidenceMeta from "./EvidenceMeta.vue";

const props = withDefaults(
  defineProps<{
    place: PlaceSummary;
    answer?: AccessAnswer | null;
    reality?: RealityAnswer | null;
    to?: string;
  }>(),
  { answer: null, reality: null, to: undefined },
);

defineOptions({ name: "PlaceSummaryCard" });

const cardTag = computed<Component | "div">(() => (props.to ? RouterLink : "div"));
const address = computed(() => props.place.canonical_address ?? "地址待补充");
const testId = computed(() => `place-summary-${props.place.id}`);
</script>

<template>
  <component :is="cardTag" :to="to ?? undefined" class="place-summary-card" :data-testid="testId">
    <div class="place-summary-card__header">
      <PaIcon name="building" size="md" aria-hidden="true" />
      <span class="place-summary-card__name">{{ place.canonical_name }}</span>
    </div>
    <p class="place-summary-card__address">{{ address }}</p>
    <div class="place-summary-card__statuses">
      <RuleStatus :semantic="answerStatusKey(answer)" />
      <RealityStatus :state="reality?.state ?? null" />
    </div>
    <EvidenceMeta
      v-if="reality"
      :evidence-count="reality.evidence_count"
      :distinct-source-count="reality.distinct_source_count"
      :days-ago="reality.days_since_last_seen"
    />
  </component>
</template>

<style scoped>
.place-summary-card {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  padding: var(--pa-space-4);
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  text-decoration: none;
  color: var(--pa-color-text-primary);
}

.place-summary-card__header {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
}

.place-summary-card__name {
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
}

.place-summary-card__address {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}

.place-summary-card__statuses {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-1);
}
</style>
