/**
 * @petaccess/design-tokens — user-facing copy dictionaries (M2 §35).
 *
 * Every internal enum or state that can reach a screen is translated here,
 * once, with neutral wording. A .vue page that writes its own translation of
 * `INSUFFICIENT_OBSERVATION` or `REALITY_*` is a bug, not a convenience.
 *
 * Copy principles (V020_DESIGN_SYSTEM_SPEC §13 / §35):
 *   • UNKNOWN ≠ ALLOWED/PROHIBITED — "暂无…" never reads as a verdict.
 *   • Observation ≠ Rule — reality copy never claims to describe policy.
 *   • Evidence-led — every state names what was seen/verified, not a score.
 *   • Divergence uses warm warning wording, never alarm language.
 */

/* ------------------------------------------------------------------ reality */

export type RealityStateKey =
  | "OBSERVED_RECENTLY"
  | "OBSERVED_HISTORICALLY"
  | "MULTI_EVIDENCE_OBSERVED"
  | "NO_RECENT_RECORD"
  | "INSUFFICIENT_OBSERVATION"
  | "DISPUTED";

export interface RealityStateCopy {
  readonly label: string;
  readonly description: string;
  readonly ariaLabel: string;
  /** CSS vars for the calm-blue / neutral / warm palette. */
  readonly colorVar: string;
  readonly bgVar: string;
}

export const REALITY_STATE_COPY: Readonly<Record<RealityStateKey, RealityStateCopy>> = {
  OBSERVED_RECENTLY: {
    label: "近期现场有动物出现",
    description: "最近 7 天内存在经核验的现场记录。",
    ariaLabel: "近期现场有动物出现：最近七天内有经核验的现场记录",
    colorVar: "--pa-color-reality-observed",
    bgVar: "--pa-color-reality-observed-bg",
  },
  OBSERVED_HISTORICALLY: {
    label: "仅有历史记录",
    description: "过往有现场记录，但近期未见，不呈现为现状。",
    ariaLabel: "仅有历史记录：过往有现场记录，但近期未见",
    colorVar: "--pa-color-reality-historical",
    bgVar: "--pa-color-reality-historical-bg",
  },
  MULTI_EVIDENCE_OBSERVED: {
    label: "多来源证实近期出现",
    description: "多个相互独立的现场记录指向同一近期事实。",
    ariaLabel: "多来源证实近期有动物出现",
    colorVar: "--pa-color-reality-observed",
    bgVar: "--pa-color-reality-observed-bg",
  },
  NO_RECENT_RECORD: {
    label: "暂无近期现场记录",
    description: "暂无记录不代表现实中没有动物。",
    ariaLabel: "暂无近期现场记录；暂无记录不代表现实中没有动物",
    colorVar: "--pa-color-reality-insufficient",
    bgVar: "--pa-color-reality-insufficient-bg",
  },
  INSUFFICIENT_OBSERVATION: {
    label: "暂无足够现场记录",
    description: "现有记录不足或未完成人工核验，无法形成近期事实结论。",
    ariaLabel: "暂无足够现场记录，无法形成近期事实结论",
    colorVar: "--pa-color-reality-insufficient",
    bgVar: "--pa-color-reality-insufficient-bg",
  },
  DISPUTED: {
    label: "信息存在争议",
    description: "现场记录之间存在不一致，待人工复核。",
    ariaLabel: "信息存在争议：现场记录之间存在不一致，待人工复核",
    colorVar: "--pa-color-reality-disputed",
    bgVar: "--pa-color-reality-disputed-bg",
  },
};

/** Caller-safe accessor: unknown states degrade to the neutral "no record". */
export function realityCopyFor(state: string | null | undefined): RealityStateCopy {
  return (
    REALITY_STATE_COPY[(state as RealityStateKey) ?? "NO_RECENT_RECORD"] ??
    REALITY_STATE_COPY.NO_RECENT_RECORD
  );
}

/* ------------------------------------------------------------------ evidence */

export type EvidenceStateKey = "verified" | "pending" | "disputed" | "historical";

export interface EvidenceStateCopy {
  readonly label: string;
  readonly description: string;
  readonly colorVar: string;
  readonly bgVar: string;
}

export const EVIDENCE_STATE_COPY: Readonly<Record<EvidenceStateKey, EvidenceStateCopy>> = {
  verified: {
    label: "已核验",
    description: "已由至少一种核验方式确认来源。",
    colorVar: "--pa-color-evidence-verified",
    bgVar: "--pa-color-evidence-verified-bg",
  },
  pending: {
    label: "待核验",
    description: "已收录，尚无核验结论。",
    colorVar: "--pa-color-evidence-pending",
    bgVar: "--pa-color-evidence-pending-bg",
  },
  disputed: {
    label: "存在争议",
    description: "来源间不一致，待人工复核。",
    colorVar: "--pa-color-evidence-disputed",
    bgVar: "--pa-color-evidence-disputed-bg",
  },
  historical: {
    label: "历史记录",
    description: "超出时效，不呈现为现状。",
    colorVar: "--pa-color-evidence-historical",
    bgVar: "--pa-color-evidence-historical-bg",
  },
};

/* ------------------------------------------------------------------ facility */

export type FacilityStateKey = "confirmed" | "unverified";

export const FACILITY_STATE_COPY: Readonly<Record<FacilityStateKey, { label: string }>> = {
  confirmed: { label: "已核验" },
  unverified: { label: "未核验" },
};

/* ----------------------------------------------------------------- freshness */

export type FreshnessKey = "FRESH" | "RECENT" | "AGING" | "HISTORICAL" | "EXPIRED_FOR_SUMMARY";

export interface FreshnessCopy {
  readonly label: string;
  readonly detail: string;
}

/** Single source for every freshness phrase in the consumer UI. */
export const FRESHNESS_COPY: Readonly<Record<FreshnessKey, FreshnessCopy>> = {
  FRESH: { label: "近期核验", detail: "7 天内" },
  RECENT: { label: "30 天内核验", detail: "30 天内" },
  AGING: { label: "90 天内核验", detail: "90 天内" },
  HISTORICAL: { label: "历史核验", detail: "1 年内" },
  EXPIRED_FOR_SUMMARY: { label: "超出时效", detail: "超过 1 年，不计入近期" },
};

/* --------------------------------------------------------------- divergence */

export type DivergenceKey =
  | "RULE_REALITY_ALIGNED"
  | "RULE_PROHIBITS_BUT_OBSERVED"
  | "RULE_ALLOWS_BUT_NO_RECENT_RECORD"
  | "RULE_UNKNOWN_BUT_OBSERVED"
  | "RULE_CONDITIONAL_AND_OBSERVED"
  | "INSUFFICIENT_DATA";

/** Warm, non-alarm wording — divergence is a fact to reconcile, not a hazard. */
export const DIVERGENCE_COPY: Readonly<Record<DivergenceKey, string>> = {
  RULE_REALITY_ALIGNED: "规则与现实一致",
  RULE_PROHIBITS_BUT_OBSERVED: "规则禁止，但现场近期有动物出现",
  RULE_ALLOWS_BUT_NO_RECENT_RECORD: "规则允许，但暂无近期现场记录",
  RULE_UNKNOWN_BUT_OBSERVED: "规则未知，但现场近期有动物出现",
  RULE_CONDITIONAL_AND_OBSERVED: "规则附条件，现场近期有动物出现",
  INSUFFICIENT_DATA: "信息不足，无法对比",
};

/* ------------------------------------------------------------------- errors */

export type DomainErrorKind =
  | "NETWORK_OFFLINE"
  | "SERVICE_UNAVAILABLE"
  | "AUTH_EXPIRED"
  | "MAP_UNAVAILABLE"
  | "CONTENT_NOT_FOUND"
  | "UNKNOWN_ERROR";

export interface ErrorPresentation {
  kind: DomainErrorKind;
  title: string;
  description: string;
  /** Suggested retry action label; empty means the state is not retryable. */
  retryLabel: string;
}

/**
 * Unified domain error → presentation mapping (M2 §28). The consumer UI must
 * never surface 500 / SQLAlchemy / FastAPI / Tauri / Rust / stack traces;
 * every failure is folded into one of these six presentations.
 */
export const ERROR_PRESENTATIONS: Readonly<Record<DomainErrorKind, ErrorPresentation>> = {
  NETWORK_OFFLINE: {
    kind: "NETWORK_OFFLINE",
    title: "当前无网络连接",
    description: "已加载内容仍可查看；需要联网的操作已暂停。",
    retryLabel: "重新连接",
  },
  SERVICE_UNAVAILABLE: {
    kind: "SERVICE_UNAVAILABLE",
    title: "服务暂时不可用",
    description: "数据服务暂未响应，请稍后重试。",
    retryLabel: "重试",
  },
  AUTH_EXPIRED: {
    kind: "AUTH_EXPIRED",
    title: "登录已过期",
    description: "请重新登录后再继续。",
    retryLabel: "重新登录",
  },
  MAP_UNAVAILABLE: {
    kind: "MAP_UNAVAILABLE",
    title: "地图暂不可用",
    description: "地图服务未加载成功，请稍后重试或使用列表视图。",
    retryLabel: "重试",
  },
  CONTENT_NOT_FOUND: {
    kind: "CONTENT_NOT_FOUND",
    title: "未找到该内容",
    description: "它可能已被移除，或链接有误。",
    retryLabel: "",
  },
  UNKNOWN_ERROR: {
    kind: "UNKNOWN_ERROR",
    title: "出现了一点问题",
    description: "操作未能完成，请重试。",
    retryLabel: "重试",
  },
};
