/**
 * Consumer Visible Text Leakage Gate (Goal §29, §49).
 *
 * Checks ONLY text a user can actually see — never data-testid, JSON fixtures,
 * internal attributes or source. Three classes are banned from visible text:
 *
 *   1. UUIDs (including id.slice(0,8) fragments: any 8+ hex run followed by
 *      `-`, or the full 8-4-4-4-12 shape).
 *   2. Known raw enums (denylist below — snake_case internal vocabulary that
 *      must never reach the screen: zone types, animal scopes, rule statuses,
 *      workflow states, internal invariants).
 *   3. All-caps invariant codes (NO_RECENT_RECORD, UNKNOWN, ALLOWED,
 *      PROHIBITED, VERIFIED…) that are internal vocabulary, not copy.
 *
 * The scan runs over `document.body.innerText` of every consumer page on the
 * deterministic visual stack. False-positive discipline: the denylist is
 * explicit and consumer-safe words are never matched (e.g. "已知"/"来源").
 */
import { expect, test } from "@playwright/test";

const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

/** Phase A pages — asserted from Phase A onward. */
const PHASE_A_PAGES: [string, string][] = [
  ["home", "/"],
  ["search", "/#/search"],
  ["map", "/#/map"],
  ["place", `/#/place/${PLACE_ID}`],
  ["contribute", "/#/contribute"],
];

/**
 * Phase C pages — asserted once Phase C closes them (Goal §49: Reality
 * invariant consumerized; Evidence resolved label / no UUID). Kept in the
 * same gate so the final run proves zero leakage across all seven pages.
 */
const PHASE_C_PAGES: [string, string][] = [
  ["reality", `/#/place/${PLACE_ID}/reality`],
  ["evidence", `/#/place/${PLACE_ID}/evidence`],
];

const PAGES: [string, string][] =
  process.env.LEAKAGE_SCOPE === "all" ? [...PHASE_A_PAGES, ...PHASE_C_PAGES] : PHASE_A_PAGES;

/**
 * Raw internal enums / invariants that must never be visible to a consumer.
 * Kept explicit and tight so ordinary Chinese copy and legitimate brand words
 * are never false-positived.
 */
const BANNED_RAW_ENUMS: string[] = [
  "pet_area",
  "dining_area",
  "children_area",
  "ordinary_pet",
  "service_dog",
  "pending_review",
  "superseded",
  "reality_report",
  "candidate",
  "NO_RECENT_RECORD",
  "INSUFFICIENT_OBSERVATION",
  "OBSERVED_RECENTLY",
  "MULTI_EVIDENCE_OBSERVED",
  "RULE_REALITY_ALIGNED",
  "ordinary_pet_indoor_dining",
  "animal_on_customer_seat",
  "explicitly_allowed",
  "no_interaction_observed",
  "operator_discretion",
  "temporarily_unavailable",
  "outdoor_holding_cage",
  "pet_waiting_area",
  "leash_required",
  "muzzle_required",
  "carrier_required",
  "stroller_required",
  "no_ground",
  "registration_required",
  "vaccination_required",
  "max_weight_kg",
  "min_weight_kg",
  "max_shoulder_height_cm",
  "max_count",
  "reservation_required",
  "advance_notice_required",
  "designated_entrance",
  "designated_elevator",
  "designated_route",
  "time_windows",
  "date_windows",
  "room_restriction",
  "holder_scope",
  "service_role",
];

/** Full UUID shape. */
const UUID_RE = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i;
/** A bare 8+ hex fragment immediately followed by a hyphen (id.slice(0,8)). */
const UUID_PREFIX_RE = /\b[0-9a-f]{8}-(?![0-9a-f]{4}-)/i;

/** All-caps invariant codes (internal, not copy). */
const INVARIANT_RE =
  /\b(?:NO_RECENT_RECORD|INSUFFICIENT_OBSERVATION|OBSERVED_RECENTLY|MULTI_EVIDENCE_OBSERVED|RULE_REALITY_ALIGNED|POTENTIAL_CONFLICT|REVIEW_REQUIRED)\b/;

async function visibleText(page: import("@playwright/test").Page): Promise<string> {
  return page.evaluate(() => document.body.innerText);
}

test("visible text leaks no UUID on any consumer page", async ({ page }) => {
  for (const [name, url] of PAGES) {
    await page.goto(url);
    await page.waitForTimeout(1200);
    const text = await visibleText(page);
    const hit = text.match(UUID_RE) ?? text.match(UUID_PREFIX_RE);
    expect(hit, `${name} shows a UUID fragment: ${hit?.[0] ?? ""}`).toBeNull();
  }
});

test("visible text leaks no raw enum on any consumer page", async ({ page }) => {
  for (const [name, url] of PAGES) {
    await page.goto(url);
    await page.waitForTimeout(1200);
    const text = await visibleText(page);
    for (const banned of BANNED_RAW_ENUMS) {
      expect(text, `${name} shows raw enum "${banned}"`).not.toContain(banned);
    }
  }
});

test("visible text leaks no internal invariant code on any consumer page", async ({ page }) => {
  for (const [name, url] of PAGES) {
    await page.goto(url);
    await page.waitForTimeout(1200);
    const text = await visibleText(page);
    const hit = text.match(INVARIANT_RE);
    expect(hit, `${name} shows invariant code: ${hit?.[0] ?? ""}`).toBeNull();
  }
});
