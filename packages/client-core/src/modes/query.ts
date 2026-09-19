/**
 * Query-mode wording and rule-material summaries (design #4, #6, #12).
 *
 * This module used to also hold `evaluatePlace`: a client-side combiner that
 * asked the v1 evaluator once per zone and took the most favourable result,
 * inverting the framing again for "restrictions" mode. That was the client
 * deciding a normative result — the very thing design §10 forbids, and worse,
 * it flattened zones into a place verdict (a mall with one pet-friendly zone
 * read as enterable overall). Rule conclusions now come only from
 * `POST /places/{id}/access-answer`; what is left here is wording and the
 * "is there anything to read here" summary, neither of which is a conclusion.
 */
import type { RuleView } from "../api/client";
import type { QueryMode } from "../stores/session";

export const MODE_LABELS: Record<QueryMode, string> = {
  with_pet: "带宠出行",
  restrictions: "普通宠物限制",
  service_dog: "服务犬通行",
  rules_only: "规则地图",
};

export const CONDITION_LABELS: Record<string, string> = {
  leash_required: "需牵引",
  muzzle_required: "需嘴套",
  carrier_required: "需宠物包",
  stroller_required: "需推车",
  no_ground: "不可落地",
  registration_required: "需犬证",
  vaccination_required: "需免疫证明",
  max_weight_kg: "体重上限",
  min_weight_kg: "体重下限",
  max_shoulder_height_cm: "肩高上限",
  max_count: "数量限制",
  reservation_required: "需预约",
  advance_notice_required: "需提前告知",
  designated_entrance: "指定入口",
  designated_elevator: "指定电梯",
  designated_route: "指定路线",
  time_windows: "时段限制",
  date_windows: "日期限制",
  season: "季节限制",
  fee: "收费",
  room_restriction: "房型限制",
};

/**
 * A condition's wording. A lookup, not a conclusion: the condition itself is
 * already decided by the server and arrives inside the answer.
 */
export function conditionLabel(type: string): string {
  return CONDITION_LABELS[type] ?? type;
}

/** Latest verification + source summary for the place header. */
export function provenanceSummary(
  rules: RuleView[],
  verifications: { occurred_at: string }[],
): {
  latestVerified: string | null;
  ruleCount: number;
} {
  const verified = rules
    .map((r) => r.last_verified_at)
    .filter((v): v is string => Boolean(v))
    .sort()
    .reverse();
  return {
    latestVerified: verified[0] ?? verifications[0]?.occurred_at ?? null,
    ruleCount: rules.filter((r) => r.status === "current").length,
  };
}
