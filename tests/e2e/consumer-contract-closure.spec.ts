/**
 * M3.1 Consumer Contract corrective closure (UI_RECONSTRUCTION_GOAL §8).
 *
 * Contract gates covered here:
 *   - TRANSPORT_ERROR_CACHE (§8.2): a failed snapshot is never stored as a
 *     cached "fact". First request 500 → second request after recovery must
 *     re-request and succeed; the failure value must not be served as a
 *     cache hit inside TTL.
 *   - SNAPSHOT_CACHE_KEY (§8.3): the snapshot key carries the full query
 *     context. A service-dog query never hits the ordinary-dog snapshot:
 *     the key function is tested as a pure function (Node, no page) and the
 *     session mapping is covered directly.
 *   - LENS_SEMANTICS (§8.5): ?lens= presence / rules / indoor / dining really
 *     changes the Consumer projection (Reality-first vs Rule-first headline,
 *     zone facts surfaced), never the domain facts themselves.
 */
import { expect, test } from "@playwright/test";
import { currentQueryContext, snapshotKey } from "../../apps/client-h5/src/consumer/repository";
import { lensOrderScore } from "../../apps/client-h5/src/consumer/rowView";
import { session } from "../../packages/client-core/src/index";

const PLACE = {
  id: "00000000-0000-0000-0000-000000000002",
  canonical_name: "契约测试场所",
  place_type: "cafe",
  rule_count: 2,
};

const SNAPSHOT_OK = {
  place_id: PLACE.id,
  generated_at: "2026-09-27T10:00:00Z",
  version: "test",
  rule_answer: {
    query_context: {},
    normative_result: {
      effect: "allowed",
      compliance_state: "CONSISTENT",
      summary: "允许进入",
      governing_rule_ids: ["r1"],
      governing_layer: ["OPERATOR_POLICY"],
      mandatory_levels: ["mandatory"],
    },
    condition_evaluation: {
      conditions: [],
      unmet: [],
      missing_inputs: [],
      pending_exceptions: [],
    },
    scope_summary: {
      place: { id: PLACE.id, name: PLACE.canonical_name, place_type: "cafe" },
      zone: null,
      zone_requested: false,
      scope_level: "place",
      zone_scoped_rule_count: 0,
      animal_scope_requested: "dog",
      declared_role: null,
    },
    evidence_state: {
      rules: [],
      first_party_operator_source_pending: false,
      first_party_operator_source_count: 0,
      weakest_directness: null,
      acceptance_required: false,
    },
    conflict_state: {
      has_conflict: false,
      compliance_state: "CONSISTENT",
      unresolved_conflicts: [],
      suppressed: [],
    },
    rights_information: {
      normative_effects: [],
      operator_obligations: [],
      facilitation_required: false,
      holder_scopes: [],
    },
    matched_rule_versions: [],
    explanation_items: [],
    next_actions: [],
    evaluated_at: "2026-09-27T10:00:00Z",
    valid_until: null,
    evaluation_version: "test",
  },
  reality_answer: {
    state: "OBSERVED_RECENTLY",
    last_seen_at: "2026-09-25T18:42:00Z",
    evidence_count: 2,
    distinct_source_count: 2,
    observed_zones: ["一层公共区域", "餐饮堂食区"],
    observed_zone_facts: [
      { name: "一层公共区域", zone_type: "floor", indoor_outdoor: "indoor" },
      { name: "餐饮堂食区", zone_type: "dining_area", indoor_outdoor: "indoor" },
    ],
    observed_zone_types: ["dining_area", "floor"],
    observed_indoor_outdoor: ["indoor"],
    observed_actions: ["entered_with_leash"],
    staff_response_summary: [],
    facility_summary: [],
    freshness_state: "FRESH",
    verification_state: "VERIFIED",
    recent_count_7d: 1,
    recent_count_30d: 2,
    days_since_last_seen: 2,
    note: null,
  },
  staff_response_summary: [],
  facility_summary: [],
  divergence: {
    state: "NONE",
    rule_effect: "ALLOWED",
    reality_state: "OBSERVED_RECENTLY",
    note: null,
  },
  evidence_summary: {
    rule_evidence: [],
    rule_first_party_pending: false,
    reality_evidence_count: 2,
    reality_distinct_source_count: 2,
    reality_verification_state: "VERIFIED",
  },
};

function ordinaryCtx() {
  return {
    animal: "dog",
    service_role: "none",
    declared_role: null,
    action: "enter",
    zone_id: null,
  };
}

async function mockList(page: import("@playwright/test").Page, items: (typeof PLACE)[]) {
  await page.route(/\/api\/v1\/places\?/, (route) =>
    route.fulfill({ json: { items, total: items.length, limit: 20, offset: 0 } }),
  );
}

// ------------------------------------------------------------------ C2 ---

test("C2: transport error is never served as a cached fact — recovery re-requests", async ({
  page,
}) => {
  let fail = true;
  await mockList(page, [PLACE]);
  await page.route("**/coexistence", (route) => {
    if (fail) {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: {} }),
      });
    } else {
      route.fulfill({ json: SNAPSHOT_OK });
    }
  });

  // First search: snapshot 500 → row must show the explicit transport error,
  // never an "未核验" verdict or a blank.
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("契约");
  await page.getByTestId("search-btn").click();
  await expect(page.getByTestId(`result-${PLACE.id}`)).toBeVisible();
  await expect(page.locator("[data-testid=`result-${PLACE.id}`]")).toContainText(
    "规则结论暂时无法取得",
  );

  // Network recovers. The same query again must RE-REQUEST (the failed value
  // was never cached), and the row now shows the real ALLOWED badge.
  fail = false;
  await page.getByTestId("search-btn").click();
  await expect(page.locator("[data-testid=`result-${PLACE.id}`]")).toContainText("明确允许");
});

// ------------------------------------------------------------------ C3 ---

test("C3: snapshot key differs when the query context changes (ordinary dog → service dog)", () => {
  const ordinary = snapshotKey("place-1", ordinaryCtx());
  const service = snapshotKey("place-1", { ...ordinaryCtx(), service_role: "working" });
  const otherPlace = snapshotKey("place-2", ordinaryCtx());
  // A service-dog question must never be served the ordinary-dog snapshot.
  expect(service).not.toBe(ordinary);
  // Place is a distinct dimension too.
  expect(otherPlace).not.toBe(ordinary);
  // Changing any context dimension changes the key — the cache slot is the
  // full question, not a place-only slot.
  expect(snapshotKey("place-1", { ...ordinaryCtx(), action: "leave" })).not.toBe(ordinary);
});

test("C3: currentQueryContext maps service-dog mode to service_role=working", () => {
  const prevMode = session.mode;
  try {
    session.mode = "service_dog";
    const ctx = currentQueryContext();
    expect(ctx.service_role).toBe("working");
  } finally {
    session.mode = prevMode;
  }
});

// ------------------------------------------------------------------ C5 ---

test("C5: lens changes consumer projection without changing domain facts", async ({ page }) => {
  await mockList(page, [PLACE]);
  await page.route("**/coexistence", (route) => route.fulfill({ json: SNAPSHOT_OK }));

  await page.goto("/#/search?lens=rules");
  await page.getByTestId("search-input").fill("契约");
  await page.getByTestId("search-btn").click();
  await expect(page.getByTestId(`result-${PLACE.id}`)).toBeVisible();
  // rules lens = Rule-first: the rule conclusion is the row headline.
  const rulesRow = page.getByTestId(`result-${PLACE.id}`);
  await expect(rulesRow.locator("[data-testid=row-lens-headline]")).toContainText("允许进入");

  await page.goto("/#/search?lens=presence");
  await page.getByTestId("search-input").fill("契约");
  await page.getByTestId("search-btn").click();
  await expect(page.getByTestId(`result-${PLACE.id}`)).toBeVisible();
  // presence lens = Reality-first: the reality line is the row headline.
  const presenceRow = page.getByTestId(`result-${PLACE.id}`);
  await expect(presenceRow.locator("[data-testid=row-lens-headline]")).toContainText(
    "近期现场有动物出现",
  );
  await page.goto("/#/search?lens=indoor");
  await page.getByTestId("search-input").fill("契约");
  await page.getByTestId("search-btn").click();
  await expect(page.getByTestId(`result-${PLACE.id}`)).toBeVisible();
  const indoorRow = page.getByTestId(`result-${PLACE.id}`);
  await expect(indoorRow.locator("[data-testid=row-lens-headline]")).toContainText(
    "室内区域有经核验动物出现",
  );
  await expect(indoorRow.locator("[data-testid=row-lens-headline]")).toContainText("一层公共区域");

  await page.goto("/#/search?lens=dining");
  await page.getByTestId("search-input").fill("契约");
  await page.getByTestId("search-btn").click();
  const diningRow = page.getByTestId(`result-${PLACE.id}`);
  await expect(diningRow.locator("[data-testid=row-lens-headline]")).toContainText(
    "餐饮区域有经核验动物出现",
  );
  await expect(diningRow.locator("[data-testid=row-lens-headline]")).toContainText("餐饮堂食区");
  await expect(diningRow.locator("[data-testid=row-lens-headline]")).not.toContainText(
    "一层公共区域",
  );
});

test("C5: indoor/dining ranking requires the matching structured Zone facet", () => {
  const corridorOnly = {
    ...SNAPSHOT_OK.reality_answer,
    observed_zones: ["一层公共区域"],
    observed_zone_facts: [{ name: "一层公共区域", zone_type: "floor", indoor_outdoor: "indoor" }],
    observed_zone_types: ["floor"],
    observed_indoor_outdoor: ["indoor"],
  };
  expect(lensOrderScore("indoor", null, corridorOnly)).toBe(1);
  expect(lensOrderScore("dining", null, corridorOnly)).toBe(0);
});
