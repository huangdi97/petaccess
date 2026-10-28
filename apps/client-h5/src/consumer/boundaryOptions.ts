export interface BoundaryAttributeOption {
  value: string;
  label: string;
  stances: string[];
}

export const BOUNDARY_ATTRIBUTES: BoundaryAttributeOption[] = [
  { value: "off_leash", label: "脱绳活动", stances: ["avoid", "accept"] },
  { value: "designated_area", label: "指定活动区", stances: ["prefer", "avoid"] },
  {
    value: "indoor_access",
    label: "室内进入",
    stances: ["require_prohibited", "accept", "prefer"],
  },
  { value: "carrier_required", label: "要求装载（笼/包/推车）", stances: ["accept", "avoid"] },
  { value: "muzzle_required", label: "要求嘴套", stances: ["accept", "avoid"] },
  { value: "size_limit", label: "体型限制", stances: ["avoid", "accept"] },
  { value: "breed_limit", label: "品种限制", stances: ["avoid", "accept"] },
  { value: "peak_hours_restriction", label: "高峰时段限制", stances: ["prefer", "accept"] },
  { value: "dining_together", label: "可与同桌就餐", stances: ["prefer", "avoid"] },
  { value: "waiting_area", label: "设有等候区", stances: ["prefer", "avoid"] },
];

export const BOUNDARY_STANCE_LABELS: Record<string, string> = {
  accept: "可接受",
  avoid: "希望没有",
  require_prohibited: "必须禁止",
  prefer: "希望提供",
};

export const BOUNDARY_ATTRIBUTE_LABELS = Object.fromEntries(
  BOUNDARY_ATTRIBUTES.map((item) => [item.value, item.label]),
);
