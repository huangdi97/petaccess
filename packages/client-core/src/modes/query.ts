/**
 * Query mode → evaluator input mapping + user-facing answer synthesis
 * (design #4, #6, #12; UI 目标：先给一句答案).
 */
import type { EvaluateView, RuleView, Zone } from "../api/client";
import type { QueryMode } from "../stores/session";

export interface AnimalQuery {
  species: string;
  service_role?: string;
  weight_kg?: number | null;
  count?: number | null;
}

export const MODE_LABELS: Record<QueryMode, string> = {
  with_pet: "带宠出行",
  restrictions: "普通宠物限制",
  service_dog: "服务犬通行",
  rules_only: "规则地图",
};

export const STATUS_LABELS: Record<EvaluateView["status"], string> = {
  MATCH: "可以进入",
  CONDITIONAL: "有条件进入",
  RESTRICTED: "普通宠物明示限制",
  UNKNOWN: "信息不足",
  CONFLICT: "来源冲突待复核",
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

/** Build the evaluator request for a mode (design #4). */
export function modeQuery(mode: QueryMode, animal: AnimalQuery | null): {
  animal: AnimalQuery; intended_action: string;
} {
  switch (mode) {
    case "service_dog":
      return { animal: { species: "dog", service_role: "working" }, intended_action: "enter" };
    case "restrictions":
      return { animal: { species: "dog", service_role: "none" }, intended_action: "enter" };
    case "rules_only":
      return { animal: animal ?? { species: "other", service_role: "none" },
               intended_action: "enter" };
    case "with_pet":
    default:
      return { animal: animal ?? { species: "dog", service_role: "none" },
               intended_action: "enter" };
  }
}

/** THE one-sentence answer (design #48). */
export interface Answer {
  headline: string;
  status: EvaluateView["status"];
  /** per-zone breakdown; empty when evaluated place-wide */
  zones: ZoneAnswer[];
  obligations: string[];
  unknownInputs: string[];
  needsPetInfo: boolean;
}

export interface ZoneAnswer {
  zone: Zone;
  status: EvaluateView["status"];
  obligations: string[];
}

export function conditionLabel(type: string): string {
  return CONDITION_LABELS[type] ?? type;
}

/** Evaluate across all zones + place level and synthesize the answer. */
export async function evaluatePlace(
  mode: QueryMode,
  animal: AnimalQuery | null,
  placeId: string,
  zones: Zone[],
  evaluateFn: (body: { animal: AnimalQuery; place_id: string;
    zone_id?: string | null; intended_action: string }) => Promise<EvaluateView>,
): Promise<Answer> {
  const q = modeQuery(mode, animal);
  const zoneAnswers: ZoneAnswer[] = [];
  const obligations = new Set<string>();
  const unknownInputs = new Set<string>();
  let overall: EvaluateView["status"] = "UNKNOWN";

  const rank: Record<EvaluateView["status"], number> = {
    MATCH: 0, CONDITIONAL: 1, CONFLICT: 3, UNKNOWN: 2, RESTRICTED: 4,
  };
  // Overall answer = the most favorable applicable determination among zones
  // (a place with an allowed pet zone is enterable, with zone caveats shown).
  let best: EvaluateView["status"] = "UNKNOWN";
  const evaluated = await evaluateFn({ ...q, place_id: placeId, zone_id: null });
  for (const u of evaluated.unknown_inputs) unknownInputs.add(u.input);
  for (const c of evaluated.unmet_conditions) obligations.add(conditionLabel(c.condition_type));
  if (evaluated.status !== "UNKNOWN") best = evaluated.status;

  for (const zone of zones) {
    const r = await evaluateFn({ ...q, place_id: placeId, zone_id: zone.id });
    for (const u of r.unknown_inputs) unknownInputs.add(u.input);
    for (const c of r.unmet_conditions) {
      obligations.add(conditionLabel(c.condition_type));
    }
    if (r.status !== "UNKNOWN" && rank[r.status] < rank[best]) best = r.status;
    if (r.status !== "UNKNOWN") {
      zoneAnswers.push({
        zone,
        status: r.status,
        obligations: r.unmet_conditions.map((c) => conditionLabel(c.condition_type)),
      });
    }
  }
  overall = best;
  if (mode === "restrictions") {
    // Restriction mode inverts the framing: the answer highlights explicit limits
    overall = zoneAnswers.some((z) => z.status === "RESTRICTED") || evaluated.status === "RESTRICTED"
      ? "RESTRICTED" : "UNKNOWN";
  }
  return {
    headline: STATUS_LABELS[overall],
    status: overall,
    zones: zoneAnswers.sort((a, b) => rank[a.status] - rank[b.status]),
    obligations: [...obligations],
    unknownInputs: [...unknownInputs],
    needsPetInfo: animal === null && mode !== "rules_only",
  };
}

/** Latest verification + source summary for the place header. */
export function provenanceSummary(rules: RuleView[], verifications: { occurred_at: string }[]): {
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
