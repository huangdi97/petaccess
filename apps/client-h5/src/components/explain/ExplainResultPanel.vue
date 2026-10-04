<script setup lang="ts">
import type { AccessAnswer } from "@petaccess/client-core";
import { answerVerdictLabel } from "../../answer";

const props = defineProps<{ answer: AccessAnswer; steps: string[] }>();

const COMPLIANCE_TEXT: Record<string, string> = {
  CONSISTENT: "各层一致",
  POTENTIAL_CONFLICT: "存在潜在冲突",
  REVIEW_REQUIRED: "需人工复核",
  UNKNOWN: "信息不足",
};

const MISSING_INPUT_TEXT: Record<string, string> = {
  holder_scope: "同行人身份（是否为残障人士）",
  service_role: "动物角色（导盲犬 / 助听犬 / 其他服务犬）",
};
</script>

<template>
  <section class="explain-decision" data-testid="effective-rules">
    <span class="explain-label">当前结论</span>
    <strong class="explain-verdict" data-testid="effective-effect">
      {{ answerVerdictLabel(answer) }}
    </strong>
    <p class="muted explain-meta">
      {{ COMPLIANCE_TEXT[answer.normative_result.compliance_state] ?? "部分信息仍需核对" }}
      ·
      {{
        answer.scope_summary.scope_level === "zone"
          ? (answer.scope_summary.zone?.name ?? "当前区域")
          : answer.scope_summary.scope_level === "none"
            ? "尚无可靠规则覆盖"
            : "场所整体"
      }}
    </p>
  </section>

  <section v-if="answer.rights_information.operator_obligations.length" class="explain-section">
    <h2>需要满足</h2>
    <p>{{ answer.rights_information.operator_obligations.join("、") }}</p>
  </section>

  <section v-if="answer.condition_evaluation.missing_inputs.length" class="explain-section">
    <h2>还需要哪些信息</h2>
    <p class="muted">
      补充{{
        answer.condition_evaluation.missing_inputs
          .map((item) => MISSING_INPUT_TEXT[item] ?? "相关条件")
          .join("、")
      }}后，才能得到更确定的结论。当前信息不足不代表允许。
    </p>
  </section>

  <section class="explain-section">
    <h2>判断过程</h2>
    <ol class="explain-steps">
      <li v-for="(step, index) in props.steps" :key="index">{{ step }}</li>
    </ol>
  </section>

  <section v-if="answer.evidence_state.rules.length" class="explain-section">
    <h2>来源</h2>
    <div
      v-for="(evidence, index) in answer.evidence_state.rules"
      :key="index"
      class="explain-source"
      data-testid="trace-provenance"
    >
      {{ evidence.provenance_statement }}
    </div>
  </section>

  <section
    v-if="
      answer.conflict_state.suppressed.length ||
      answer.conflict_state.unresolved_conflicts.length
    "
    class="explain-section explain-review"
  >
    <h2>仍需人工复核</h2>
    <p v-if="answer.conflict_state.suppressed.length" class="muted">
      有 {{ answer.conflict_state.suppressed.length }} 条较低优先级信息没有作为当前结论依据。
    </p>
    <p v-if="answer.conflict_state.unresolved_conflicts.length" class="muted">
      另有 {{ answer.conflict_state.unresolved_conflicts.length }}
      组来源仍存在冲突；系统不会自动裁决。
    </p>
  </section>
</template>

<style scoped>
.explain-decision {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin-top: var(--pa-space-5);
  padding: var(--pa-space-2) 0 var(--pa-space-2) var(--pa-space-4);
  border-left: var(--pa-border-width-strong) solid var(--pa-color-accent);
}

.explain-label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.explain-verdict {
  font-size: var(--pa-font-size-28);
  line-height: var(--pa-line-height-36);
  font-weight: var(--pa-font-weight-650);
}

.explain-meta,
.explain-section > p {
  margin: 0;
}

.explain-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-section h2 {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.explain-section > p {
  max-width: 680px;
  line-height: var(--pa-line-height-23);
}

.explain-steps {
  margin: var(--pa-space-3) 0 0;
  padding-left: var(--pa-space-5);
}

.explain-steps li {
  margin-bottom: var(--pa-space-2);
  line-height: var(--pa-line-height-23);
}

.explain-source {
  padding: var(--pa-space-2) 0;
  color: var(--pa-color-text-secondary);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-review {
  border-left: var(--pa-border-width-strong) solid var(--pa-color-warning);
  padding-left: var(--pa-space-4);
}

.explain-review p + p {
  margin-top: var(--pa-space-2);
}
</style>
