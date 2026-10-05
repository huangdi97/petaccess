/**
 * Reality-specific consumer vocabulary.
 *
 * Keep staff / observation / facility enums out of page components so raw
 * domain tokens never reach consumer copy. Every mapper is total-by-fallback.
 */

/** Observed actions (ObservedAction). */
export const OBSERVED_ACTION_LABELS: Record<string, string> = {
  entered: "进入",
  present: "在场",
  stayed: "停留",
  dined_near_table: "在餐桌附近用餐",
  on_customer_seat: "在顾客座椅上",
  on_table_surface: "在桌面上",
  near_food_service: "在食品服务区附近",
  in_self_service_food_area: "在自助食品区",
  leashed: "牵引中",
  off_leash: "未牵引",
  in_carrier: "装载中",
  in_stroller: "推车中",
};

export function observedActionLabel(value: string | null | undefined): string {
  return OBSERVED_ACTION_LABELS[value ?? ""] ?? "其他观察动作";
}

/** Staff response actions (StaffResponseAction / ObservationStaffAction). */
export const STAFF_ACTION_LABELS: Record<string, string> = {
  // Legacy onsite ObservationStaffAction.
  explicitly_allowed: "明确允许",
  explicitly_refused: "明确拒绝",
  asked_to_remove: "要求带离",
  no_interaction_observed: "未观察到互动",
  interaction_unknown: "互动情况未知",

  // v0.9 Reality StaffResponseAction.
  proactive_accommodation: "主动提供便利",
  provide_water: "提供饮水",
  provide_container_or_stroller: "提供宠物箱或推车",
  direct_to_allowed_zone: "引导到允许区域",
  remind_leash: "提醒牵引",
  require_carrier: "要求使用宠物箱或包",
  request_relocation: "要求更换位置",
  request_wait_outside: "要求在外等候",
  deny_entry: "拒绝进入",
  request_exit: "要求离开",
  policy_explanation: "解释场所规则",
  escalate_to_manager: "转交负责人处理",
  no_intervention_observed: "未观察到干预",
  unknown: "处理情况未知",
};

export function staffActionLabel(value: string | null | undefined): string {
  return STAFF_ACTION_LABELS[value ?? ""] ?? "处理情况未知";
}

/** Staff role only; individual identity is never consumer-visible. */
export const STAFF_ROLE_LABELS: Record<string, string> = {
  owner: "负责人",
  manager: "管理人员",
  frontline_staff: "现场工作人员",
  server: "服务人员",
  security: "安保人员",
  cleaning_staff: "保洁人员",
  front_desk: "前台人员",
  unknown_staff: "工作人员",
};

export function staffRoleLabel(value: string | null | undefined): string {
  return STAFF_ROLE_LABELS[value ?? ""] ?? "工作人员";
}

export const STAFF_AWARENESS_LABELS: Record<string, string> = {
  awareness_confirmed: "已确认工作人员注意到该情况",
  awareness_likely: "工作人员可能注意到该情况",
  awareness_unknown: "是否被工作人员注意到尚不明确",
};

export function staffAwarenessLabel(value: string | null | undefined): string {
  return STAFF_AWARENESS_LABELS[value ?? ""] ?? "是否被工作人员注意到尚不明确";
}

/** Facility operational states (FacilityOperationalState). */
export const FACILITY_STATE_LABELS: Record<string, string> = {
  active: "正常使用中",
  temporarily_unavailable: "暂时不可用",
  removed: "已移除",
  unknown: "状态未知",
};
/** Animal facility types (AnimalFacilityType) — for the reality facility summary. */
export const ANIMAL_FACILITY_LABELS: Record<string, string> = {
  outdoor_holding_cage: "户外安置笼",
  kennel: "犬舍",
  tether_point: "拴宠点",
  pet_waiting_area: "携宠等候区",
  pet_parking: "宠物暂放区",
  water_bowl: "饮水碗",
  pet_stroller: "宠物推车",
  carrier_storage: "宠物箱寄存",
  pet_entrance: "宠物入口",
  pet_elevator: "宠物电梯",
  dedicated_pet_zone: "独立携宠区",
  waste_bag_station: "拾便袋站",
  cleaning_station: "清洁站",
  washing_point: "清洗点",
  dedicated_pet_tableware: "专用宠物餐具",
  other: "其他设施",
};

export function animalFacilityLabel(value: string | null | undefined): string {
  return ANIMAL_FACILITY_LABELS[value ?? ""] ?? "其他设施";
}

export function facilityStateLabel(value: string | null | undefined): string {
  return FACILITY_STATE_LABELS[value ?? ""] ?? "状态未知";
}

/** How a verified animal facility is made available; this is not entry policy. */
export const FACILITY_ACCESS_MODE_LABELS: Record<string, string> = {
  operator_provided: "场所提供",
  self_service: "自助使用",
  staff_assisted: "需工作人员协助",
  unknown: "使用方式未确认",
};

export function facilityAccessModeLabel(value: string | null | undefined): string {
  return FACILITY_ACCESS_MODE_LABELS[value ?? ""] ?? "使用方式未确认";
}

export const FACILITY_PURPOSE_LABELS: Record<string, string> = {
  purpose_confirmed: "用途已核验",
  purpose_staff_stated: "用途来自工作人员说明",
  purpose_signage_supported: "用途有现场标识支持",
  purpose_user_inferred: "用途为用户推测",
  purpose_unknown: "用途待核验",
};

export function facilityPurposeLabel(value: string | null | undefined): string {
  return FACILITY_PURPOSE_LABELS[value ?? ""] ?? "用途待核验";
}

export function facilityPurposeIsConfirmed(value: string | null | undefined): boolean {
  return ["purpose_confirmed", "purpose_staff_stated", "purpose_signage_supported"].includes(
    value ?? "",
  );
}

export function verifiedBooleanLabel(value: boolean | null | undefined): string {
  return value === true ? "有" : value === false ? "无" : "未确认";
}
