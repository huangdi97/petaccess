import type { AccessAnswer } from "@petaccess/client-core";

const COMPLIANCE_TEXT: Record<string, string> = {
  CONSISTENT: "已比较当前可用规则，暂未发现层级冲突。",
  POTENTIAL_CONFLICT: "不同来源可能存在冲突，当前结论保留提示。",
  REVIEW_REQUIRED: "不同来源仍需人工复核，系统不会自动裁决。",
  UNKNOWN: "现有依据不足，暂时无法得到更确定的规则结论。",
};

export function consumerExplanation(answer: AccessAnswer): string[] {
  const steps: string[] = ["先按当前查询对象、进入动作和适用区域筛选规则。"];

  if (answer.scope_summary.scope_level === "zone") {
    steps.push(`当前结论按「${answer.scope_summary.zone?.name ?? "当前区域"}」判断。`);
  } else if (answer.scope_summary.scope_level === "place") {
    steps.push("当前结论适用于场所整体。");
  } else if (answer.scope_summary.scope_level === "jurisdiction") {
    steps.push("当前结论由适用的辖区法规决定。");
  } else if (answer.scope_summary.scope_level === "mixed") {
    steps.push("当前结论由多个适用层级共同决定，具体范围可在规则与证据中核对。");
  } else {
    steps.push("当前查询没有找到足够可靠的适用规则。");
  }

  const evidenceCount = answer.evidence_state.rules.length;
  if (evidenceCount > 0) steps.push(`当前结论关联 ${evidenceCount} 条规则依据。`);

  steps.push(
    COMPLIANCE_TEXT[answer.normative_result.compliance_state] ??
      "当前来源已经按规则层级和适用范围进行比较。",
  );

  if (answer.condition_evaluation.missing_inputs.length) {
    steps.push("仍缺少部分个体或同行人条件，因此结论会保留信息不足提示。");
  }
  if (answer.conflict_state.suppressed.length) {
    steps.push("较低优先级的信息没有覆盖更高优先级的当前规则。");
  }
  if (answer.conflict_state.unresolved_conflicts.length) {
    steps.push("仍有来源之间的冲突需要人工核对。");
  }
  return steps;
}
