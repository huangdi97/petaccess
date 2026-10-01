<script setup lang="ts">
/**
 * PlaceRulesPane — Place Dossier 规则 view（v0.2.4 §23）。
 *
 * 当前规则 / conditions / exceptions / rule conflicts / source /
 * effective·freshness / historical versions（折叠，progressive disclosure）。
 * 历史版本与纠错留在这里，不放 Overview。
 */
import { computed, ref } from "vue";
import type { AccessAnswer, RuleView, SourceView } from "@petaccess/client-core";
import { conditionLabel } from "@petaccess/client-core";
import {
  mandatoryLevelLabel,
  ruleLayerLabel,
  ruleStatusLabel,
  ruleSubjectLine,
  sourceLabel,
} from "../../consumer/labels";
import { answerStatusKey } from "../../answer";
import StatusBadge from "../StatusBadge.vue";
import SourceBadge from "../SourceBadge.vue";

const props = defineProps<{
  currentRules: RuleView[];
  historyRules: RuleView[];
  sourceMap: Map<string, SourceView>;
  conditions: string[];
  answer: AccessAnswer | null;
  latestVerifiedAt: string | null;
}>();

const historyOpen = ref(false);

const STALE_DAYS = 180;
function isStale(r: RuleView): boolean {
  if (!r.last_verified_at) return false;
  const age = (Date.now() - new Date(r.last_verified_at).getTime()) / 86_400_000;
  return age > STALE_DAYS;
}

const conflicts = computed(() => {
  const bad = props.currentRules.filter((r) => !r.last_verified_at);
  return {
    hasConflict: (props.answer?.conflict_state?.has_conflict ?? false) || bad.length > 1,
    note: props.answer?.conflict_state?.has_conflict
      ? "来源存在不一致：已保留全部规则，按最严结论展示，等待复核。"
      : bad.length > 1
        ? "部分规则缺少核验信息，需要人工复核（不猜测）。"
        : "",
  };
});
</script>

<template>
  <div data-ui="place-rules-view" data-testid="place-rules-view">
    <!-- 当前规则 -->
    <section class="place-section" data-testid="conditions" data-ui="place-rules">
      <h2 class="place-section__title">当前规则</h2>
      <div v-if="!currentRules.length" class="muted">暂无可靠规则结论（未收录 ≠ 没有规则）。</div>
      <div v-for="r in currentRules" :key="r.id" class="zone-row" data-testid="rule-row">
        <span class="zone-row__name">
          {{ ruleSubjectLine(r.animal_scope, r.action) }}
          <span v-if="r.rule_layer" class="tag zone-row__layer">
            {{ ruleLayerLabel(r.rule_layer) }}
          </span>
          <span v-if="r.mandatory_level" class="tag zone-row__force">
            {{ mandatoryLevelLabel(r.mandatory_level) }}
          </span>
        </span>
        <span class="zone-row__control">
          <StatusBadge :effect="r.effect" />
          <StatusBadge v-if="isStale(r)" semantic="STALE" />
        </span>
      </div>
      <StatusBadge
        v-if="answer && (answerStatusKey(answer) === 'CONFLICT' || conflicts.hasConflict)"
        semantic="CONFLICT"
      />
      <p v-if="conflicts.note" class="muted">{{ conflicts.note }}</p>
    </section>

    <!-- 进入前需满足（conditions） -->
    <section class="place-section">
      <h2 class="place-section__title">进入前需满足</h2>
      <div v-if="!conditions.length" class="muted">暂无明确条件（未收录条件 ≠ 无限制）</div>
      <div v-else class="rule-conditions">
        <p v-for="c in conditions" :key="c" class="rule-condition">{{ c }}</p>
      </div>
    </section>

    <!-- 例外区域（pending exceptions） -->
    <section
      v-if="(answer?.condition_evaluation.pending_exceptions ?? []).length"
      class="place-section"
    >
      <h2 class="place-section__title">限制区域 / 例外</h2>
      <p v-for="e in answer?.condition_evaluation.pending_exceptions ?? []" :key="e" class="muted">
        {{ conditionLabel(e) }}
      </p>
    </section>

    <!-- 依据 / 时效 —— §18 普通 text row，三条 beige bar 取消 -->
    <section class="place-section">
      <h2 class="place-section__title">依据与时效</h2>
      <div v-for="r in currentRules" :key="r.id" class="source-line" data-testid="rule-source">
        <span>
          {{ sourceLabel(sourceMap.get(r.source_id)?.issuer ?? null, true) }}
          <SourceBadge :source-type="sourceMap.get(r.source_id)?.source_type" />
        </span>
        <span class="muted">
          {{ r.last_verified_at ? `最近核验 ${r.last_verified_at.slice(0, 10)}` : "来源仍待补充" }}
        </span>
      </div>
      <p v-if="!currentRules.length" class="muted">暂无规则来源。</p>
    </section>

    <!-- 历史版本（§23 折叠，progressive disclosure） -->
    <section class="place-section" data-testid="history" data-ui="place-history">
      <h2 class="place-section__title">历史版本与纠错</h2>
      <div v-if="!historyRules.length" class="muted">暂无历史版本</div>
      <template v-else>
        <button
          type="button"
          class="disclosure-toggle"
          :aria-expanded="historyOpen"
          data-testid="history-toggle"
          @click="historyOpen = !historyOpen"
        >
          {{ historyOpen ? "收起历史版本" : "查看全部历史版本" }}
          <span class="disclosure-toggle__count">{{ historyRules.length }}</span>
        </button>
        <div v-show="historyOpen" class="history-list">
          <div v-for="r in historyRules" :key="r.id" class="zone-row">
            <span class="zone-row__name">
              {{ ruleSubjectLine(r.animal_scope, r.action) }}
              <span class="tag" style="margin-left: 6px">{{ ruleStatusLabel(r.status) }}</span>
            </span>
            <StatusBadge :effect="r.effect" />
          </div>
        </div>
      </template>
      <p class="muted history-note">
        管理方声明与用户观察并存：认领后管理方规则标注来源，用户仍可提交现场记录。
      </p>
      <RouterLink class="btn-inline" :to="`/contribute/${currentRules[0]?.place_id ?? ''}`">
        报告规则 / 贡献 →
      </RouterLink>
    </section>
  </div>
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
.zone-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: 48px;
  max-height: 64px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.zone-row:last-child {
  border-bottom: none;
}
.zone-row__name {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-1);
  font-size: var(--pa-font-size-base);
}
.zone-row__control {
  display: inline-flex;
  align-items: center;
  gap: var(--pa-space-2);
  flex-shrink: 0;
}
.tag {
  display: inline-block;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-sm);
  padding: 1px var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}
.rule-conditions {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.rule-condition {
  margin: 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
}
.source-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.source-line:last-child {
  border-bottom: none;
}
.disclosure-toggle {
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-md);
  padding: var(--pa-space-2) 0;
  cursor: pointer;
  min-height: var(--pa-size-control-md);
}
.disclosure-toggle__count {
  margin-left: var(--pa-space-1);
  color: var(--pa-color-text-muted);
}
.history-list {
  margin-top: var(--pa-space-1);
}
.history-note {
  margin: var(--pa-space-2) 0 0;
}
</style>
