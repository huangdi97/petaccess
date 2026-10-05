<script setup lang="ts">
import { computed } from "vue";

import { answerVerdictLabel } from "../../answer";
import type { HomeCard } from "../../composables/useHomeLauncher";
import { lensOrderScore, type ConsumerLens } from "../../consumer/rowView";
import { divergenceLabel, realityStateLabel } from "../../reality";

const props = withDefaults(
  defineProps<{
    verified: HomeCard[];
    pending: HomeCard[];
    interest?: ConsumerLens;
    section?: "recommend" | "divergence";
  }>(),
  { interest: "", section: "recommend" },
);

const emit = defineEmits<{
  open: [id: string];
}>();

const cards = computed(() => [...props.verified, ...props.pending]);
const recommendationTitle = computed(() =>
  props.interest ? "按你的关注推荐" : "近期值得先看",
);

function hasUsefulFact(card: HomeCard): boolean {
  return Boolean(card.facts.answer || (card.facts.reality?.evidence_count ?? 0) > 0);
}

/**
 * Recommendation is an ordering projection, never a venue score. A saved
 * attention lens gets first priority; neutral Home falls back to recency and
 * evidence availability. No positive/negative morality is inferred.
 */
function compareRecommendation(a: HomeCard, b: HomeCard): number {
  if (props.interest) {
    const byInterest =
      lensOrderScore(props.interest, b.facts.answer, b.facts.reality) -
      lensOrderScore(props.interest, a.facts.answer, a.facts.reality);
    if (byInterest) return byInterest;
  }

  const aDays = a.facts.reality?.days_since_last_seen ?? Number.POSITIVE_INFINITY;
  const bDays = b.facts.reality?.days_since_last_seen ?? Number.POSITIVE_INFINITY;
  if (aDays !== bDays) return aDays - bDays;

  const aEvidence = a.facts.reality?.evidence_count ?? 0;
  const bEvidence = b.facts.reality?.evidence_count ?? 0;
  if (aEvidence !== bEvidence) return bEvidence - aEvidence;

  return a.place.canonical_name.localeCompare(b.place.canonical_name, "zh-CN");
}

const recommended = computed(() =>
  [...cards.value].filter(hasUsefulFact).sort(compareRecommendation).slice(0, 2),
);

const divergences = computed(() =>
  cards.value
    .filter((card) => {
      const state = card.facts.snapshot?.divergence?.state;
      return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
    })
    .slice(0, 3),
);

function headline(card: HomeCard): string {
  if (props.interest === "rules" && card.facts.answer) {
    return answerVerdictLabel(card.facts.answer);
  }
  const reality = card.facts.reality;
  if (reality && reality.evidence_count > 0) return realityStateLabel(reality);
  if (card.facts.answer) return answerVerdictLabel(card.facts.answer);
  return "信息不足";
}

function meta(card: HomeCard): string {
  const reality = card.facts.reality;
  const parts: string[] = [];
  if (reality?.days_since_last_seen != null) {
    parts.push(`${reality.days_since_last_seen} 天前最近记录`);
  }
  if ((reality?.evidence_count ?? 0) > 0) {
    parts.push(`${reality?.evidence_count} 条现场证据`);
  }
  const ruleEvidence = card.facts.snapshot?.evidence_summary.rule_evidence.length ?? 0;
  if (!parts.length && ruleEvidence > 0) parts.push(`${ruleEvidence} 条规则依据`);
  return parts.join(" · ");
}

function divergenceText(card: HomeCard): string {
  return divergenceLabel(card.facts.snapshot?.divergence ?? null);
}
</script>

<template>
  <section
    v-if="section === 'recommend' && recommended.length"
    class="home-recommend"
    data-ui="home-recommend"
  >
    <h2 class="home-digest-title">{{ recommendationTitle }}</h2>
    <p v-if="interest" class="home-digest-note muted">只调整信息顺序，不对场所评分。</p>
    <button
      v-for="card in recommended"
      :key="'recommend-' + card.place.id"
      type="button"
      class="home-recommend__row"
      :data-testid="'recommend-' + card.place.id"
      @click="emit('open', card.place.id)"
    >
      <strong class="home-recommend__name">{{ card.place.canonical_name }}</strong>
      <span class="home-recommend__headline">{{ headline(card) }}</span>
      <span v-if="meta(card)" class="muted home-recommend__meta">{{ meta(card) }}</span>
    </button>
  </section>

  <section
    v-if="section === 'divergence' && divergences.length"
    class="home-divergence"
    data-ui="home-divergence"
  >
    <h2 class="home-digest-title">规则与现场不一致</h2>
    <button
      v-for="card in divergences"
      :key="'divergence-' + card.place.id"
      type="button"
      class="home-divergence__row"
      :data-testid="'divergence-' + card.place.id"
      @click="emit('open', card.place.id)"
    >
      <strong>{{ card.place.canonical_name }}</strong>
      <span>{{ divergenceText(card) }}</span>
    </button>
  </section>
</template>

<style scoped>
.home-digest-title {
  margin: var(--pa-space-5) 0 var(--pa-space-2);
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.home-digest-note {
  margin: calc(-1 * var(--pa-space-1)) 0 var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
}

.home-recommend__row,
.home-divergence__row {
  width: 100%;
  cursor: pointer;
  border: none;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: 0;
  background: transparent;
  text-align: left;
  color: var(--pa-color-text-primary);
}

.home-recommend__row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: var(--pa-space-4) 0;
}

.home-recommend__name {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
}

.home-recommend__headline {
  margin-top: var(--pa-space-1);
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
}

.home-recommend__meta {
  margin-top: var(--pa-space-1);
  font-size: var(--pa-font-size-md);
}

.home-divergence__row {
  display: grid;
  grid-template-columns: minmax(0, 0.7fr) minmax(0, 1.3fr);
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
}

.home-divergence__row span {
  color: var(--pa-color-status-conflict);
}

.home-recommend__row:hover,
.home-divergence__row:hover {
  background: var(--pa-color-surface-interactive);
}

@media (max-width: 767px) {
  .home-divergence__row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }
}
</style>
