<script setup lang="ts">
/**
 * DecisionInspector — the quiet detail / dossier inspector (Design Freeze §9:
 * Search = List–Detail Workspace; Place = Dossier + Decision Inspector).
 *
 * Flat primary surface, divider-led rows, NO card. Shows only the 3–5 key
 * facts that answer the current query: current context, primary status,
 * conditions, major exception, source / verified / freshness. Data flows in
 * as props (never fetched here); semantic values come from shared
 * vocabularies (answer.ts / reality.ts / rowView.ts).
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
  <section class="decision-inspector" data-testid="decision-inspector">
    <template v-if="place">
      <header class="decision-inspector__head">
        <div class="decision-inspector__title-row">
          <h2 class="decision-inspector__name">{{ place.canonical_name }}</h2>
          <StatusBadge :semantic="status" />
        </div>
        <p class="decision-inspector__meta">
          {{ placeTypeLabel(place.place_type) }} ·
          {{ place.canonical_address ?? "地址待补充" }}
        </p>
      </header>

      <dl class="decision-inspector__facts">
        <div class="surface-row">
          <dt>当前查询</dt>
          <dd>{{ speciesLabel }} · 进入 · 公共区域</dd>
        </div>

        <div class="surface-row">
          <dt>结论</dt>
          <dd data-testid="inspector-verdict">
            <template v-if="answerError">暂时无法取得（请检查网络后重试）</template>
            <template v-else-if="answer">{{ verdict }}</template>
            <template v-else>尚未核验</template>
          </dd>
        </div>

        <div v-if="answer && !answerError" class="surface-row">
          <dt>适用范围</dt>
          <dd>{{ scope }}</dd>
        </div>

        <div v-if="conditions.length" class="surface-row">
          <dt>条件</dt>
          <dd>{{ conditions.join("、") }}</dd>
        </div>

        <div v-if="divergence" class="surface-row">
          <dt>差异</dt>
          <dd data-testid="inspector-divergence">{{ divergence }}</dd>
        </div>

        <div class="surface-row">
          <dt>近期现场</dt>
          <dd>
            <template v-if="realityError">暂时无法取得</template>
            <template v-else>{{ realityLine }}</template>
          </dd>
        </div>

        <div v-if="freshness" class="surface-row">
          <dt>时效</dt>
          <dd data-testid="inspector-freshness">{{ freshness }}</dd>
        </div>
      </dl>

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
.decision-inspector {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-4);
  min-width: 0;
}

.decision-inspector__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.decision-inspector__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
}

.decision-inspector__name {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.decision-inspector__meta {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}

.decision-inspector__facts {
  display: flex;
  flex-direction: column;
  margin: 0;
}

.decision-inspector__facts dt {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}

.decision-inspector__facts dd {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
  text-align: right;
  overflow-wrap: anywhere;
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
</style>
