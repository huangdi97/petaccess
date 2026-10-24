export const privacyInventory = [
  { item: "账号", stored: "保存", detail: "邮箱与显示名，用于登录和会话。" },
  { item: "宠物档案", stored: "保存", detail: "仅使用你主动填写、且规则判断真正需要的信息。" },
  { item: "共处边界", stored: "保存", detail: "用于逐项比对你的出行偏好，不形成场所总分。" },
  { item: "连续位置轨迹", stored: "不保存", detail: "附近查询只使用当次位置，不建立持续轨迹。" },
  { item: "现场核验位置", stored: "最小化保存", detail: "只保留核验所需的距离或精度范围。" },
  {
    item: "上传证据",
    stored: "按许可处理",
    detail: "作为私有核验材料保存；不可公开再分发的内容不会直接向消费者展示。",
  },
  { item: "变化关注", stored: "保存", detail: "仅保存你主动关注的规则变化或经核验现场更新。" },
] as const;
