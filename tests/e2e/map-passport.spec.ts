/**
 * M4 Map + Place Passport acceptance (A1/A2/A4, B1/B2/B3/B5).
 *
 * Runs on the self-contained E2E stack (petaccess_e2e seeded with the
 * deterministic fixtures — 星河咖啡·测试店 family, CAFE_ID has published rules).
 * The e2e default viewport (1280x720) is desktop, so the map renders in
 * split-view and the PlacePreview pane is present.
 */
import { expect, test } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
/** Deterministic seed UUID with published rules (h5-journey.spec.ts). */
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76";
/** Ready fixture (place-ready-v1) — unknown places render the §15 Unknown Overview. */
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test("A4 — /#/map?place= 深链预选；页面选择后 back/forward 同步", async ({ page }) => {
  // Entry 1: deep link opens the desktop pane with the right place.
  await page.goto(`${BASE}/#/map?place=${CAFE_ID}`);
  await expect(page.getByTestId("place-preview")).toBeVisible();
  await expect(page.getByTestId("preview-open")).toHaveAttribute("href", `#/place/${CAFE_ID}`);

  // Entry 2: an unknown place id leaves the pane in its empty hint state.
  await page.goto(`${BASE}/#/map?place=00000000-0000-0000-0000-000000000000`);
  await expect(page.getByTestId("preview-empty")).toBeVisible();

  // Back restores the deep-linked selection; forward re-applies the empty one.
  await page.goBack();
  await expect(page.getByTestId("preview-open")).toHaveAttribute("href", `#/place/${CAFE_ID}`);
  await page.goForward();
  await expect(page.getByTestId("preview-empty")).toBeVisible();
});

test("A1 — desktop 地图 split-view + 四 Lens + 详情面板", async ({ page }) => {
  await page.goto(`${BASE}/#/map`);
  await expect(page.getByTestId("map")).toBeVisible();
  for (const lens of ["rule", "reality", "facility", "divergence"]) {
    await expect(page.getByTestId(`map-lens-${lens}`)).toBeVisible();
  }
  // Desktop auto-selects the first hit so the pane is populated, not empty.
  await expect(page.getByTestId("place-preview")).toBeVisible();
  await expect(page.getByTestId("preview-open")).toBeVisible();
});

test("A2 — map 错误统一呈现，不泄漏内部字样", async ({ page }) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: { message: "Internal Server Error: psycopg2 at SQLAlchemy" } }),
    }),
  );
  await page.goto(`${BASE}/#/map`);
  await expect(page.locator('[data-state="ERROR"]').first()).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const needle of ["SQLAlchemy", "FastAPI", "psycopg2", "Internal Server Error"]) {
    expect(text, `map must not leak ${needle}`).not.toContain(needle);
  }
});

test("A2 — map 空态使用统一文案（地图暂无已发布场所 + 返回首页）", async ({ page }) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto(`${BASE}/#/map`);
  await expect(page.getByTestId("map-empty")).toBeVisible();
  await expect(page.getByTestId("map-empty")).toContainText("地图暂无已发布场所");
  await expect(
    page.getByTestId("map-empty").getByRole("button", { name: "返回首页" }),
  ).toBeVisible();
});

test("B1/B2 — Place Dossier 概览 + 规则/现场 view 关键段齐备", async ({ page }) => {
  // §15: unknown places (cafe) show the minimal Unknown Overview, so the
  // dossier overview blocks are asserted on the ready mall fixture; the cafe
  // still serves the rules/reality views (they render regardless of state).
  await page.goto(`${BASE}/#/place/${MALL_ID}`);
  // Rule dimension: answer section with verdict + overview evidence summary.
  await expect(page.getByTestId("section-answer")).toBeVisible();
  await expect(page.getByTestId("overview-evidence")).toBeVisible();
  // Reality dimension visible on the overview too (recent reality block).
  await expect(page.getByTestId("overview-reality")).toBeVisible();
  // Rules view carries the source rows.
  await page.goto(`${BASE}/#/place/${MALL_ID}?view=rules`);
  await expect(page.getByTestId("place-rules-view")).toBeVisible();
  await expect(page.getByTestId("rule-source").first()).toBeVisible();
  // Reality view hosts the shared published v0.9 event log.
  await page.goto(`${BASE}/#/place/${MALL_ID}?view=reality`);
  await expect(page.getByTestId("place-reality-view")).toBeVisible();
  await expect(
    page.getByTestId("place-reality-view").locator("[data-ui='reality-event-log']"),
  ).toBeVisible();
});

test("B3 — Place Evidence view 证据来源链渲染，无原始枚举", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${CAFE_ID}?view=evidence`);
  await expect(page.getByTestId("place-evidence-view")).toBeVisible();
  await expect(page.getByTestId("evidence-provenance")).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const raw of ["VERIFIED", "PENDING", "DISPUTED", "HISTORICAL"]) {
    expect(text, `raw evidence enum ${raw} must not reach the page`).not.toContain(raw);
  }
});

test("B5 — Search DecisionInspector 查看完整场所 → Place Passport", async ({ page }) => {
  // Search the ready mall fixture: the cafe deep-link lands on the §15 Unknown
  // Overview, which has no dossier answer block.
  await page.goto(`${BASE}/#/search?q=云栖`);
  await expect(page.getByTestId("decision-inspector")).toBeVisible();
  await page.getByTestId("inspector-open").click();
  await expect(page.getByTestId("section-answer")).toBeVisible();
});
