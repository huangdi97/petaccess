/**
 * UI Oracle — language-scan.ts
 *
 * Node-side language scan over collected visible text (document.body.innerText).
 * The Playwright spec collects text; this module classifies hits. Output JSON is
 * written to artifacts/blind-ui-recovery/language-scan.json by report.ts.
 */

export interface LanguageHit {
  pageId: string;
  uuid: string[];
  snakeCase: string[];
  allcaps: string[];
  invariants: string[];
  refs: string[];
}

const UUID_RE = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i;
const UUID_PREFIX_RE = /\b[0-9a-f]{8}-(?![0-9a-f]{4}-)/i;
const SNAKE_RE = /\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b/g;
const ALLCAPS_RE = /\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b/g;
const REFS_RE = /\b(?:ADR|RFC|TD)-\d+\b|\bAC-[A-Z0-9-]+\b|\bPR-\d+\b/gi;
/** Known internal invariants that must never appear as raw codes. */
export const INVARIANTS = [
  "NO_RECENT_RECORD",
  "INSUFFICIENT_OBSERVATION",
  "OBSERVED_RECENTLY",
  "MULTI_EVIDENCE_OBSERVED",
  "RULE_REALITY_ALIGNED",
  "POTENTIAL_CONFLICT",
  "REVIEW_REQUIRED",
];

/** Known raw enums from the model that must never be visible. */
export const BANNED_ENUMS = [
  "ordinary_pet",
  "service_dog",
  "pet_area",
  "dining_area",
  "children_area",
  "pending_review",
  "superseded",
  "withdrawn",
  "reality_report",
  "candidate",
  "explicitly_allowed",
  "no_interaction_observed",
  "operator_discretion",
  "temporarily_unavailable",
  "outdoor_holding_cage",
  "pet_waiting_area",
  "ordinary_pet_indoor_dining",
  "animal_on_customer_seat",
  // §17：raw enum 短词（consumer 页禁止英文裸值）。
  "allowed",
  "prohibited",
  "conditional",
  "unknown",
  "verified",
  "disputed",
  "observed",
  "historical",
];

export function scanVisibleText(pageId: string, text: string): LanguageHit {
  const uuid = new Set<string>();
  const m1 = text.match(UUID_RE);
  if (m1) uuid.add(m1[0]!);
  const m2 = text.match(UUID_PREFIX_RE);
  if (m2) uuid.add(m2[0]!);

  const snakeCase = new Set<string>();
  for (const m of text.matchAll(SNAKE_RE)) {
    const tok = m[0]!;
    if (tok.length < 4) continue;
    if (INVARIANTS.includes(tok)) continue;
    snakeCase.add(tok);
  }
  // Explicit enums always flagged regardless of shape.
  for (const e of BANNED_ENUMS) {
    if (text.includes(e)) snakeCase.add(e);
  }

  const allcaps = new Set<string>();
  for (const m of text.matchAll(ALLCAPS_RE)) {
    const tok = m[0]!;
    if (INVARIANTS.includes(tok)) continue;
    // Two-char caps like "AI/OK" are legit; require real snake/underscore or ≥4 chars.
    if (tok.length >= 4 && /[A-Z]/.test(tok)) allcaps.add(tok);
  }

  const invariants = INVARIANTS.filter((i) => text.includes(i));

  const refs = new Set<string>();
  for (const m of text.matchAll(REFS_RE)) refs.add(m[0].toUpperCase());

  return {
    pageId,
    uuid: [...uuid],
    snakeCase: [...snakeCase],
    allcaps: [...allcaps],
    invariants,
    refs: [...refs],
  };
}

export function verdict(hit: LanguageHit): "PASS" | "FAIL" {
  return (
    hit.uuid.length === 0 &&
    hit.snakeCase.length === 0 &&
    hit.invariants.length === 0 &&
    hit.refs.length === 0
    ? "PASS"
    : "FAIL"
  );
}

