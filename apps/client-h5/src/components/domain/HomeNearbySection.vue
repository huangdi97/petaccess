<script setup lang="ts">
/**
 * HomeNearbySection — the verified/pending nearby list (freeze §9).
 *
 * Pure presentation over the launcher's derived rows: divider-led rows via
 * PlaceResultRow plus scope / conditions / why — never cards. Loading,
 * transport error, empty and freshness (offline/stale) states are explicit.
 */
import { computed } from "vue";
import { type PlaceSummary } from "@petaccess/client-core";
import PlaceResultRow from "./PlaceResultRow.vue";
import SkeletonList from "../SkeletonList.vue";
import StateMessage from "../StateMessage.vue";
import StatusBadge from "../StatusBadge.vue";
import { placeTypeLabel } from "@petaccess/client-core";
import { freshnessLineFor } from "../../consumer/rowView";
import { answerVerdictLabel } from "../../answer";
import { divergenceLabel, realityStateLabel } from "../../reality";
import type { HomeCard } from "../../composables/useHomeLauncher";

const props = defineProps<{
  loading: boolean;
  error: string;
  places: PlaceSummary[];
  verified: HomeCard[];
  pending: HomeCard[];
  listStale: boolean;
  nearbyFetchedAtMs: number | null;
  online: boolean;
  speciesLabel: string;
  conditionsLabel: Record<string, string>;
}>();

const emit = defineEmits<{
  open: [id: string];
  why: [id: string];
  retry: [];
}>();

const freshness = computed(() =>
  freshnessLineFor(props.listStale, props.nearbyFetchedAtMs, !props.online),
);

const allCards = computed(() => [...props.verified, ...props.pending]);

function recommendationScore(card: HomeCard): number {
  const reality = card.facts.reality;
  const evidence = reality?.evidence_count ?? 0;
  const days = reality?.days_since_last_seen;
  const recent = days == null ? 0 : Math.max(0, 90 - Math.min(days, 90));
  const answered = card.facts.answer ? 20 : 0;
  const divergence = card.facts.snapshot?.divergence?.state;
  const mismatch =
    divergence && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(divergence) ? 40 : 0;
  return evidence * 10 + recent + answered + mismatch;
}

const recommended = computed(() =>
  [...allCards.value]
    .filter((card) => recommendationScore(card) > 0)
    .sort((a, b) => recommendationScore(b) - recommendationScore(a))
    .slice(0, 2),
);

const divergences = computed(() =>
  allCards.value
    .filter((card) => {
      const state = card.facts.snapshot?.divergence?.state;
      return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
    })
    .slice(0, 3),
);

function recommendationHeadline(card: HomeCard): string {
  const reality = card.facts.reality;
  if (reality && reality.evidence_count > 0) return realityStateLabel(reality);
  if (card.facts.answer) return answerVerdictLabel(card.facts.answer);
  return "信息不足";
}

function recommendationMeta(card: HomeCard): string {
  const reality = card.facts.reality;
  const parts: string[] = [];
  if (reality?.days_since_last_seen != null) parts.push(`${reality.days_since_last_seen} 天前最近记录`);
  if ((reality?.evidence_count ?? 0) > 0) parts.push(`${reality?.evidence_count} 条现场证据`);
  const ruleEvidence = card.facts.snapshot?.evidence_summary.rule_evidence.length ?? 0;
  if (!parts.length && ruleEvidence > 0) parts.push(`${ruleEvidence} 条规则依据`);
  return parts.join(" · ");
}

function divergenceText(card: HomeCard): string {
  return divergenceLabel(card.facts.snapshot?.divergence ?? null);
}
</script>

<template>
  <div data-ui="home-nearby">
    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" title="未能取得附近场所" :description="error">
      <template #action>
        <button class="primary" @click="emit('retry')">重试</button>
      </template>
    </StateMessage>

    <template v-else>
      <StateMessage
        v-if="!places.length"
        kind="EMPTY"
        data-testid="home-empty"
        title="当前还没有已发布的场所数据"
        description="你仍然可以了解 PetAccess 如何区分规则与现场，或者提交第一条线索。"
      >
        <template #action>
          <RouterLink class="primary" to="/map" data-testid="home-empty-map">探索地图</RouterLink>
          <RouterLink class="secondary" to="/contribute" data-testid="home-empty-contribute"
            >贡献线索</RouterLink
          >
        </template>
      </StateMessage>

      <template v-else>
        <p
          v-if="freshness"
          class="muted"
          data-testid="home-freshness"
          style="margin: 0 0 var(--pa-space-2)"
        >
          {{ freshness }}
        </p>

        <section v-if="recommended.length" class="home-recommend" data-ui="home-recommend">
          <h2 class="home-section-title home-section-title--stacked">按你的关注推荐</h2>
          <div
            v-for="c in recommended"
            :key="'recommend-' + c.place.id"
            class="home-recommend__row"
            :data-testid="'recommend-' + c.place.id"
            @click="emit('open', c.place.id)"
          >
            <strong class="home-recommend__name">{{ c.place.canonical_name }}</strong>
            <p class="home-recommend__headline">{{ recommendationHeadline(c) }}</p>
            <p v-if="recommendationMeta(c)" class="muted home-recommend__meta">
              {{ recommendationMeta(c) }}
            </p>
          </div>
        </section>

        <h2 class="home-section-title home-section-title--stacked">规则与现场速览</h2>

        <p v-if="!verified.length" class="muted" data-testid="verified-empty">
          这一区域暂无有依据的场所。可看地图，或改用搜索指定场所名。
        </p>

        <!-- v0.2.4 §30：divider rows，非卡。 -->
        <div
          v-for="c in verified.slice(0, 3)"
          :key="c.place.id"
          class="home-row"
          :data-testid="'verified-' + c.place.id"
          @click="emit('open', c.place.id)"
        >
          <PlaceResultRow
            :place="c.place"
            :answer="c.facts.answer"
            :answer-error="c.facts.answerError"
            :reality="c.facts.reality"
            :reality-error="c.facts.realityError"
            :species-label="speciesLabel"
            :conditions-label="conditionsLabel"
          />
          <div v-if="c.facts.answer" class="home-row__evidence-link">
            <RouterLink
              class="btn-inline"
              :to="`/place/${c.place.id}/why`"
              :data-testid="'why-' + c.place.id"
              @click.stop
            >
              查看依据 →
            </RouterLink>
          </div>
        </div>
        <section v-if="divergences.length" class="home-divergence" data-ui="home-divergence">
          <h2 class="home-section-title home-section-title--stacked">规则与现场不一致</h2>
          <div
            v-for="c in divergences"
            :key="'divergence-' + c.place.id"
            class="home-divergence__row"
            :data-testid="'divergence-' + c.place.id"
            @click="emit('open', c.place.id)"
          >
            <strong>{{ c.place.canonical_name }}</strong>
            <span>{{ divergenceText(c) }}</span>
          </div>
        </section>

        <RouterLink v-if="verified.length > 3" class="home-more btn-inline" to="/map">
          在地图查看全部附近场所 →
        </RouterLink>

        <h2 class="home-section-title home-section-title--stacked">附近待补充</h2>
        <p class="muted">这些场所我们目前没有足够依据下结论，信息不足不等于允许或禁止。</p>
        <div
          v-for="c in pending"
          :key="c.place.id"
          class="home-row"
          :data-testid="'pending-' + c.place.id"
          @click="emit('open', c.place.id)"
        >
          <div class="row home-row__head">
            <strong>{{ c.place.canonical_name }}</strong>
            <StatusBadge :semantic="c.status" />
          </div>
          <span class="muted">{{ placeTypeLabel(c.place.place_type) }}</span>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.home-recommend__row {
  cursor: pointer;
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-recommend__name {
  display: block;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
  color: var(--pa-color-text-primary);
}

.home-recommend__headline {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.home-recommend__meta {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
}

.home-divergence__row {
  cursor: pointer;
  display: grid;
  grid-template-columns: minmax(0, 0.7fr) minmax(0, 1.3fr);
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  color: var(--pa-color-text-primary);
}

.home-divergence__row span {
  color: var(--pa-color-status-conflict);
}

.home-more {
  display: inline-flex;
  margin-top: var(--pa-space-3);
}

/* v0.2.4 §30：附近/待核实 = divider rows，非卡（无圆角/无阴影/无 surface 填充）。 */
.home-row {
  cursor: pointer;
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  margin-bottom: 0;
  transition: background-color var(--pa-motion-fast) var(--pa-motion-ease);
}

.home-row:hover {
  background: var(--pa-color-surface-interactive);
}

.home-row:last-child {
  border-bottom: none;
}

.home-row__head {
  justify-content: space-between;
}

.home-row__evidence-link {
  margin-top: var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
}

.home-section-title--stacked {
  margin: var(--pa-space-5) 0 var(--pa-space-2);
}

.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

@media (max-width: 767px) {
  .home-divergence__row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }
}
</style>
