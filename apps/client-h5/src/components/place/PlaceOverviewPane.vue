<script setup lang="ts">
/**
 * PlaceOverviewPane — Place Dossier 概览（v0.2.5 §10/§11/§16）。
 *
 * 结构继续：Identity → Tabs → Current Decision → Recent Reality →
 * Space Summary → Evidence Summary，但节奏调整：
 * - desktop：main column max 820（由 PlaceView 控制）；五块齐全。
 * - mobile：不再「Decision+Reality 后大片空白」——Space/Evidence 也以
 *   56–64px summary row 呈现（§11），文本不展开。
 * - Consumer copy：无工程不变量（「当前结论仅适用于这次查询。」）；无孤立 `>`。
 * - Decision 全文表达式只出现一次（去重：Primary decision full = 1）。
 */
import { computed } from "vue";
import type { AccessAnswer, CoexistenceSnapshot, Zone } from "@petaccess/client-core";
import { zoneConsumerLine } from "../../consumer/labels";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../../answer";
import { realityStateLabel } from "../../reality";
import StatusBadge from "../StatusBadge.vue";
import { session } from "@petaccess/client-core";

const props = withDefaults(
  defineProps<{
    answer: AccessAnswer | null;
    coexistence: CoexistenceSnapshot | null;
    zoneSummary: Zone[];
    primarySourceLabel: string | null;
    latestVerifiedAt: string | null;
    observationCount: number;
    /** §11：mobile 也要 Space/Evidence summary row（非展开），desktop 五块齐全。 */
    desktop?: boolean;
  }>(),
  { desktop: true },
);

const conditions = computed(() => answerConditions(props.answer));
const keyCondition = computed(() => conditions.value[0] ?? "");
const verdict = computed(() => answerVerdictLabel(props.answer));
const statusKey = computed(() => answerStatusKey(props.answer));
const speciesLabel = computed(() => {
  const s = session.activePet?.species ?? "dog";
  if (session.activePet?.service_role === "working") return "服务犬";
  return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
});
const petContext = computed(() =>
  session.activePet ? `我的宠物：${session.activePet.display_name}` : "我的宠物：未设置",
);
const realityLine = computed(() =>
  props.coexistence?.reality_answer
    ? realityStateLabel(props.coexistence.reality_answer)
    : "暂无足够现场记录",
);
const primaryEvidence = computed(
  () => props.primarySourceLabel ?? props.answer?.evidence_state.rules[0]?.issuer ?? "来源待补充",
);
/** §11 mobile：space summary row 的 value。 */
const spaceSummaryLine = computed(() =>
  props.zoneSummary.length ? `${props.zoneSummary.length} 个已收录区域` : "暂无已收录区域",
);
/** §11 mobile：evidence summary row 的 value。 */
const evidenceSummaryLine = computed(
  () =>
    `${primaryEvidence.value} · 最近核验${props.latestVerifiedAt ? ` ${props.latestVerifiedAt}` : "暂无"}`,
);
</script>

<template>
  <!-- Current Decision（§17：完整 status surface 仅此一处；§9 自然语言补充） -->
  <section class="place-section" data-testid="section-answer" data-ui="place-decision">
    <h2 class="place-section__title">当前结论</h2>
    <div class="sub-answer sub-answer--mine" data-testid="answer">
      <p v-if="desktop" class="muted sub-answer__context" data-testid="answer-context">
        {{ petContext }} · {{ speciesLabel }} · 进入 · 公共区域
      </p>
      <StatusBadge :semantic="statusKey" />
      <p class="status" data-testid="answer-status">{{ verdict }}</p>
      <p v-if="keyCondition" class="muted" data-testid="answer-conditions">
        需满足：{{ keyCondition }}
      </p>
      <p v-if="answer" class="muted sub-answer__note">当前结论仅适用于这次查询。</p>
    </div>
  </section>

  <!-- Recent Reality：mobile 保留一行 teaser + CTA（§11）。 -->
  <section class="place-section" data-ui="place-reality-overview" data-testid="overview-reality">
    <h2 class="place-section__title">最近现场</h2>
    <p class="muted" data-testid="overview-reality-line">{{ realityLine }}</p>
    <p v-if="observationCount > 0 && desktop" class="muted overview-note">
      {{ observationCount }} 条现场记录
    </p>
    <RouterLink class="btn-inline" :to="`?view=reality`" data-testid="overview-reality-link">
      查看现场记录 →
    </RouterLink>
  </section>

  <!-- §11 mobile：Space summary row（56–64px，不展开）；desktop 显示多行区。 -->
  <section
    v-if="desktop"
    class="place-section"
    data-ui="place-zones-summary"
    data-testid="overview-zones"
  >
    <h2 class="place-section__title">空间概览</h2>
    <div v-for="z in zoneSummary.slice(0, 3)" :key="z.id" class="zone-row" data-ui="zone-row">
      <span class="zone-row__name">{{ zoneConsumerLine(z) }}</span>
      <span class="muted zone-row__hint">查看分区结论</span>
    </div>
    <p v-if="!zoneSummary.length" class="muted">暂无已收录的分区域信息</p>
    <RouterLink class="btn-inline" :to="`?view=space`" data-testid="overview-space-link">
      查看全部空间 →
    </RouterLink>
  </section>
  <RouterLink
    v-else
    class="overview-summary-row"
    :to="`?view=space`"
    data-testid="overview-zones"
    data-ui="place-zones-summary"
  >
    <span class="overview-summary-row__label">空间</span>
    <span class="overview-summary-row__value">{{ spaceSummaryLine }}</span>
    <span class="overview-summary-row__cta">查看 →</span>
  </RouterLink>

  <!-- §11 mobile：Evidence summary row；desktop 显示详情区。 -->
  <section
    v-if="desktop"
    class="place-section"
    data-ui="place-evidence-summary"
    data-testid="overview-evidence"
  >
    <h2 class="place-section__title">证据与来源</h2>
    <div class="evidence-summary-grid">
      <span class="evidence-summary-grid__label">主要依据</span>
      <span class="evidence-summary-grid__value" data-testid="overview-primary-source">{{
        primaryEvidence
      }}</span>
      <span class="evidence-summary-grid__label">最近核验</span>
      <span class="evidence-summary-grid__value" data-testid="overview-latest-verified">{{
        latestVerifiedAt ?? "暂无"
      }}</span>
      <span class="evidence-summary-grid__label">现场来源</span>
      <span class="evidence-summary-grid__value" data-testid="overview-observation-count">{{
        observationCount
      }}</span>
    </div>
    <RouterLink class="btn-inline" :to="`?view=evidence`" data-testid="overview-evidence-link">
      查看证据与来源 →
    </RouterLink>
  </section>
  <RouterLink
    v-else
    class="overview-summary-row"
    :to="`?view=evidence`"
    data-testid="overview-evidence"
    data-ui="place-evidence-summary"
  >
    <span class="overview-summary-row__label">依据</span>
    <span class="overview-summary-row__value">{{ evidenceSummaryLine }}</span>
    <span class="overview-summary-row__cta">查看 →</span>
  </RouterLink>
</template>

<style scoped>
.place-section {
  margin-bottom: var(--pa-space-5);
}
.place-section__title {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.sub-answer--mine {
  border-left: var(--pa-border-width-strong) solid var(--pa-color-accent);
  border-radius: var(--pa-radius-md);
  padding: var(--pa-space-4);
  background: var(--pa-color-surface-muted);
}
.sub-answer__context {
  margin: 0 0 var(--pa-space-1);
}
.sub-answer__note {
  margin: var(--pa-space-2) 0 0;
  color: var(--pa-color-text-secondary);
}
.status {
  margin: var(--pa-space-2) 0 var(--pa-space-1);
  font-size: var(--pa-font-size-decision);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-decision);
  color: var(--pa-color-text-primary);
}
.overview-note {
  margin: var(--pa-space-1) 0 0;
}
.zone-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: 48px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.zone-row:last-child {
  border-bottom: none;
}
.zone-row__hint {
  font-size: var(--pa-font-size-sm);
}
.evidence-summary-grid {
  display: grid;
  grid-template-columns: 6rem 1fr;
  gap: var(--pa-space-1) var(--pa-space-3);
  margin: var(--pa-space-2) 0;
}
.evidence-summary-grid__label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}
.evidence-summary-grid__value {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
}

/* §11 mobile summary row：56–64px、无 card、divider-led。 */
.overview-summary-row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: 60px;
  max-height: 68px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  text-decoration: none;
  color: var(--pa-color-text-primary);
}
.overview-summary-row:last-child {
  border-bottom: none;
}
.overview-summary-row__label {
  flex: 0 0 auto;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
.overview-summary-row__value {
  flex: 1 1 auto;
  min-width: 0;
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.overview-summary-row__cta {
  flex: 0 0 auto;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-accent);
}
</style>

@media (min-width: 768px) {
  .sub-answer--mine {
    border-radius: 0;
    padding: var(--pa-space-2) 0 var(--pa-space-2) var(--pa-space-4);
    background: transparent;
  }

  .status {
    font-size: var(--pa-font-size-24);
    line-height: var(--pa-line-height-32);
  }
}
