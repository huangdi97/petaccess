/**
 * The H5 app's ONE adapter over the unified answer model (design §10).
 *
 * Every surface — home cards, search results, map markers, place detail, the
 * shared deep link, the rule trace — reads its status, scope and conditions
 * through these three functions. That is the point: the rule conclusion is
 * decided once on the server, and a page that mapped effects or picked a zone
 * label itself would be deriving a rule conclusion a second time, in a place
 * nobody reviews.
 *
 * The vocabulary is not re-invented here either: the effect → neutral-status
 * mapping lives in `@petaccess/design-tokens` alongside the badge copy, so the
 * same rule can never be named two different ways in two tabs.
 */
import { semanticForEffect, type StatusKey } from "@petaccess/design-tokens";
import { conditionLabel, type AccessAnswer } from "@petaccess/client-core";

/** The neutral status key for an answer. `null` answer ⇒ UNKNOWN, never ALLOWED. */
export function answerStatusKey(answer: AccessAnswer | null | undefined): StatusKey {
  if (!answer) return "UNKNOWN";
  if (answer.conflict_state?.has_conflict) return "CONFLICT";
  return semanticForEffect(answer.normative_result.effect).key;
}

/** Statuses that mean "a published rule speaks to this query". */
export const ANSWERED_STATUSES: readonly StatusKey[] = ["ALLOWED", "CONDITIONAL", "RESTRICTED"];

/**
 * The conclusion in words. Lives here so the rule trace and the place passport
 * cannot word the same answer two different ways — they used to, which is how
 * one screen said 「有条件进入」 about the answer another called 「有条件可进入」.
 */
export function answerVerdictLabel(answer: AccessAnswer | null | undefined): string {
  // The status badge and the large natural-language verdict must agree.
  // A provisional normative effect must never be presented as permission
  // when the server also reports unresolved source conflicts.
  if (answer?.conflict_state?.has_conflict) return "来源不一致，待复核";
  switch (answer?.normative_result.effect) {
    case "allowed":
      return "可以进入";
    case "prohibited":
      return "不可进入";
    case "conditional":
      return "有条件进入";
    default:
      return "信息不足";
  }
}

/** A compact headline cannot bypass a conflicting status using the
 * resolver's provisional summary. Never advertise permission during a
 * published-rule conflict, even in a one-line search result. */
export function answerPrimarySummary(answer: AccessAnswer | null | undefined): string {
  // Consumer list headlines are a controlled vocabulary. Server summaries are
  // useful trace material but may contain resolver/internal wording such as
  // field names; conditions and evidence are rendered in their own rows.
  return answerVerdictLabel(answer);
}

/**
 * 「已核验：<动物 · 区域>」 — the §12.1 requirement that a scope is named
 * precisely rather than as "示例公园 A 已核验".
 *
 * The zone is named only when a zone rule actually governs; when nothing is in
 * scope the label says so instead of implying the whole venue was checked.
 */
export function answerScopeLabel(
  answer: AccessAnswer | null | undefined,
  speciesLabel: string,
): string {
  if (!answer) return `${speciesLabel} · 场所整体`;
  const scope = answer.scope_summary;
  if (scope.scope_level === "zone" && scope.zone) return `${speciesLabel} · ${scope.zone.name}`;
  if (scope.scope_level === "none") return `${speciesLabel} · 尚无规则`;
  if (scope.scope_level === "jurisdiction") return `${speciesLabel} · 辖区法规`;
  return `${speciesLabel} · 场所整体`;
}

/**
 * The conditions a visitor must meet before entering.
 *
 * Three sources, all from the answer, and the order matters: the conditions the
 * published rule actually attaches, then the duties the venue owes, then whatever
 * the answer is still waiting on. The last kind is phrased as a question rather
 * than a condition — the platform cannot answer it without the user, and
 * pretending otherwise would turn "unknown" into a rule.
 */
export function answerConditions(
  answer: AccessAnswer | null | undefined,
  obligationLabels: Record<string, string> = {},
): string[] {
  if (!answer || answer.conflict_state?.has_conflict) return [];
  // Conflicting rule sources cannot yield actionable entry conditions until
  // reviewed, even if the provisional resolver reports a conditional effect.
  const out: string[] = [];
  const push = (label: string) => {
    if (label && !out.includes(label)) out.push(label);
  };
  for (const condition of answer.condition_evaluation?.conditions ?? []) {
    const type = (condition as { condition_type?: string }).condition_type;
    if (type) push(conditionLabel(type));
  }
  for (const obligation of answer.rights_information?.operator_obligations ?? []) {
    push(obligationLabels[obligation] ?? conditionLabel(obligation));
  }
  const missing = answer.condition_evaluation?.missing_inputs ?? [];
  if (missing.length) {
    const zh: Record<string, string> = {
      holder_scope: "需说明同行人身份（是否为残障人士）",
      service_role: "需说明动物角色（导盲犬 / 助听犬 / 其他服务犬）",
    };
    for (const input of missing) push(zh[input] ?? "还需补充查询信息");
  }
  return out;
}

/** Plain-language explanation lines for the rule trace (design §19). */
export function answerExplanation(answer: AccessAnswer | null | undefined): string[] {
  return answer?.explanation_items ?? [];
}
