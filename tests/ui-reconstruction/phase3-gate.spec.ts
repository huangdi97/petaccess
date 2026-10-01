/**
 * UI Reconstruction phase-3 structural gate — objective assertions on the
 * FROZEN Reality / Evidence / Contribution archetypes (freeze §9):
 *
 *   - Reality = Temporal Event Log: `.trace-row` rows on a timeline, no
 *     `.panel` wrapper around each event.
 *   - Evidence = Evidence Record + Provenance: provenance chain + items +
 *     permanent disclaimer render on /place/:id/evidence.
 *   - Contribution = Transaction Flow: first question 你刚刚知道了什么？ with
 *     the five consumer-language options.
 *   - Query Context primitive where expected (place-scoped pages).
 *
 * Reality/evidence are checked with deterministic route stubs so they are not
 * hostage to the E2E seed's observations freshness.
 */
import { expect, test, type APIRequestContext } from "@playwright/test";

const API = `http://127.0.0.1:${process.env.API_PORT ?? "8010"}/api/v1`;
/** 云栖中心·测试商场 — seeded place with rules, sources and reality. */
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

const MOCK_OBSERVATIONS = {
  items: [
    {
      id: "gate-obs-1",
      occurred_at: "2026-09-20T10:30:00",
      animal_scope: "犬",
      observed_action: "在场",
      staff_action: "no_interaction_observed",
      place_confidence: "confirmed_on_site",
      note: "凭证记录",
      dispute_status: "NONE",
    },
  ],
  total: 1,
};
const MOCK_TRACE = {
  place_id: MALL_ID,
  summary: "近期现场有动物出现",
  fact_sections: [{ label: "现场摘要", value: "有一条现场记录", note: null }],
  review_sections: [{ label: "核验", value: "已核验" }],
  evidence_count: 1,
};
const MOCK_SOURCES = {
  items: [
    {
      id: "gate-src-1",
      issuer: "云栖管理方（演示）",
      source_type: "official_operator_policy",
      issuer_verification: "verified",
      collected_at: "2026-09-01",
    },
  ],
  total: 1,
};

async function signIn(request: APIRequestContext): Promise<string> {
  const email = `gate3-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Phase3 测试用户", email, password: "passw0rd123" },
  });
  expect(reg.ok(), `register failed: ${await reg.text()}`).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

test("reality is a timeline of .trace-row rows with no .panel per event", async ({ page }) => {
  await page.route("**/api/v1/places/*/observations", (route) =>
    route.fulfill({
      json: { items: MOCK_OBSERVATIONS.items, total: 1, offset: 0, limit: 20 },
    }),
  );
  await page.goto(`/#/place/${MALL_ID}/reality`);
  const section = page.getByTestId("trace-observations");
  await expect(section).toBeVisible();
  const rows = section.locator(".trace-row");
  await expect(rows.first()).toBeVisible();
  // Divider rows on a timeline — never a card surface around each event.
  await expect(section.locator(".panel")).toHaveCount(0);
  await expect(rows.first().locator(".panel")).toHaveCount(0);
  // Query context primitive is present on the place-scoped page.
  await expect(page.getByTestId("query-context")).toBeVisible();
});

test("evidence route renders provenance, items and the permanent disclaimer", async ({ page }) => {
  await page.route("**/api/v1/places/*/observations", (route) =>
    route.fulfill({ json: { items: MOCK_OBSERVATIONS.items, total: 1, offset: 0, limit: 20 } }),
  );
  await page.route("**/api/v1/places/*/reality/trace", (route) =>
    route.fulfill({ json: MOCK_TRACE }),
  );
  await page.route("**/api/v1/sources", (route) =>
    route.fulfill({ json: { items: MOCK_SOURCES.items, total: 1, offset: 0, limit: 20 } }),
  );
  await page.goto(`/#/place/${MALL_ID}/evidence`);
  await expect(page.getByTestId("evidence-provenance")).toBeVisible();
  await expect(page.getByTestId("evidence-items")).toBeVisible();
  await expect(page.getByTestId("evidence-sources")).toBeVisible();
  await expect(page.getByTestId("evidence-disclaimer")).toContainText(
    "现场事实不代表正式准入规则。",
  );
  // Provenance chain has exactly the five frozen steps (§39 rail layout).
  await expect(page.getByTestId("evidence-provenance").locator(".provenance-step")).toHaveCount(5);
  await expect(page.getByTestId("query-context")).toBeVisible();
});

test("contribution first screen asks 你刚刚知道了什么？ with the five consumer options", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  // Deterministic token injection: a single full-page goto boots straight into
  // ContributeView (the goto→reload pattern raced SPA boot under parallel
  // workers and intermittently landed on Home; same fix as contribute-wizard).
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-reality-observed_presence")).toBeVisible({ timeout: 15000 });
  // §41 makes the page h1 carry the same question (visually-hidden) as the
  // visible entry h2 — getByText is intentionally ambiguous, so take first.
  await expect(page.getByText("你刚刚知道了什么？").first()).toBeVisible();
  for (const label of [
    "我看到了新的规则",
    "我在现场看到动物",
    "工作人员进行了处理",
    "我发现了相关设施",
    "场所信息有误",
  ]) {
    await expect(page.getByRole("button", { name: label })).toBeVisible();
  }
  await expect(page.getByTestId("query-context")).toBeVisible();
});

test("contribution without a place hides the query context and shows the place gate", async ({
  page,
}) => {
  await page.goto("/#/contribute");
  await expect(page.getByTestId("contribute-needs-place")).toBeVisible();
  await expect(page.getByTestId("contribute-go-search")).toBeVisible();
  await expect(page.getByTestId("query-context")).toHaveCount(0);
});
