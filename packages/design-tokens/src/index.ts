/**
 * @petaccess/design-tokens — typed tokens and the neutral status vocabulary.
 *
 * Two rules from UI_UX_IMPLEMENTATION_SPEC are encoded here so they cannot drift:
 *
 *   §3  A status is NEVER conveyed by colour alone. Every status carries an
 *       icon, a text label and a colour token. `StatusSemantics` forces all three.
 *   §8  Copy is neutral. There is no ranking, no "bad venue", no "civilised
 *       index". `FORBIDDEN_COPY` is checked by the copy test.
 */

export const BREAKPOINTS = {
  sm: 0, // mobile portrait
  md: 480, // mobile landscape / small tablet
  lg: 768, // tablet
  xl: 1024, // desktop H5 / admin
} as const;

export type BreakpointKey = keyof typeof BREAKPOINTS;

/** Resolve a viewport width to the breakpoint bucket it falls into. */
export function breakpointFor(width: number): BreakpointKey {
  if (width >= BREAKPOINTS.xl) return "xl";
  if (width >= BREAKPOINTS.lg) return "lg";
  if (width >= BREAKPOINTS.md) return "md";
  return "sm";
}

/* ------------------------------------------------------------------ status */

/** Neutral access states (UI_UX_IMPLEMENTATION_SPEC §3). */
export type StatusKey =
  | "ALLOWED"
  | "CONDITIONAL"
  | "RESTRICTED"
  | "UNKNOWN"
  | "CONFLICT"
  | "STALE";

export interface StatusSemantics {
  readonly key: StatusKey;
  /** Chinese label shown to the user. Neutral wording only. */
  readonly label: string;
  /** Glyph so the state survives greyscale, colour-blindness and screenshots. */
  readonly icon: string;
  /** Screen-reader text; more explicit than the short visual label. */
  readonly ariaLabel: string;
  /** CSS custom property for the foreground colour. */
  readonly colorVar: string;
  /** CSS custom property for the tinted background. */
  readonly bgVar: string;
}

export const STATUS_SEMANTICS: Readonly<Record<StatusKey, StatusSemantics>> = {
  ALLOWED: {
    key: "ALLOWED",
    label: "明确允许",
    icon: "✓",
    ariaLabel: "明确允许：已核验来源明确允许",
    colorVar: "--pa-color-status-allowed",
    bgVar: "--pa-color-status-allowed-bg",
  },
  CONDITIONAL: {
    key: "CONDITIONAL",
    label: "有条件",
    icon: "◐",
    ariaLabel: "有条件：满足所附条件后方可进入",
    colorVar: "--pa-color-status-conditional",
    bgVar: "--pa-color-status-conditional-bg",
  },
  RESTRICTED: {
    key: "RESTRICTED",
    label: "明确限制",
    icon: "✕",
    ariaLabel: "明确限制：已核验来源明确限制",
    colorVar: "--pa-color-status-restricted",
    bgVar: "--pa-color-status-restricted-bg",
  },
  UNKNOWN: {
    key: "UNKNOWN",
    label: "尚未核验",
    icon: "?",
    ariaLabel: "尚未核验：在已核验来源中暂未找到明确规则，不代表允许",
    colorVar: "--pa-color-status-unknown",
    bgVar: "--pa-color-status-unknown-bg",
  },
  CONFLICT: {
    key: "CONFLICT",
    label: "来源存在不一致",
    icon: "⚠",
    ariaLabel: "来源存在不一致：已收录来源之间结论冲突，待人工复核",
    colorVar: "--pa-color-status-conflict",
    bgVar: "--pa-color-status-conflict-bg",
  },
  STALE: {
    key: "STALE",
    label: "需要复核",
    icon: "⟳",
    ariaLabel: "需要复核：证据超出核验时效，结论可能已变化",
    colorVar: "--pa-color-status-stale",
    bgVar: "--pa-color-status-stale-bg",
  },
};

/**
 * The resolver's `Answer.status` vocabulary (MATCH / CONDITIONAL / RESTRICTED /
 * UNKNOWN / CONFLICT) mapped onto the neutral presentation vocabulary. The
 * resolver keeps its own names; only the presentation layer is normalised, so a
 * client never has to know two vocabularies.
 */
export const ANSWER_STATUS_TO_SEMANTIC: Readonly<Record<string, StatusKey>> = {
  MATCH: "ALLOWED",
  CONDITIONAL: "CONDITIONAL",
  RESTRICTED: "RESTRICTED",
  UNKNOWN: "UNKNOWN",
  CONFLICT: "CONFLICT",
  STALE: "STALE",
};

/** A stored rule effect mapped onto the same vocabulary. */
export const EFFECT_TO_SEMANTIC: Readonly<Record<string, StatusKey>> = {
  allowed: "ALLOWED",
  conditional: "CONDITIONAL",
  prohibited: "RESTRICTED",
};

export function semanticForAnswerStatus(status: string): StatusSemantics {
  const key = ANSWER_STATUS_TO_SEMANTIC[status] ?? "UNKNOWN";
  return STATUS_SEMANTICS[key];
}

export function semanticForEffect(effect: string): StatusSemantics {
  const key = EFFECT_TO_SEMANTIC[effect] ?? "UNKNOWN";
  return STATUS_SEMANTICS[key];
}

/* ------------------------------------------------------------- source badge */

/** Foreground source badges (UI_UX_IMPLEMENTATION_SPEC §4). */
export type SourceBadgeKey =
  | "STATUTE"
  | "GOVERNMENT"
  | "OPERATOR"
  | "ONSITE"
  | "USER_REPORT"
  | "NEEDS_REVIEW"
  | "CONFLICT";

export interface SourceBadge {
  readonly key: SourceBadgeKey;
  readonly label: string;
  readonly icon: string;
}

export const SOURCE_BADGES: Readonly<Record<SourceBadgeKey, SourceBadge>> = {
  STATUTE: { key: "STATUTE", label: "官方法规", icon: "§" },
  GOVERNMENT: { key: "GOVERNMENT", label: "政府来源", icon: "⌂" },
  OPERATOR: { key: "OPERATOR", label: "管理方确认", icon: "◉" },
  ONSITE: { key: "ONSITE", label: "现场核验", icon: "◎" },
  USER_REPORT: { key: "USER_REPORT", label: "用户现场报告", icon: "☰" },
  NEEDS_REVIEW: { key: "NEEDS_REVIEW", label: "需要复核", icon: "⟳" },
  CONFLICT: { key: "CONFLICT", label: "来源不一致", icon: "⚠" },
};

/**
 * Map an internal `source_type` to a foreground badge. The backend keeps a finer
 * `evidence_strength`; the client only needs this coarse, user-meaningful set.
 */
export function badgeForSourceType(sourceType: string | null | undefined): SourceBadge {
  switch (sourceType) {
    case "statute_or_regulation":
      return SOURCE_BADGES.STATUTE;
    case "government_service":
      return SOURCE_BADGES.GOVERNMENT;
    case "official_operator_policy":
      return SOURCE_BADGES.OPERATOR;
    case "onsite_verification":
      return SOURCE_BADGES.ONSITE;
    case "ordinary_user":
      return SOURCE_BADGES.USER_REPORT;
    default:
      return SOURCE_BADGES.NEEDS_REVIEW;
  }
}

/* ---------------------------------------------------------------- copy rules */

/**
 * Page-level async and edge states (Master Goal §5.5: every core page must have
 * loading / skeleton / empty / success / partial / stale / conflict / error /
 * offline / permission-denied).
 *
 * These are *page* states, not access statuses — a place can be ALLOWED and the
 * page can still be OFFLINE. They live here for the same reason the statuses do:
 * one vocabulary, one place to edit, and a machine-checkable guarantee that each
 * state carries an icon and words rather than a colour alone.
 */
export type PageStateKey =
  | "LOADING"
  | "EMPTY"
  | "ERROR"
  | "OFFLINE"
  | "PARTIAL"
  | "STALE"
  | "CONFLICT"
  | "PERMISSION_DENIED";

export interface PageStateSemantics {
  readonly key: PageStateKey;
  /** Glyph, so the state is legible without colour. */
  readonly icon: string;
  /** Short heading. */
  readonly title: string;
  /** One neutral sentence explaining what the state does and does not mean. */
  readonly description: string;
}

export const PAGE_STATES: Readonly<Record<PageStateKey, PageStateSemantics>> = {
  LOADING: {
    key: "LOADING",
    icon: "…",
    title: "加载中",
    description: "正在取得数据。",
  },
  EMPTY: {
    key: "EMPTY",
    icon: "○",
    title: "暂无收录内容",
    description: "本平台只展示已核验收录的信息；未收录不代表该场所没有规则。",
  },
  ERROR: {
    key: "ERROR",
    icon: "!",
    title: "加载失败",
    description: "未能取得数据。在重试成功之前，页面不会展示任何推测结论。",
  },
  OFFLINE: {
    key: "OFFLINE",
    icon: "⊘",
    title: "当前无网络连接",
    description: "离线时不接受提交，以免产生未经确认的记录。已加载的内容仍可查看。",
  },
  PARTIAL: {
    key: "PARTIAL",
    icon: "◑",
    title: "信息不完整",
    description: "部分字段尚未收录，结论可能随补充证据变化。",
  },
  STALE: {
    key: "STALE",
    icon: "⟳",
    title: "需要复核",
    description: "证据超出核验时效，结论可能已变化。",
  },
  CONFLICT: {
    key: "CONFLICT",
    icon: "⚠",
    title: "来源存在不一致",
    description: "已收录来源之间结论冲突，待人工复核。",
  },
  PERMISSION_DENIED: {
    key: "PERMISSION_DENIED",
    icon: "⛔",
    title: "需要登录",
    description: "此操作需要登录后进行；未登录不会提交任何数据。",
  },
};

/** Neutral wording the product must use (UI_UX_IMPLEMENTATION_SPEC §8). */
export const REQUIRED_COPY = {
  unknownLong: "截至今日，在已核验来源中暂未找到明确规则",
  unknownShort: "尚未核验",
  observationDisclaimer: "现场记录 ≠ 场所正式政策",
  noRankingDisclaimer: "本产品不提供综合评分或场所排名",
} as const;

/** Words that must never appear in user-facing copy (UI_UX_IMPLEMENTATION_SPEC §8). */
export const FORBIDDEN_COPY: readonly string[] = [
  "雷店",
  "雷区",
  "黑榜",
  "红榜",
  "恶心",
  "脏",
  "没素质",
  "反宠",
  "爱宠人士",
  "文明指数",
  "遇宠率",
  "星级",
] as const;

/* --------------------------------------------------------------------- misc */

export const MOTION = {
  fast: "--pa-motion-fast",
  base: "--pa-motion-base",
  slow: "--pa-motion-slow",
  ease: "--pa-motion-ease",
} as const;

/** Minimum interactive target size (UI_UX_IMPLEMENTATION_SPEC §10). */
export const TOUCH_TARGET_PX = 44;
