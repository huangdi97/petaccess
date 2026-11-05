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
import { animalFacilityLabel, facilityStateLabel, staffActionLabel } from "./consumer/labels";

/** One-line reader copy for each of the six RealitySummary states. */
export const REALITY_STATE_LABELS: Record<string, string> = {
  OBSERVED_RECENTLY: "近期现场有动物出现",
  OBSERVED_HISTORICALLY: "仅有历史记录，未呈现为近期",
  MULTI_EVIDENCE_OBSERVED: "多来源证实近期现场有动物",
  NO_RECENT_RECORD: "暂无近期现场记录",
  INSUFFICIENT_OBSERVATION: "暂无足够现场记录",
  DISPUTED: "现场记录存在争议",
};

/** One-line reader copy for each of the six divergence states (AC8). */
export const DIVERGENCE_LABELS: Record<string, string> = {
  RULE_REALITY_ALIGNED: "规则与现实一致",
  RULE_PROHIBITS_BUT_OBSERVED: "规则禁止，但现场近期有动物出现",
  RULE_ALLOWS_BUT_NO_RECENT_RECORD: "规则允许，但暂无近期现场记录",
  RULE_UNKNOWN_BUT_OBSERVED: "规则信息不足，但现场近期有动物出现",
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
  if (!answer) return "暂无近期现场记录";
  return REALITY_STATE_LABELS[answer.state] ?? "现场状态待确认";
}

export function divergenceLabel(d: RuleRealityDivergence | null | undefined): string {
  if (!d) return "信息不足，无法对比";
  return DIVERGENCE_LABELS[d.state] ?? "信息不足，无法对比";
}

/** Human-readable staff response action counts (facts only, no score). */
export function staffResponseLines(staff: { response_action: string; count: number }[]): string[] {
  return staff.map((s) => `${staffActionLabel(s.response_action)}：${s.count} 次`);
}

/** Facility facts with verified freshness. */
export function facilityLines(
  facilities: {
    facility_type: string;
    count: number;
    operational_state: string;
    last_verified_at: string | null;
  }[],
): string[] {
  return facilities.map((f) => {
    const state = facilityStateLabel(f.operational_state);
    const fresh = f.last_verified_at ? `，最近核验 ${f.last_verified_at.slice(0, 10)}` : "";
    return `${animalFacilityLabel(f.facility_type)}（${state}）：${f.count} 处${fresh}`;
  });
}

/** M7 — contribution history vocabulary (candidate type + review posture). */
export const CANDIDATE_TYPE_LABELS: Record<string, string> = {
  observed_presence: "现场出现记录",
  staff_response: "工作人员处理记录",
  animal_facility: "动物设施记录",
};

/** Review posture of a reality candidate (REVIEW_PENDING default; decisions human-only). */
export const CONTRIBUTION_STATUS_LABELS: Record<string, string> = {
  REVIEW_PENDING: "等待人工核验",
  VERIFIED: "已核验",
  VERIFIED_WITH_NOTE: "已核验（附注）",
  HOLD: "待定",
  REJECTED: "已驳回",
};

export function contributionStatusLabel(candidate: {
  review_status: string;
  reality_decision: string | null;
}): string {
  const key = candidate.reality_decision ?? candidate.review_status;
  return CONTRIBUTION_STATUS_LABELS[key] ?? "核验状态待确认";
}
