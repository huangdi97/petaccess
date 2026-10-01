/**
 * M5 Reality Trace + Evidence acceptance (A1–A4, B1/B2).
 *
 * Runs on the self-contained E2E stack. The deterministic seed provides
 * 云栖中心·测试商场 (rules + reality data) and 星河咖啡·栖霞分店 (0 rules).
 * The e2e viewport (1280x720) is desktop.
 */
import { expect, test } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
/** 云栖中心·测试商场 — the richest seeded place (rules, sources, reality). */
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test("A1 — 概览现场 CTA 进入现场 view；直接深链可访问", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}`);
  await expect(page.getByTestId("overview-reality")).toBeVisible();
  await page.getByTestId("overview-reality-link").click();
  await expect(page.getByTestId("place-reality-view")).toBeVisible();

  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);
  await expect(page.getByTestId("trace-summary")).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`/#/place/${MALL_ID}/reality`));
});

test("A2/B2 — v0.2.4：timeline 首屏 + 一行 metadata，无原始枚举", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);
  await expect(page.getByTestId("trace-summary")).toBeVisible();
  // §34：summary 收为一行 metadata；timeline 紧随其后进入首屏。
  await expect(page.getByTestId("reality-summary")).toBeVisible();
  const firstEvent = page.locator("[data-testid='trace-observations'] .trace-row").first();
  await expect(firstEvent).toBeVisible();
  const top = await firstEvent.evaluate((el) => el.getBoundingClientRect().top);
  // §51 gate：first event top <= 360px（不用 scrollTo 证明 timeline 存在）。
  expect(top).toBeLessThanOrEqual(360);
  // 无 raw enum / 无内部字段名。
  const text = await page.evaluate(() => document.body.innerText);
  for (const raw of [
    "dispute_status",
    "reality_verification_state",
    "OBSERVED_RECENTLY",
    "INSUFFICIENT_OBSERVATION",
  ]) {
    expect(text, `raw enum ${raw} must not reach reality page`).not.toContain(raw);
  }
});

test("A3 — 观察时间线渲染；空时间线走 REALITY empty copy", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);
  await expect(page.getByTestId("trace-observations")).toBeVisible();
  // Timeline rows exist for the seeded reality data (≥1 row) OR the empty
  // block renders — the section must never be blank.
  const rows = page.locator('[data-testid="trace-observations"] .trace-row');
  const empty = page.getByTestId("trace-empty");
  await expect(rows.first().or(empty).first()).toBeVisible();

  // Forced-empty observations → the shared REALITY empty copy.
  await page.route("**/api/v1/places/*/observations**", (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);
  await expect(page.getByTestId("trace-empty")).toBeVisible();
  await expect(page.getByTestId("trace-empty")).toContainText("暂无近期现场记录");
});

test("A4 — 深链标题正确；错误统一呈现且不泄漏内部字样", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);
  await expect(page).toHaveTitle("现场轨迹 · PetAccess");

  await page.route("**/api/v1/places/*/reality/trace**", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: { message: "Internal Server Error: psycopg2 at SQLAlchemy" } }),
    }),
  );
  // Reload (goto to the identical hash URL is a no-op), so the intercepted 500 fires.
  await page.reload();
  await expect(page.getByText("未能取得现场轨迹")).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const needle of ["SQLAlchemy", "FastAPI", "psycopg2", "Internal Server Error"]) {
    expect(text, `trace must not leak ${needle}`).not.toContain(needle);
  }
});

test("B1 — 无原始证据枚举上屏", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);
  await expect(page.getByTestId("trace-summary")).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const raw of [
    "VERIFIED",
    "PENDING",
    "DISPUTED",
    "HISTORICAL",
    "dispute_status",
    "reality_verification_state",
  ]) {
    expect(text, `raw enum ${raw} must not reach the trace page`).not.toContain(raw);
  }
});
