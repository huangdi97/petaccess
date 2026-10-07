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

export function ruleLeadConditionLabel(values: string[]): string {
  return values.length ? values.join("、") : "未补充条件";
}
