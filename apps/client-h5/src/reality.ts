/**
 * v0.9-R1 H5 reality vocabulary — the ONE translation of reality semantics.
 *
 * Mirrors the backend vocabulary exactly (app/services/reality_summary.py and
 * app/services/rule_reality_divergence.py). A page that invented its own word
 * for a state would be a second interpreter nobody reviews, so every reality
 * state, divergence state and freshness bucket renders through here.
 *
 * Honesty rules baked into the copy (same red lines as the backend):
 *   • NO_RECENT_RECORD / INSUFFICIENT_OBSERVATION are never "没有动物".
 *   • One observation is never "经常/高频" (the backend emits no frequency word).
 *   • Expired facts are never presented as recent.
 */

import type { RealityAnswer, RuleRealityDivergence } from "@petaccess/client-core";

/** One-line reader copy for each of the six RealitySummary states. */
export const REALITY_STATE_LABELS: Record<string, string> = {
  OBSERVED_RECENTLY: "近期现场有动物出现",
  OBSERVED_HISTORICALLY: "仅有历史记录，未呈现为近期",
  MULTI_EVIDENCE_OBSERVED: "多来源证实近期现场有动物",
  NO_RECENT_RECORD: "暂无近期现场记录（≠ 没有动物）",
  INSUFFICIENT_OBSERVATION: "现场记录不足或未完成人工核验",
  DISPUTED: "现场记录存在争议",
};

/** One-line reader copy for each of the six divergence states (AC8). */
export const DIVERGENCE_LABELS: Record<string, string> = {
  RULE_REALITY_ALIGNED: "规则与现实一致",
  RULE_PROHIBITS_BUT_OBSERVED: "规则禁止，但现场近期有动物出现",
  RULE_ALLOWS_BUT_NO_RECENT_RECORD: "规则允许，但暂无近期现场记录",
  RULE_UNKNOWN_BUT_OBSERVED: "规则未知，但现场近期有动物出现",
  RULE_CONDITIONAL_AND_OBSERVED: "规则附条件，现场近期有动物出现",
  INSUFFICIENT_DATA: "信息不足，无法对比",
};

export const FRESHNESS_LABELS: Record<string, string> = {
  FRESH: "7 天内",
  RECENT: "30 天内",
  AGING: "90 天内",
  HISTORICAL: "1 年内",
  EXPIRED_FOR_SUMMARY: "超过 1 年（不计入近期）",
};

/** The state as neutral tone; null/unknown never gets a green badge. */
export function realityTone(state: string | undefined): string {
  switch (state) {
    case "OBSERVED_RECENTLY":
    case "MULTI_EVIDENCE_OBSERVED":
      return "info";
    case "DISPUTED":
    case "INSUFFICIENT_OBSERVATION":
      return "warn";
    case "NO_RECENT_RECORD":
      return "neutral";
    default:
      return "neutral";
  }
}

export function realityStateLabel(answer: RealityAnswer | null | undefined): string {
  if (!answer) return "暂无近期现场记录（≠ 没有动物）";
  return REALITY_STATE_LABELS[answer.state] ?? answer.state;
}

export function divergenceLabel(d: RuleRealityDivergence | null | undefined): string {
  if (!d) return "信息不足，无法对比";
  return DIVERGENCE_LABELS[d.state] ?? d.state;
}

/** Human-readable staff response action counts (facts only, no score). */
export function staffResponseLines(staff: { response_action: string; count: number }[]): string[] {
  return staff.map((s) => `${s.response_action}：${s.count} 次`);
}

/** Facility facts with verified freshness. */
export function facilityLines(facilities: {
  facility_type: string;
  count: number;
  operational_state: string;
  last_verified_at: string | null;
}[]): string[] {
  return facilities.map((f) => {
    const op = f.operational_state === "active" ? "" : `（${f.operational_state}）`;
    const fresh = f.last_verified_at ? `，最近核验 ${f.last_verified_at.slice(0, 10)}` : "";
    return `${f.facility_type}${op}：${f.count} 处${fresh}`;
  });
}