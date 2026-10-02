<script setup lang="ts">
/**
 * DecisionInspector — the quiet detail / dossier inspector (Design Freeze §9:
 * Search = List–Detail Workspace; Place = Dossier + Decision Inspector).
 *
 * VISUAL FIDELITY (Goal §3.1): this is a *judgment surface*, not a database
 * detail table and not a card. The old `<dl>` label/value rows read as an
 * engineering form; the hierarchy is now explicit:
 *
 *   Identity → Current Context → PRIMARY DECISION (large) → Conditions →
 *   Major Exception → Recent Reality → Source/Freshness.
 *
 * Per Design Freeze §5 the inspector is a flat pane: no border, no radius, no
 * card background — only a bottom divider that separates it from the next
 * surface, and the decision block carries a thick accent left edge.
 *
 * Only the 3–5 facts that answer the current query are shown (freeze §9);
 * the full dossier stays on the Place page. Data flows in as props (never
 * fetched here); semantic values come from the shared vocabularies
 * (answer.ts / reality.ts / rowView.ts / consumer/labels.ts).
 */
import { computed } from "vue";
import {
  placeTypeLabel,
  type AccessAnswer,
  type CoexistenceSnapshot,
  type RealityAnswer,
} from "@petaccess/client-core";
import { answerConditions, answerVerdictLabel } from "../../answer";
import { freshnessLineFor } from "../../consumer/rowView";
import { realityStateLabel } from "../../reality";
const props = withDefaults(
  defineProps<{
    place: {
      id: string;
      canonical_name: string;
      place_type: string;
      canonical_address?: string | null;
    } | null;
    answer?: AccessAnswer | null;
    answerError?: boolean;
    reality?: RealityAnswer | null;
    realityError?: boolean;
    snapshot?: CoexistenceSnapshot | null;
    stale?: boolean;
    fetchedAtMs?: number | null;
    offline?: boolean;
    speciesLabel?: string;
    conditionsLabel?: Record<string, string>;
    /**
     * v0.2.3 §22/§33：search detail = large identity (28/650) + primary
     * decision 30/650, flat accent, content column ≤704px；place inspector =
     * compact (decision 24–26), label 12 / value 14–16。
     */
    variant?: "search" | "place";
  }>(),
  {
    answer: null,
    answerError: false,
    reality: null,
    realityError: false,
    snapshot: null,
    stale: false,
    fetchedAtMs: null,
    offline: false,
    speciesLabel: "普通犬",
    conditionsLabel: () => ({}),
    variant: "search",
  },
);

const verdict = computed(() => answerVerdictLabel(props.answer));
const conditions = computed(() => answerConditions(props.answer, props.conditionsLabel));
const freshness = computed(() => freshnessLineFor(props.stale, props.fetchedAtMs, props.offline));
/** §12 Evidence one-line：来源 issuer + 时效。 */
const SOURCE_RATE: Record<string, string> = {
  official_operator_policy: "运营方规则",
  onsite_signage: "现场标识",
  government_service: "政府服务",
  statute_or_regulation: "法规",
  certified_verifier: "认证核验方",
  ordinary_user: "用户提交",
  external_web_reference: "外部网页",
  imported_dataset: "导入数据",
};
const evidenceLine = computed(() => {
  const ev = props.answer?.evidence_state.rules[0];
  const issuer = ev?.issuer ?? SOURCE_RATE[ev?.source_type ?? ""] ?? "来源待补充";
  return freshness.value ? `${issuer} · ${freshness.value}` : issuer;
});
/** §12/§26：Primary Decision 的 key condition（第一条；无则不猜测）。 */
const keyCondition = computed(() => conditions.value[0] ?? "");
/** §26：限制区域（例外区域列表；无则整块不渲染）。 */
const exceptions = computed(() =>
  (props.answer?.condition_evaluation.pending_exceptions ?? []).map(
    (e) => props.conditionsLabel[e] ?? e,
  ),
);
/** §26：最近核验（来自 rules 的 last_verified_at 最近值；无则原文提示）。 */
const latestVerifiedLabel = computed(() => {
  const cut = props.answer?.evidence_state.rules[0]?.source_id
    ? (props.snapshot?.generated_at ?? null)
    : null;
  return cut ? cut.slice(0, 10) : "暂无";
});
/** §12（search）one-line reality summary：撇去括号补充，保持单行。 */
const realityLineForSearch = computed(() => {
  if (!props.reality) return "暂无足够现场记录";
  const label = realityStateLabel(props.reality);
  return label.replace(/\s*（.*?）\s*$/, "");
});
/** §26（place）：现场 —— 暂无足够记录，不再输出长解释。 */
const realityLineForPlace = computed(() =>
  props.reality ? realityStateLabel(props.reality) : "暂无足够记录",
);
</script>

<template>
  <section
    class="decision-inspector"
    :class="`decision-inspector--${variant}`"
    data-testid="decision-inspector"
  >
    <template v-if="place">
      <!-- v0.2.4 §12：Search detail 保留 identity；v0.2.5 §16：place inspector
           不再重复 Place Name/地址（identity 只在 main column）。 -->
      <header v-if="variant === 'search'" class="decision-inspector__head">
        <h2 class="decision-inspector__name" data-ui="search-detail-name">
          {{ place.canonical_name }}
        </h2>
        <p class="decision-inspector__meta">
          {{ placeTypeLabel(place.place_type) }} ·
          {{ place.canonical_address ?? "地址待补充" }}
        </p>
      </header>

      <!-- Search detail（§12 严格顺序）：Identity → Query → Decision → Reality →
           Evidence/Source → CTA；place inspector（§26）走下方紧凑结构。 -->
      <template v-if="variant === 'search'">
        <div class="inspector-block inspector-block--context">
          <span class="inspector-block__label">当前查询</span>
          <p class="inspector-block__value">{{ speciesLabel }} · 进入 · 公共区域</p>
        </div>

        <div class="inspector-block inspector-block--decision" data-ui="search-decision">
          <span class="inspector-block__label" data-ui="search-decision-label">结论</span>
          <p
            class="inspector-decision"
            data-ui="search-decision-text"
            data-testid="inspector-verdict"
          >
            <template v-if="answerError">暂时无法取得（请检查网络后重试）</template>
            <template v-else-if="answer">{{ verdict }}</template>
            <template v-else>尚未核验</template>
          </p>
          <p
            v-if="keyCondition"
            class="inspector-block__value inspector-scope"
            data-testid="inspector-key-condition"
          >
            需满足：{{ keyCondition }}
          </p>
        </div>

        <div class="inspector-secondary">
          <div class="inspector-block" data-ui="search-reality">
            <span class="inspector-block__label">近期现场</span>
            <p class="inspector-block__value">
              <template v-if="realityError">暂时无法取得</template>
              <template v-else>{{ realityLineForSearch }}</template>
            </p>
          </div>

          <div class="inspector-block inspector-block--meta" data-ui="search-evidence">
            <span class="inspector-block__label">证据与来源</span>
            <p class="inspector-block__value" data-testid="inspector-evidence">
              {{ evidenceLine }}
            </p>
          </div>
        </div>
        <footer class="decision-inspector__foot">
          <RouterLink class="btn-inline" :to="`/place/${place.id}`" data-testid="inspector-open">
            查看完整场所 →
          </RouterLink>
        </footer>
      </template>

      <!-- Place inspector（§26 固定内容，无 CTA 大按钮，底部 text link） -->
      <template v-else>
        <div class="inspector-block inspector-block--context">
          <span class="inspector-block__label">当前查询</span>
          <p class="inspector-block__value">{{ speciesLabel }} · 进入 · 公共区域</p>
        </div>

        <div class="inspector-block inspector-block--decision" data-ui="search-decision">
          <span class="inspector-block__label" data-ui="search-decision-label">结论</span>
          <p
            class="inspector-decision"
            data-ui="search-decision-text"
            data-testid="inspector-verdict"
          >
            <template v-if="answerError">暂时无法取得（请检查网络后重试）</template>
            <template v-else-if="answer">{{ verdict }}</template>
            <template v-else>尚未核验</template>
          </p>
        </div>

        <div v-if="keyCondition" class="inspector-block">
          <span class="inspector-block__label">需要</span>
          <p class="inspector-block__value" data-testid="inspector-key-condition">
            {{ keyCondition }}
          </p>
        </div>

        <div v-if="exceptions.length" class="inspector-block">
          <span class="inspector-block__label">限制区域</span>
          <p class="inspector-block__value">{{ exceptions.join("、") }}</p>
        </div>

        <div class="inspector-block">
          <span class="inspector-block__label">依据</span>
          <p class="inspector-block__value">{{ evidenceLine }}</p>
        </div>

        <div class="inspector-block">
          <span class="inspector-block__label">最近核验</span>
          <p class="inspector-block__value">{{ latestVerifiedLabel }}</p>
        </div>

        <div class="inspector-block" data-ui="search-reality">
          <span class="inspector-block__label">现场</span>
          <p class="inspector-block__value">
            <template v-if="realityError">暂时无法取得</template>
            <template v-else>{{ realityLineForPlace }}</template>
          </p>
        </div>

        <footer class="decision-inspector__foot decision-inspector__foot--link">
          <RouterLink
            class="btn-inline"
            :to="`/place/${place.id}/evidence`"
            data-testid="inspector-evidence-link"
          >
            查看完整证据 →
          </RouterLink>
        </footer>
      </template>
    </template>

    <div v-else class="decision-inspector__onboarding">
      <!-- v0.2.5 §18：右侧纯 onboarding 文案，去重复 CTA（左侧 pane 保留 primary）。 -->
      <h2 class="decision-inspector__onboarding-title">选择一个场所后，</h2>
      <p class="decision-inspector__onboarding-body">这里会显示准入结论、条件和最近现场。</p>
    </div>
  </section>
</template>
<style scoped>
/* Flat pane per Design Freeze §5: inspector is NOT a card. It fills the
 * available column height so the workspace reads as a composed two-pane
 * surface instead of a short block floating in empty canvas (Goal §3.1:
 * "空而不静" — the inspector must own its space).
 *
 * v0.2.3 §22 (search detail) vs §33 (place inspector) sizes are toggled by
 * the `variant` prop — the same component, two type sizes, one hierarchy. */
.decision-inspector {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-28);
  min-width: 0;
  min-height: calc(100vh - 112px);
  align-self: stretch;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  padding-bottom: var(--pa-space-5);
}

.decision-inspector--place {
  gap: var(--pa-space-5);
}

.decision-inspector__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

/* §22：detail 内容列最大 704px，不铺满整个 DetailPane（972）。 */
.decision-inspector--search {
  max-width: var(--pa-layout-detail-content);
}

.decision-inspector__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
}

/* §22 identity: place name = page identity 28/36/650（Blueprint §18 字体蓝图）。 */
.decision-inspector__name {
  margin: 0;
  font-size: var(--pa-font-size-28);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-36);
  color: var(--pa-color-text-primary);
}

.decision-inspector--place .decision-inspector__name {
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
}

.decision-inspector__meta {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-muted);
}

.inspector-block {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.inspector-block__label {
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
}

.inspector-block__value {
  margin: 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-primary);
  overflow-wrap: anywhere;
}

/* §22 primary decision: FLAT accent block — label 12 / decision 30 / support
 * 15 / left accent 2px / padding-left 16。蓝图明确「不能做成大卡」：
 * no surface fill, no radius, no shadow — the accent edge + size carry it.
 * （生活气息收口的暖 surface 在决策块上按蓝图取消） */
.inspector-block--decision {
  border-left: var(--pa-border-width-strong) solid var(--pa-color-accent);
  padding-left: var(--pa-space-4);
  padding-top: var(--pa-space-1);
  padding-bottom: var(--pa-space-2);
}

.inspector-decision {
  margin: 0;
  /* v0.2.4 §44：primary decision 桌面 28/36/650（不再到处 30px）。 */
  font-size: var(--pa-font-size-decision);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-decision);
  color: var(--pa-color-text-primary);
}

.decision-inspector--place .inspector-decision {
  font-size: var(--pa-font-size-26);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-32);
}

.inspector-scope {
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-secondary);
}

/* Conditions: one readable line each, check-marked, never a comma blob. */
.inspector-conditions {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.inspector-conditions__item {
  display: flex;
  align-items: baseline;
  gap: var(--pa-space-2);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-primary);
}

.inspector-conditions__mark {
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-bold);
}

.inspector-block--meta {
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

/* v0.2.7 §22：secondary evidence grouping —— reality + evidence 归组为
   次要信息区（顶部细分隔线），primary decision 保持唯一强焦点。 */
.inspector-secondary {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.inspector-secondary .inspector-block--meta {
  border-top: none;
  padding-top: 0;
}

.decision-inspector__foot {
  margin-top: var(--pa-space-2);
}

/* §26：place inspector 底部用 text link（查看完整证据 →），不放 CTA 大按钮。 */
.decision-inspector__foot--link {
  margin-top: var(--pa-space-3);
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.decision-inspector__foot--link a {
  font-size: var(--pa-font-size-md);
}

.decision-inspector__hint {
  margin: 0;
  padding: var(--pa-space-6) 0;
  text-align: center;
  color: var(--pa-color-text-muted);
}

.decision-inspector__onboarding {
  /* §23：右侧 onboarding copy，max-width 520，top 108–140，禁止右侧空白。 */
  max-width: 520px;
  padding-top: 108px;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
}

.decision-inspector__onboarding-title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.decision-inspector__onboarding-body {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
}

/* Narrow screens: keep the decision legible without shrinking the body type. */
@media (max-width: 767px) {
  .decision-inspector,
  .decision-inspector--place {
    gap: var(--pa-space-5);
    padding-bottom: var(--pa-space-4);
  }

  .decision-inspector__onboarding {
    padding-top: var(--pa-space-6);
  }

  .inspector-decision {
    font-size: var(--pa-font-size-24);
    line-height: var(--pa-line-height-32);
  }
}
</style>
