<script setup lang="ts">
/**
 * PlaceResultRow — the ONE result-row presentation shared by Home and Search
 * (M3 DESIGN.md §5: Place identity → Rule 主结论 → Reality 摘要 →
 * Freshness/Evidence 元数据 → 仅相关 divergence).
 *
 * Data arrives as props: the row never fetches, never derives domain semantics.
 * Rule 结论来自统一 answer 模型（answer.ts 适配器），Reality 摘要来自
 * placeReality / snapshot 的共享词汇（reality.ts）。transport 错误以
 * answerError / realityError 显式呈现，绝不伪装成 UNKNOWN / 空态。
 */
import { computed } from "vue";
import {
  placeTypeLabel,
  type AccessAnswer,
  type CoexistenceSnapshot,
  type PlaceSummary,
  type RealityAnswer,
} from "@petaccess/client-core";
import { STATUS_SEMANTICS } from "@petaccess/design-tokens";
import StatusBadge from "../StatusBadge.vue";
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";
import { answerConditions, answerPrimarySummary, answerStatusKey } from "../../answer";
import {
  coexistenceEvidenceLine,
  coexistenceRealityLine,
  lensProjection,
  type ConsumerLens,
} from "../../consumer/rowView";

const props = withDefaults(
  defineProps<{
    place: PlaceSummary;
    answer?: AccessAnswer | null;
    answerError?: boolean;
    reality?: RealityAnswer | null;
    snapshot?: CoexistenceSnapshot | null;
    realityError?: boolean;
    /** 非空时渲染为关键 divergence（仅相关时出现）。 */
    divergence?: string;
    speciesLabel: string;
    conditionsLabel: Record<string, string>;
    /** Consumer lens — changes presentation only, never the facts (M3.1 §8.5). */
    lens?: ConsumerLens;
    /** Home's featured row can provide a larger scene/type anchor externally. */
    showIdentityGlyph?: boolean;
  }>(),
  {
    answer: null,
    answerError: false,
    reality: null,
    snapshot: null,
    realityError: false,
    divergence: "",
    lens: "",
    showIdentityGlyph: true,
  },
);

const status = computed(() => answerStatusKey(props.answer));
const statusLabel = computed(() => STATUS_SEMANTICS[status.value].label);
const conditions = computed(() => answerConditions(props.answer, props.conditionsLabel));
/** Keep the badge compact while giving the row one readable Rule sentence.
 * Do not duplicate the badge label; unknown/conflict get an explanatory line
 * instead of invented permission. */
const decisionLine = computed(() => {
  const summary = props.answer ? answerPrimarySummary(props.answer) : "";
  if (summary && summary !== statusLabel.value) return summary;
  if (status.value === "UNKNOWN") return "尚缺足够规则依据";
  if (status.value === "CONFLICT") return "规则来源尚未形成一致结论";
  return "";
});
const realityLine = computed(() => coexistenceRealityLine(props.snapshot, props.reality));
const evidenceLine = computed(() => coexistenceEvidenceLine(props.snapshot, props.reality));
const projection = computed(() =>
  lensProjection(props.lens, props.answer, props.reality, props.snapshot),
);
</script>

<template>
  <div class="place-result-row">
    <div class="place-result-row__head">
      <div class="place-result-row__identity-wrap">
        <PlaceTypeGlyph v-if="showIdentityGlyph" :place-type="place.place_type" />
        <div class="place-result-row__identity">
          <strong class="place-result-row__name">{{ place.canonical_name }}</strong>
          <span v-if="place.parent_place_name" class="place-result-row__meta"
            >所属 {{ place.parent_place_name }}</span
          >
          <span class="place-result-row__meta"
            >{{ placeTypeLabel(place.place_type) }} ·
            {{ place.canonical_address ?? "地址待补充" }}</span
          >
        </div>
      </div>
      <StatusBadge :semantic="status" class="place-result-row__badge" />
    </div>

    <!-- M3.1 lens projection：真实改变 Consumer 呈现（rule-first / reality-first），
         不改变任何 domain 事实；indoor/dining 仅上浮服务端返回的 observed_zones。 -->
    <div v-if="lens" class="place-result-row__lens" data-testid="row-lens">
      <p
        v-if="projection.headline === 'rule' && answer"
        class="place-result-row__rule"
        data-testid="row-lens-headline"
      >
        {{ answerPrimarySummary(answer) }}
      </p>
      <p v-else class="place-result-row__reality-line" data-testid="row-lens-headline">
        {{ projection.realityLine }}
      </p>
      <p
        v-if="projection.zoneFacts.length"
        class="place-result-row__meta"
        data-testid="row-lens-zones"
      >
        相关区域：{{ projection.zoneFacts.join("、") }}
      </p>
    </div>

    <!-- transport error ≠ domain fact：明确说“暂时无法取得”，不是“尚未核验” -->
    <p v-if="answerError" class="place-result-row__row-error" data-testid="row-answer-error">
      规则结论暂时无法取得 —— 请检查网络后重试。
    </p>

    <!-- The badge answers "which state"; this line answers "what does it mean"
         without repeating the same short label. -->
    <p v-else-if="!lens && decisionLine" class="place-result-row__rule" data-testid="row-rule">
      {{ decisionLine }}
    </p>

    <!-- Only the most important non-redundant condition consumes another line. -->
    <p v-if="!answerError && answer && conditions.length" class="place-result-row__conditions">
      进入前需满足：{{ conditions[0] }}
    </p>

    <!-- Reality 摘要：现场事实层，区别于 Rule -->
    <div class="place-result-row__reality">
      <span class="place-result-row__reality-label">近期现场</span>
      <p v-if="realityError" class="place-result-row__row-error" data-testid="row-reality-error">
        现场信息暂时无法取得 —— 请检查网络后重试。
      </p>
      <template v-else>
        <p class="place-result-row__reality-line">{{ realityLine }}</p>
        <p v-if="evidenceLine" class="place-result-row__meta">{{ evidenceLine }}</p>
      </template>
    </div>

    <!-- 重要 divergence 仅相关时出现 -->
    <p v-if="divergence" class="place-result-row__divergence" data-testid="row-divergence">
      {{ divergence }}
    </p>
  </div>
</template>

<style scoped>
.place-result-row {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  min-width: 0;
}

.place-result-row__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--pa-space-3);
}

.place-result-row__identity-wrap {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-3);
  min-width: 0;
}

.place-result-row__identity {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  min-width: 0;
}

.place-result-row__name {
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.place-result-row__meta {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
  line-height: var(--pa-line-height-base);
  overflow-wrap: break-word;
}

.place-result-row__badge {
  flex-shrink: 0;
}

.place-result-row__rule {
  margin: 0;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
  line-height: var(--pa-line-height-base);
}

.place-result-row__conditions {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
  line-height: var(--pa-line-height-base);
}

.place-result-row__row-error {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
  line-height: var(--pa-line-height-base);
}

.place-result-row__reality {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin-top: var(--pa-space-2);
  padding-top: var(--pa-space-2);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.place-result-row__reality-label {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}

.place-result-row__reality-line {
  margin: 0;
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-primary);
  line-height: var(--pa-line-height-base);
}

.place-result-row__divergence {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-status-conflict);
  line-height: var(--pa-line-height-base);
}
</style>
