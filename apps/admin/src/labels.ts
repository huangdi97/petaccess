/**
 * Chinese labels for the enum values the admin surfaces render.
 *
 * Admin tables were printing raw wire values — `ordinary_pet`, `url_monitor`,
 * `integration_fixture`, `MATCH_PENDING` — so a reviewer reading the queue was
 * reading the API contract rather than the data. This is the same failure the
 * consumer side had with `residential_community`; the vocabulary lives in
 * `@petaccess/client-core` for the app and here for the console, so the two
 * never disagree about what `conditional` is called.
 *
 * Every lookup falls back to the raw value. A new enum member shows up
 * untranslated instead of blank, which is a visible prompt to add it — a blank
 * cell is not.
 *
 * Known gap: `@petaccess/client-core` carries the equivalent maps for the
 * consumer app (`client-core/src/labels.ts`). Admin does not depend on that
 * package, so the two are maintained separately for now. When a shared domain
 * package exists they belong in it; duplicating a *label* here is survivable,
 * whereas the consumer/admin split on *status semantics* would not be — those
 * read from the same generated schema in both apps.
 */

export const ANIMAL_SCOPE_LABELS: Record<string, string> = {
  dog: "犬",
  cat: "猫",
  pet: "宠物",
  ordinary_pet: "普通宠物",
  all: "所有动物",
  all_animals: "所有动物",
  service_dog: "服务犬",
  guide_dog: "导盲犬",
  other: "其他",
};

export const RULE_ACTION_LABELS: Record<string, string> = {
  enter: "进入",
  pass_through: "穿行",
  stay: "停留",
  walk: "遛行",
  off_leash: "解除牵引",
  ground_contact: "落地",
  feed: "喂食",
};

export const RULE_EFFECT_LABELS: Record<string, string> = {
  allowed: "允许",
  prohibited: "禁止",
  conditional: "有条件",
  unknown: "不明",
};

export const EXTRACTION_METHOD_LABELS: Record<string, string> = {
  ocr: "OCR 识别",
  user_link: "用户提交链接",
  url_link: "用户提交链接",
  url_monitor: "来源监控",
  manual: "人工录入",
  integration_fixture: "集成测试夹具",
  import: "批量导入",
  ai: "AI 抽取",
  vision: "图像识别",
};

export const CANDIDATE_STATUS_LABELS: Record<string, string> = {
  DISCOVERED: "已发现",
  EXTRACTED: "已抽取",
  MATCH_PENDING: "待匹配",
  REVIEW_PENDING: "待人工复核",
  APPROVED: "已批准",
  PUBLISHED: "已发布",
  REJECTED: "已驳回",
  WITHDRAWN: "已撤回",
  SUPERSEDED: "已被替代",
};

export const RULE_LAYER_LABELS: Record<string, string> = {
  legal: "法规层",
  template: "模板层",
  operator: "管理方层",
  site: "场所层",
};

export const EVIDENCE_CLASS_LABELS: Record<string, string> = {
  primary_source: "一手来源",
  operator_statement: "管理方声明",
  third_party: "第三方",
  user_observation: "用户观察",
  derived: "派生",
};

export const BOUNDARY_VERDICT_LABELS: Record<string, string> = {
  MATCH: "一致",
  CONFLICT: "冲突",
  UNKNOWN: "未知",
};

/** Look a value up, keeping the raw value visible when it is not yet mapped. */
export function label(map: Record<string, string>, value: string | null | undefined): string {
  if (!value) return "—";
  return map[value] ?? value;
}
