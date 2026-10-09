<script setup lang="ts">
/**
 * PlaceRulesPane — Place Dossier 规则 view（v0.2.5 §12–14）。
 *
 * v0.2.4 的平铺 `普通宠物 · 进入` 重复行用户无法区分上下文；v0.2.5 重组为
 * **Context → Rule**：按真实 domain data（rule.zone_id / place-level）分组——
 *   场所整体
 *     普通宠物 · 进入        有条件进入
 *     需宠物包
 *   餐饮堂食区
 *     普通宠物 · 进入        明确限制
 *   服务犬
 *     进入 · 明确允许
 * 一组：Context label + Rule subject/action + Primary status + Conditions +
 * Source/freshness（secondary）。组间 divider + 20–24 gap；无 card wall。
 * Rule Conflict 改为 inline（△ 来源不一致 · 部分信息仍待人工复核 · 查看差异 →），
 * 不渲染紫色 badge 为主角。不知道 context 时按 zone_id 分组，无法归属的规则
 * 进入「场所整体」；不伪造 zone/context。
 */
import { computed, ref } from "vue";
import type { AccessAnswer, RuleView, SourceView, Zone } from "@petaccess/client-core";
import {
  mandatoryLevelLabel,
  ruleLayerLabel,
  ruleStatusLabel,
  ruleSubjectLine,
  zoneTypeLabel,
} from "../../consumer/labels";
import { publicSourceIssuer } from "../../consumer/sourcePrivacy";
import StatusBadge from "../StatusBadge.vue";

const props = defineProps<{
  placeId: string;
  currentRules: RuleView[];
  historyRules: RuleView[];
  sourceMap: Map<string, SourceView>;
  conditions: string[];
  answer: AccessAnswer | null;
  latestVerifiedAt: string | null;
  /** v0.2.5 §12：zone 上下文（真实 domain data，决定 rule grouping 的 context label）。 */
  zoneList: Zone[];
}>();

const historyOpen = ref(false);

/** zone_id → consumer context label.
 * Use the real Zone name first ("一层" / "四层餐饮区"), not only the coarse
 * zone type ("楼层"). Collapsing several named zones into one heading recreates
 * the exact repeated-rule problem this view was designed to remove.
 */
const zoneNameById = computed(() => {
  const m = new Map<string, string>();
  for (const zone of props.zoneList) {
    const type = zoneTypeLabel(zone.zone_type);
    const name = zone.name?.trim();
    m.set(zone.id, name && name !== type ? `${name} · ${type}` : name || type || "分区");
  }
  return m;
});

/** §12 grouping：place-level（zone_id null）→「场所整体」；zone-level → 按 zone。 */
interface RuleGroup {
  contextLabel: string;
  rules: RuleView[];
}
const ruleGroups = computed<RuleGroup[]>(() => {
  const groups = new Map<string, RuleView[]>();
  const keyOf = (r: RuleView): string => {
    if (r.zone_id) return zoneNameById.value.get(r.zone_id) ?? "场所整体";
    return "场所整体";
  };
  for (const r of props.currentRules) {
    const key = keyOf(r);
    const list = groups.get(key);
    if (list) list.push(r);
    else groups.set(key, [r]);
  }
  return [...groups.entries()].map(([contextLabel, rules]) => ({ contextLabel, rules }));
});

const conflicts = computed(() => {
  const bad = props.currentRules.filter((r) => !r.last_verified_at);
  const hasConflict = (props.answer?.conflict_state?.has_conflict ?? false) || bad.length > 1;
  const note = props.answer?.conflict_state?.has_conflict
    ? "部分信息仍待人工复核"
    : bad.length > 1
      ? "部分规则缺少核验信息，需要人工复核"
      : "";
  return { hasConflict, note };
});

/** 每条 rule 的 conditions（优先 RuleView note / rule_conditions；无则本组 conditions）。 */
function ruleConditionLines(r: RuleView): string[] {
  // Only show condition copy that is attached to this rule. A page-wide
  // condition list can span several contexts and must not be repeated under
  // every rule as if it were rule-specific.
  return r.note ? [r.note] : [];
}
</script>

<template>
  <div data-ui="place-rules-view" data-testid="place-rules-view">
    <section
      v-if="conditions.length"
      class="current-query-conditions"
      data-testid="current-query-conditions"
    >
      <span class="current-query-conditions__label">当前查询需要</span>
      <p class="current-query-conditions__value">{{ conditions.join("、") }}</p>
    </section>

    <!-- §12 Rule Groups：Context → Rule；组间 divider + 20–24 gap，非 card wall。 -->
    <section
      v-for="group in ruleGroups"
      :key="group.contextLabel"
      class="rule-group"
      data-testid="rule-group"
      data-ui="place-rule-group"
    >
      <h2 class="rule-group__context" data-testid="rule-group-context">{{ group.contextLabel }}</h2>
      <div v-for="r in group.rules" :key="r.id" class="rule-card" data-testid="rule-row">
        <div class="rule-card__head">
          <span class="rule-card__subject">{{ ruleSubjectLine(r.animal_scope, r.action) }}</span>
          <span class="rule-card__status">
            <StatusBadge v-if="r.effect" :effect="r.effect" data-testid="rule-effect-badge" />
          </span>
        </div>
        <p
          v-for="c in ruleConditionLines(r)"
          :key="c"
          class="rule-card__condition"
          data-testid="rule-condition"
        >
          {{ c }}
        </p>
        <p class="muted rule-card__meta" data-testid="rule-source">
          <template v-if="r.rule_layer">
            {{ ruleLayerLabel(r.rule_layer) }}
            <template v-if="r.mandatory_level">
              · {{ mandatoryLevelLabel(r.mandatory_level) }}</template
            >
            ·
          </template>
          {{
            publicSourceIssuer(
              sourceMap.get(r.source_id)?.source_type,
              sourceMap.get(r.source_id)?.issuer,
            )
          }}
          <span v-if="r.last_verified_at"> · 最近核验 {{ r.last_verified_at.slice(0, 10) }}</span>
          <span v-else> · 来源仍待补充</span>
        </p>
      </div>
    </section>
    <p v-if="!currentRules.length" class="muted">暂无可靠规则结论。未收录不代表没有规则。</p>

    <!-- §14 Rule Conflict：inline，不渲染紫色 badge 为主角。 -->
    <section v-if="conflicts.hasConflict" class="rule-conflict" data-testid="rule-conflict">
      <p class="rule-conflict__title">△ 来源不一致</p>
      <p class="muted rule-conflict__note">{{ conflicts.note }}</p>
      <RouterLink class="btn-inline" :to="`/place/${placeId}?view=evidence`">
        查看差异 →
      </RouterLink>
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
              <span v-if="r.rule_layer" class="tag">{{ ruleLayerLabel(r.rule_layer) }}</span>
              <span class="tag">{{ ruleStatusLabel(r.status) }}</span>
            </span>
            <StatusBadge v-if="r.effect" :effect="r.effect" />
          </div>
        </div>
      </template>
      <p class="muted history-note">
        管理方声明与用户观察并存：认领后管理方规则标注来源，用户仍可提交现场记录。
      </p>
      <RouterLink class="btn-inline" :to="`/contribute/${placeId}`"> 报告规则 / 贡献 → </RouterLink>
    </section>
  </div>
</template>

<style scoped>
/* Current-query conditions are shown once, then the actual zone/context rules follow. */
.current-query-conditions {
  display: flex;
  align-items: baseline;
  gap: var(--pa-space-3);
  margin: 0 0 var(--pa-space-5);
  padding-bottom: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.current-query-conditions__label {
  flex: 0 0 auto;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.current-query-conditions__value {
  margin: 0;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}

/* 组间 divider + 20–24 gap（§13）；组内非 card wall：divider rows。 */
.rule-group {
  margin: 0 0 var(--pa-space-6);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}
.rule-group:last-of-type {
  border-bottom: none;
}
.rule-group__context {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.rule-card {
  padding: var(--pa-space-3) 0 var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.rule-card:last-child {
  border-bottom: none;
}
.rule-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
}
.rule-card__subject {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
.rule-card__status {
  flex-shrink: 0;
}
.rule-card__condition {
  margin: var(--pa-space-2) 0 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}
.rule-card__meta {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

/* §14 inline conflict — text-led, no purple badge as hero. */
.rule-conflict {
  margin: var(--pa-space-2) 0 var(--pa-space-5);
  padding: var(--pa-space-3) var(--pa-space-4);
  border-left: var(--pa-border-width-strong) solid var(--pa-color-warning);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-muted);
}
.rule-conflict__title {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
.rule-conflict__note {
  margin: 0 0 var(--pa-space-1);
}

/* 历史版本区保持 divider rows（非卡片）。 */
.place-section {
  margin-top: var(--pa-space-4);
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
}
.tag {
  display: inline-block;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-sm);
  padding: 1px var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
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

@media (max-width: 767px) {
  .rule-group {
    margin-bottom: var(--pa-space-5);
    padding-bottom: var(--pa-space-4);
  }

  .rule-group__context {
    font-size: var(--pa-font-size-lg);
  }

  .rule-card {
    padding: var(--pa-space-3) 0;
  }

  .rule-card__meta {
    line-height: var(--pa-line-height-20);
  }
}
</style>
