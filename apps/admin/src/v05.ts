/**
 * Admin v0.5 shared vocabulary.
 *
 * These constants mirror the API-side vocab classes (app.models.v05 /
 * app.models.evidence). They exist so the UI can offer the *legal* transitions
 * and vocabularies instead of letting an operator guess. If the API vocabulary
 * changes, this file must change with it.
 */

// ---- rule candidate state machine (app.models.v05.CANDIDATE_TRANSITIONS)
export const CANDIDATE_TRANSITIONS: Record<string, string[]> = {
  DISCOVERED: ["EXTRACTED", "REJECTED"],
  EXTRACTED: ["MATCH_PENDING", "REJECTED"],
  MATCH_PENDING: ["REVIEW_PENDING", "REJECTED"],
  REVIEW_PENDING: ["APPROVED", "REJECTED"],
  APPROVED: ["PUBLISHED", "REJECTED"],
  PUBLISHED: ["SUPERSEDED"],
  REJECTED: [],
  SUPERSEDED: [],
};

export const CANDIDATE_STATUSES = [
  "DISCOVERED",
  "EXTRACTED",
  "MATCH_PENDING",
  "REVIEW_PENDING",
  "APPROVED",
  "PUBLISHED",
  "REJECTED",
  "SUPERSEDED",
];

// ---- observation candidate state machine (app.models.evidence)
export const OBSERVATION_TRANSITIONS: Record<string, string[]> = {
  DISCOVERED: ["EXTRACTED", "REJECTED"],
  EXTRACTED: ["PLACE_MATCH_PENDING", "REJECTED"],
  PLACE_MATCH_PENDING: ["REVIEW_PENDING", "REJECTED"],
  REVIEW_PENDING: ["APPROVED", "REJECTED"],
  APPROVED: ["PUBLISHED", "REJECTED"],
  PUBLISHED: ["SUPERSEDED"],
  REJECTED: [],
  SUPERSEDED: [],
};

export const OBSERVATION_STATUSES = [
  "DISCOVERED",
  "EXTRACTED",
  "PLACE_MATCH_PENDING",
  "REVIEW_PENDING",
  "APPROVED",
  "PUBLISHED",
  "REJECTED",
  "SUPERSEDED",
];

// ---- collector axis (app.models.evidence.CollectorType)
export const COLLECTOR_TYPES = [
  { value: "OfficialWebCollector", label: "官方网页（官方来源）", leadOnly: false },
  { value: "OperatorSiteCollector", label: "经营方站点（官方来源）", leadOnly: false },
  { value: "ManualVerificationCollector", label: "人工核实（官方来源）", leadOnly: false },
  { value: "OnsiteEvidenceCollector", label: "现场取证（官方来源）", leadOnly: false },
  { value: "SearchDiscoveryCollector", label: "搜索发现（仅线索）", leadOnly: true },
  { value: "SocialLeadCollector", label: "社交平台（仅线索）", leadOnly: true },
  { value: "UserLinkCollector", label: "用户提交链接（仅线索）", leadOnly: true },
];

// ---- evidence class (app.models.evidence.EvidenceClass)
export const EVIDENCE_CLASSES = [
  { value: "original", label: "原始证据（独立权重）" },
  { value: "derived", label: "派生证据（必须引用原件）" },
];

// ---- extraction method (app.models.evidence.ExtractionMethod)
export const EXTRACTION_METHODS = [
  "manual",
  "ocr",
  "ai_vision",
  "ai_text",
  "url_monitor",
  "import",
  "phone",
  "onsite_visit",
];

// ---- rule layer (app.models.enums.RuleLayer)
export const RULE_LAYERS = [
  { value: "LEGAL", label: "法律法规" },
  { value: "REGULATORY_GUIDANCE", label: "监管指引" },
  { value: "OPERATOR_POLICY", label: "经营方政策" },
  { value: "TEMPORARY_POLICY", label: "临时政策" },
];

// ---- animal scope (mirrors the API/seed vocabulary)
export const ANIMAL_SCOPES = ["dog", "cat", "pet", "all", "service_dog"];

// ---- rule effects
export const EFFECTS = ["allowed", "prohibited", "conditional", "unknown"];

// ---- coexistence attributes + neutral stances (brief §7: neutral wording)
export const COEXISTENCE_ATTRIBUTES = [
  { value: "off_leash", label: "是否允许放开牵引（脱绳）" },
  { value: "designated_area", label: "是否设有指定活动区" },
  { value: "indoor_access", label: "室内是否可进入" },
  { value: "carrier_required", label: "是否要求装载（笼/包/推车）" },
  { value: "muzzle_required", label: "是否要求嘴套" },
  { value: "size_limit", label: "是否有体型限制" },
  { value: "breed_limit", label: "是否有品种限制" },
  { value: "peak_hours_restriction", label: "高峰时段是否限制" },
  { value: "dining_together", label: "是否可与同桌就餐" },
  { value: "waiting_area", label: "是否设有等候区" },
];

/** Boundary stance vocabulary — must match the branches in
 *  `app.rulespec.v05_boundary.match()`. A stance describes the *user's own*
 *  requirement; it is never a verdict about the venue (brief §7). */
export const COEXISTENCE_STANCES = [
  { value: "accept", label: "可接受" },
  { value: "avoid", label: "希望没有" },
  { value: "require_prohibited", label: "必须禁止（硬性要求）" },
  { value: "prefer", label: "希望提供" },
];

// ---- amenity types (kept as free text with suggestions)
export const AMENITY_TYPES = [
  "water_station",
  "shade",
  "waste_bag",
  "waste_bin",
  "dog_park",
  "tether_point",
  "pet_menu",
  "pet_seat",
];

// ---- entrance types (app.models.v05.entrance_type)
export const ENTRANCE_TYPES = ["GENERAL", "PET_ALLOWED", "PET_PROHIBITED", "SERVICE_DOG_ONLY"];

// ---- place-boundary verdicts (app.services.boundary_matcher.BoundaryVerdict)
export const BOUNDARY_VERDICTS = ["MATCH", "CONFLICT", "UNKNOWN"];

/** Tailwind-free semantic class for a status pill. */
export function statusTone(status: string): string {
  switch (status) {
    case "APPROVED":
    case "PUBLISHED":
    case "current":
      return "ok";
    case "REJECTED":
      return "restricted";
    case "REVIEW_PENDING":
    case "MATCH_PENDING":
    case "PLACE_MATCH_PENDING":
      return "warn";
    default:
      return "unknown";
  }
}

export function verdictTone(verdict: string): string {
  switch (verdict) {
    case "MATCH":
      return "ok";
    case "CONFLICT":
      return "restricted";
    default:
      return "unknown";
  }
}
