export function ruleLeadEffectLabel(effect: "allowed" | "restricted" | "conditional" | ""): string {
  if (effect === "allowed") return "明确允许";
  if (effect === "restricted") return "明确限制";
  if (effect === "conditional") return "有条件进入";
  return "";
}

export function ruleLeadSourceBasisLabel(value: string): string {
  if (value === "onsite_signage") return "现场规则牌 / 公告";
  if (value === "staff_statement") return "工作人员口头说明";
  if (value === "official_online") return "官方公开信息";
  if (value === "other") return "其他线索";
  return "来源类型不确定";
}

const RULE_LEAD_CONDITION_LABELS: Record<string, string> = {
  leash_required: "需牵引",
  carrier_required: "需宠物包",
  stroller_required: "需推车",
  no_ground: "不可落地",
};

export function ruleLeadConditionLabel(values: string[]): string {
  if (!values.length) return "未补充条件";
  return values.map((value) => RULE_LEAD_CONDITION_LABELS[value] ?? "其他待核验条件").join("、");
}
