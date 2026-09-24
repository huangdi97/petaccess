<script setup lang="ts">
/**
 * RuleSummary — 规则维度的事实小结.
 *
 * Pure presentational: the status, scope and conditions all go through the
 * shared adapters in `../../answer`, so the rule conclusion is never derived
 * twice. No data fetching.
 */
import { computed } from "vue";
import type { AccessAnswer } from "@petaccess/client-core";
import { answerConditions, answerScopeLabel, answerStatusKey } from "../../answer";
import RuleStatus from "./RuleStatus.vue";

const props = withDefaults(
  defineProps<{
    answer?: AccessAnswer | null;
    speciesLabel?: string;
    showScope?: boolean;
    showConditions?: boolean;
  }>(),
  { answer: null, speciesLabel: "普通犬", showScope: true, showConditions: true },
);

defineOptions({ name: "RuleSummary" });

const scopeLabel = computed(() => answerScopeLabel(props.answer, props.speciesLabel));
const conditions = computed(() => answerConditions(props.answer));

/** Unknown line: the platform never turns "no rule found" into a verdict. */
const NO_RULE_LINE = "尚未核验：在已核验来源中暂未找到明确规则";
</script>

<template>
  <div class="rule-summary">
    <RuleStatus :semantic="answerStatusKey(answer)" />
    <p v-if="answer && showScope" class="rule-summary__scope">已核验：{{ scopeLabel }}</p>
    <p v-else-if="!answer" class="rule-summary__scope">{{ NO_RULE_LINE }}</p>
    <p v-if="showConditions && conditions.length" class="rule-summary__conditions">
      进入前需满足：{{ conditions.join("、") }}
    </p>
  </div>
</template>

<style scoped>
.rule-summary {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.rule-summary__scope {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}

.rule-summary__conditions {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-status-conditional);
}
</style>
