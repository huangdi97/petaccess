/**
 * Consumer label mapper — the ONE place a raw enum becomes user language.
 *
 * Goal §30 / CONSUMER_VISIBLE_LANGUAGE_MAP.md: internal enums stay in the
 * API/model; the consumer layer only ever outputs user language. Pages must
 * not write their own `if (x === "pet_area")` translations — they import from
 * here (and from the shared client-core vocabularies this module re-exports).
 *
 * Every lookup is total-by-fallback: unknown values render a consumer-safe
 * generic word, NEVER the raw enum (raw values on screen are exactly what
 * failed the last human visual review — `pet_area`, `ordinary_pet · enter`,
 * `superseded`, `floor`).
 */
import {
  conditionLabel,
  placeTypeLabel,
  ruleSummaryLabel,
  type PlaceSummary,
} from "@petaccess/client-core";

export { conditionLabel, placeTypeLabel, ruleSummaryLabel };

/** Zones (services/api/app/models/enums.py → ZoneType). */
export const ZONE_TYPE_LABELS: Record<string, string> = {
  area: "公共区域",
  floor: "楼层",
  children_area: "儿童区",
  pet_area: "携宠区",
  lawn: "草坪",
  plaza: "广场",
  road: "道路",
  supermarket: "超市",
  dining_area: "堂食区",
  entrance: "入口",
  elevator: "电梯",
  other: "其他区域",
};

export function zoneTypeLabel(value: string | null | undefined): string {
  return ZONE_TYPE_LABELS[value ?? ""] ?? "其他区域";
}

/** Floor reference — consumer copy, never the raw `floor`/`1F` token.
 * "1F"→"一层", "B1"→"地下一层"; anything else falls back to a safe prefix. */
const FLOOR_ZH: Record<string, string> = {
  "1F": "一层",
  "2F": "二层",
  "3F": "三层",
  "4F": "四层",
  "5F": "五层",
  "6F": "六层",
  B1: "地下一层",
  B2: "地下二层",
};

export function floorLabel(value: string | null | undefined): string {
  if (!value) return "";
  if (value.toLowerCase() === "floor") return "楼层";
  return FLOOR_ZH[value] ?? "楼层";
}

/** One consumer-friendly zone line: `一层公共区域` / `餐饮堂食区` / `户外区域`.
 * The raw DB name is not trusted on screen when it embeds floor tokens
 * (seed names like "1F 公共区" leak "1F"); otherwise the seed's own
 * consumer-readable name ("室内堂食区") is kept. */
const FLOOR_TOKEN_RE = /^(?:[0-9]+F|B[0-9]+)\s+/i;

export function zoneConsumerLine(zone: {
  name?: string | null;
  floor_ref?: string | null;
  zone_type?: string | null;
}): string {
  const rawName = (zone.name ?? "").trim();
  if (rawName && !FLOOR_TOKEN_RE.test(rawName)) return rawName;
  const floor = zone.floor_ref ? floorLabel(zone.floor_ref) : "";
  const type = zoneTypeLabel(zone.zone_type ?? "");
  if (type === "楼层" && floor) return floor;
  return floor ? `${floor}${type}` : type;
}

/** Animal scopes (AnimalScope). */
export const ANIMAL_SCOPE_LABELS: Record<string, string> = {
  dog: "犬",
  cat: "猫",
  ordinary_pet: "普通宠物",
  service_dog: "服务犬",
  other: "其他动物",
};

export function animalScopeLabel(value: string | null | undefined): string {
  return ANIMAL_SCOPE_LABELS[value ?? ""] ?? "其他动物";
}

/** Rule actions (RuleAction). */
export const RULE_ACTION_LABELS: Record<string, string> = {
  enter: "进入",
  pass_through: "通行",
  stay: "停留",
  walk: "散步",
  off_leash: "放开牵引",
  ground_contact: "落地",
  ride_elevator: "乘坐电梯",
  ride_transport: "乘坐交通工具",
  use_facility: "使用设施",
  dine: "用餐",
  stay_overnight: "过夜",
};

export function ruleActionLabel(value: string | null | undefined): string {
  return RULE_ACTION_LABELS[value ?? ""] ?? "其他动作";
}

/** Rule statuses (RuleStatus). */
export const RULE_STATUS_LABELS: Record<string, string> = {
  current: "当前生效",
  superseded: "已被取代（历史）",
  withdrawn: "已撤回",
  disputed: "存在争议",
  archived: "已归档",
  pending_review: "待复核",
};

export function ruleStatusLabel(value: string | null | undefined): string {
  return RULE_STATUS_LABELS[value ?? ""] ?? "状态未知";
}

/** Rule layers (PlaceView layerLabel). */
export const RULE_LAYER_LABELS: Record<string, string> = {
  LEGAL: "法规",
  REGULATORY_GUIDANCE: "监管指引",
  OPERATOR_POLICY: "运营方政策",
  TEMPORARY_POLICY: "临时/事件政策",
};

export function ruleLayerLabel(value: string | null | undefined): string {
  return RULE_LAYER_LABELS[value ?? ""] ?? "其他来源类型";
}

/** Mandatory levels (MandatoryLevel). */
export const MANDATORY_LEVEL_LABELS: Record<string, string> = {
  mandatory: "强制",
  advisory: "建议",
  operator_discretion: "运营方裁量",
};

export function mandatoryLevelLabel(value: string | null | undefined): string {
  return MANDATORY_LEVEL_LABELS[value ?? ""] ?? "约束力未知";
}

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

/** Amenity types (PlaceView AMENITY_LABELS). */
export const AMENITY_LABELS: Record<string, string> = {
  PET_WATER: "宠物饮水",
  WASTE_BAG: "拾便袋",
  PET_TOILET: "宠物厕所",
  PET_WASH: "宠物清洗",
  STROLLER_RENTAL: "推车租借",
  TIE_UP: "拴宠点",
  PET_HOLDING: "宠物寄存",
  PET_ELEVATOR: "宠物电梯",
  PET_ENTRANCE: "宠物入口",
  PET_ACTIVITY_AREA: "宠物活动区",
};

export function amenityLabel(value: string | null | undefined): string {
  return AMENITY_LABELS[value ?? ""] ?? "其他设施";
}

/** Coexistence attributes (PlaceView COEXISTENCE_LABELS). */
export const COEXISTENCE_LABELS: Record<string, string> = {
  ordinary_pet_indoor_dining: "室内堂食",
  ordinary_pet_outdoor_dining: "户外堂食",
  animal_on_customer_seat: "顾客座椅",
  animal_on_table_surface: "桌面",
  animal_near_food_service_area: "食品服务区附近",
  animal_in_self_service_food_area: "食品自助区",
  animal_use_customer_tableware: "使用顾客餐具",
  dedicated_pet_tableware: "专用宠物餐具",
  dedicated_pet_zone: "独立携宠区",
  zone_separation: "区域分隔",
};

export function coexistenceLabel(value: string | null | undefined): string {
  return COEXISTENCE_LABELS[value ?? ""] ?? "其他共处规则";
}

/** Coexistence values (allowed/prohibited/conditional). */
export const COEXISTENCE_VALUE_LABELS: Record<string, string> = {
  allowed: "允许",
  prohibited: "禁止",
  conditional: "有条件",
};

export function coexistenceValueLabel(value: string | null | undefined): string {
  return COEXISTENCE_VALUE_LABELS[value ?? ""] ?? "状态未知";
}

/** Entrance types (PlaceView ENTRANCE_LABELS). */
export const ENTRANCE_LABELS: Record<string, string> = {
  GENERAL: "通用入口",
  PET_DESIGNATED: "指定携宠入口",
  SERVICE: "服务通道",
  PARKING_CONNECTION: "车库连接",
  OTHER: "其他",
};

export function entranceLabel(value: string | null | undefined): string {
  return ENTRANCE_LABELS[value ?? ""] ?? "其他入口";
}

/**
 * A rule row's consumer line: "普通宠物 · 进入" — never raw enums.
 */
export function ruleSubjectLine(
  animalScope: string | null | undefined,
  action: string | null | undefined,
): string {
  return `${animalScopeLabel(animalScope)} · ${ruleActionLabel(action)}`;
}

/**
 * Source label that can never leak an internal id. An unresolved source is a
 * consumer-safe sentence, never a UUID prefix (Goal §3.4 / map §11).
 */
export function sourceLabel(issuer: string | null | undefined, hasSource: boolean): string {
  if (issuer) return issuer;
  return hasSource ? "来源信息暂不可用" : "暂无来源信息";
}

export type { PlaceSummary };
