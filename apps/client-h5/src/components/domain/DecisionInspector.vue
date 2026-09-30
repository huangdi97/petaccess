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
import {
  answerConditions,
  answerScopeLabel,
  answerStatusKey,
  answerVerdictLabel,
} from "../../answer";
import { freshnessLineFor } from "../../consumer/rowView";
import { divergenceLabel, realityStateLabel } from "../../reality";
import StatusBadge from "../StatusBadge.vue";
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

const status = computed(() => answerStatusKey(props.answer));
const scope = computed(() => answerScopeLabel(props.answer, props.speciesLabel));
const verdict = computed(() => answerVerdictLabel(props.answer));
const conditions = computed(() => answerConditions(props.answer, props.conditionsLabel));
const realityLine = computed(() =>
  props.reality ? realityStateLabel(props.reality) : "暂无足够现场记录（≠ 没有动物）",
);
const divergence = computed(() =>
  props.snapshot ? divergenceLabel(props.snapshot.divergence) : "",
);
const freshness = computed(() => freshnessLineFor(props.stale, props.fetchedAtMs, props.offline));
</script>

<template>
  <section
    class="decision-inspector"
    :class="`decision-inspector--${variant}`"
    data-testid="decision-inspector"
  >
    <template v-if="place">
      <header class="decision-inspector__head">
        <div class="decision-inspector__title-row">
          <h2 class="decision-inspector__name" data-ui="search-detail-name">
            {{ place.canonical_name }}
          </h2>
          <StatusBadge :semantic="status" />
        </div>
        <p class="decision-inspector__meta">
          {{ placeTypeLabel(place.place_type) }} ·
          {{ place.canonical_address ?? "地址待补充" }}
        </p>
      </header>
      <!-- Current Context -->
      <div class="inspector-block inspector-block--context">
        <span class="inspector-block__label">当前查询</span>
        <p class="inspector-block__value">{{ speciesLabel }} · 进入 · 公共区域</p>
      </div>

      <!-- Primary Decision: the one fact the user came for -->
      <div class="inspector-block inspector-block--decision" data-ui="search-decision">
        <span class="inspector-block__label" data-ui="search-decision-label">结论</span>
        <p class="inspector-decision" data-ui="search-decision-text" data-testid="inspector-verdict">
          <template v-if="answerError">暂时无法取得（请检查网络后重试）</template>
          <template v-else-if="answer">{{ verdict }}</template>
          <template v-else>尚未核验</template>
        </p>
        <p v-if="answer && !answerError" class="inspector-block__value inspector-scope">
          {{ scope }}
        </p>
      </div>
      <!-- Conditions: one line per requirement, only when they exist -->
      <div v-if="conditions.length" class="inspector-block" data-ui="search-conditions">
        <span class="inspector-block__label">进入前需满足</span>
        <ul class="inspector-conditions">
          <li v-for="c in conditions" :key="c" class="inspector-conditions__item">
            <span class="inspector-conditions__mark" aria-hidden="true">✓</span>
            {{ c }}
          </li>
        </ul>
      </div>

      <!-- Major Exception: divergence, only when a real difference exists -->
      <div v-if="divergence" class="inspector-block">
        <span class="inspector-block__label">与现场情况</span>
        <p class="inspector-block__value" data-testid="inspector-divergence">{{ divergence }}</p>
      </div>

      <!-- Recent Reality -->
      <div class="inspector-block" data-ui="search-reality">
        <span class="inspector-block__label">近期现场</span>
        <p class="inspector-block__value">
          <template v-if="realityError">暂时无法取得</template>
          <template v-else>{{ realityLine }}</template>
        </p>
      </div>

      <!-- Source / freshness: quiet metadata, never the headline -->
      <div v-if="freshness" class="inspector-block inspector-block--meta" data-ui="search-evidence">
        <span class="inspector-block__label">时效</span>
        <p class="inspector-block__value" data-testid="inspector-freshness">{{ freshness }}</p>
      </div>

      <footer class="decision-inspector__foot">
        <RouterLink class="btn primary" :to="`/place/${place.id}`" data-testid="inspector-open">
          查看完整场所
        </RouterLink>
      </footer>
    </template>

    <p v-else class="decision-inspector__hint">
      从结果中选择一个场所，查看当前查询下的结论与现场摘要。
    </p>
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
  font-size: var(--pa-font-size-30);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-38);
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

.decision-inspector__foot {
  margin-top: var(--pa-space-2);
}

.decision-inspector__hint {
  margin: 0;
  padding: var(--pa-space-6) 0;
  text-align: center;
  color: var(--pa-color-text-muted);
}

/* Narrow screens: keep the decision legible without shrinking the body type. */
@media (max-width: 767px) {
  .decision-inspector,
  .decision-inspector--place {
    gap: var(--pa-space-5);
    padding-bottom: var(--pa-space-4);
  }
  .inspector-decision {
    font-size: var(--pa-font-size-24);
    line-height: var(--pa-line-height-32);
  }
}
</style>
