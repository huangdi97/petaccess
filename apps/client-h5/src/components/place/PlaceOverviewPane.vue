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
import {
  animalFacilityLabel,
  facilityPurposeIsConfirmed,
  staffActionLabel,
  zoneConsumerLine,
} from "../../consumer/labels";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../../answer";
import { coexistenceRealityLine } from "../../consumer/rowView";
import { querySubjectLabel } from "../../consumer/queryContext";
import { divergenceLabel } from "../../reality";
import StatusBadge from "../StatusBadge.vue";

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
const querySubject = computed(() => `查询对象：${querySubjectLabel()}`);
const realityLine = computed(() =>
  coexistenceRealityLine(props.coexistence, props.coexistence?.reality_answer),
);
const realityMetaLine = computed(() => {
  const reality = props.coexistence?.reality_answer;
  const evidence = props.coexistence?.evidence_summary;
  if (!reality && !evidence) return "";
  const parts: string[] = [];
  const factCount = evidence?.reality_evidence_count ?? 0;
  const sourceCount = evidence?.reality_distinct_source_count ?? 0;
  if (factCount > 0) parts.push(`${factCount} 条经核验现场事实`);
  if (sourceCount > 0) parts.push(`${sourceCount} 个来源`);
  if (reality?.days_since_last_seen != null)
    parts.push(`最近动物记录 ${reality.days_since_last_seen} 天前`);
  return parts.join(" · ");
});
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

/** Canonical first-screen coexistence summary: Rule + Reality stay separate,
 * while staff handling / facilities remain factual Reality details. */
const staffSummaryLine = computed(() => {
  const rows = props.coexistence?.staff_response_summary ?? [];
  if (!rows.length) return "暂无经核验的工作人员处理记录";
  return rows
    .slice(0, 2)
    .map((item) => `${staffActionLabel(item.response_action)} × ${item.count}`)
    .join(" · ");
});

const facilitySummaryLine = computed(() => {
  const rows = props.coexistence?.facility_summary ?? [];
  if (!rows.length) return "暂无经核验的动物设施记录";
  const confirmed = rows.find((item) => facilityPurposeIsConfirmed(item.purpose_state));
  const item = confirmed ?? rows[0];
  if (!item) return "暂无经核验的动物设施记录";
  const verified = item.last_verified_at ? ` · 核验 ${item.last_verified_at.slice(0, 10)}` : "";
  const label = facilityPurposeIsConfirmed(item.purpose_state)
    ? animalFacilityLabel(item.facility_type)
    : "疑似动物相关设施 · 用途待核验";
  return `${label} × ${item.count}${verified}`;
});

const divergenceLine = computed(() => {
  const d = props.coexistence?.divergence;
  if (!d) return "";
  if (["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(d.state)) return "";
  return divergenceLabel(d);
});
</script>

<template>
  <!-- Canonical first screen: Rule + Reality are read together but never merged. -->
  <div class="place-overview-lead" data-ui="place-coexistence-lead">
    <!-- Current Decision（§17：完整 status surface 仅此一处；§9 自然语言补充） -->
    <section class="place-section" data-testid="section-answer" data-ui="place-decision">
      <h2 class="place-section__title">规则</h2>
      <div class="sub-answer sub-answer--mine" data-testid="answer">
        <p v-if="desktop" class="muted sub-answer__context" data-testid="answer-context">
          {{ querySubject }} · 进入 · 公共区域
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
      <h2 class="place-section__title">现场概览</h2>
      <p class="place-reality-headline" data-testid="overview-reality-line">{{ realityLine }}</p>
      <p v-if="realityMetaLine" class="muted overview-note">{{ realityMetaLine }}</p>
      <p v-else-if="observationCount > 0 && desktop" class="muted overview-note">
        {{ observationCount }} 条现场记录
      </p>
      <div
        v-if="staffSummaryLine || facilitySummaryLine || divergenceLine"
        class="coexistence-facts"
        data-ui="coexistence-facts"
      >
        <p v-if="staffSummaryLine" class="coexistence-fact">
          <span class="coexistence-fact__label">工作人员处理</span>
          <span class="coexistence-fact__value">{{ staffSummaryLine }}</span>
          <RouterLink class="btn-inline coexistence-fact__link" :to="`?view=reality`">
            查看处理记录 →
          </RouterLink>
        </p>
        <p v-if="facilitySummaryLine" class="coexistence-fact">
          <span class="coexistence-fact__label">动物设施</span>
          <span class="coexistence-fact__value">{{ facilitySummaryLine }}</span>
          <RouterLink class="btn-inline coexistence-fact__link" :to="`?view=space`">
            查看设施 →
          </RouterLink>
        </p>
        <p v-if="divergenceLine" class="coexistence-fact coexistence-fact--divergence">
          <span class="coexistence-fact__label">规则与现场</span>
          <span class="coexistence-fact__value">{{ divergenceLine }}</span>
          <RouterLink class="btn-inline coexistence-fact__link" :to="`?view=evidence`">
            查看依据 →
          </RouterLink>
        </p>
      </div>
      <RouterLink class="btn-inline" :to="`?view=reality`" data-testid="overview-reality-link">
        查看现场记录 →
      </RouterLink>
    </section>
  </div>

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
      <span class="evidence-summary-grid__value" data-testid="overview-observation-count">
        {{
          coexistence?.evidence_summary.reality_distinct_source_count
            ? `${coexistence.evidence_summary.reality_distinct_source_count} 个来源`
            : "暂无"
        }}
      </span>
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
    <span class="overview-summary-row__label">证据与来源</span>
    <span class="overview-summary-row__value">{{ evidenceSummaryLine }}</span>
    <span class="overview-summary-row__cta">查看 →</span>
  </RouterLink>
</template>

<style scoped>
.place-overview-lead {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: var(--pa-space-6);
  margin-bottom: var(--pa-space-6);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.place-overview-lead > .place-section {
  margin-bottom: 0;
}

.place-overview-lead > .place-section + .place-section {
  padding-left: var(--pa-space-6);
  border-left: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

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
.place-reality-headline {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
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

.coexistence-facts {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin: var(--pa-space-4) 0 var(--pa-space-2);
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.coexistence-fact {
  display: grid;
  grid-template-columns: 7rem minmax(0, 1fr);
  gap: var(--pa-space-3);
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-primary);
}

.coexistence-fact__label {
  color: var(--pa-color-text-muted);
}

.coexistence-fact__link {
  grid-column: 2;
  justify-self: start;
  white-space: nowrap;
  align-self: start;
}

.coexistence-fact--divergence {
  color: var(--pa-color-status-conflict);
}

@media (max-width: 767px) {
  .place-overview-lead {
    grid-template-columns: 1fr;
    gap: var(--pa-space-5);
    margin-bottom: var(--pa-space-5);
    padding-bottom: var(--pa-space-4);
  }

  .place-overview-lead > .place-section + .place-section {
    padding-left: 0;
    padding-top: var(--pa-space-4);
    border-left: none;
    border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  }

  .coexistence-facts {
    gap: var(--pa-space-1);
    margin-top: var(--pa-space-3);
    padding-top: var(--pa-space-2);
  }

  .coexistence-fact {
    display: grid;
    grid-template-columns: 6.4rem minmax(0, 1fr);
    align-items: start;
    gap: var(--pa-space-1) var(--pa-space-2);
  }

  .coexistence-fact__label {
    font-size: var(--pa-font-size-sm);
  }

  .coexistence-fact__value {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .coexistence-fact__link {
    display: none;
  }
}

@media (min-width: 768px) {
  .sub-answer--mine {
    border-radius: 0;
    padding: var(--pa-space-2) 0 var(--pa-space-2) var(--pa-space-4);
    background: transparent;
  }
}
</style>
