/**
 * M3 consumer route/query foundation (goal A1/A3, B1/B2) + E2 error hygiene.
 *
 * Runs against the same self-contained E2E stack as the other suites:
 * petaccess_e2e is rebuilt and seeded (星河咖啡·测试店 …), the API serves
 * :8010, the built H5 preview serves :5175. Hash history throughout.
 */
import { expect, test } from "@playwright/test";

const HOME = "http://127.0.0.1:5175/";
const BASE = "http://127.0.0.1:5175";

test("A1 — unknown paths render the unified 404 state, never a blank page", async ({ page }) => {
  await page.goto(`${BASE}/#/definitely-not-a-page`);
  await expect(page.getByTestId("not-found")).toBeVisible();
  await expect(
    page.getByTestId("not-found").getByRole("heading", { name: "页面不存在" }),
  ).toBeVisible();
  // The product shell survives the 404 (rail/tabbar is still reachable).
  await expect(page.getByTestId("consumer-app-shell")).toBeVisible();
  await expect(
    page.getByText("你访问的页面不存在或已被移动。返回首页继续查找场所。"),
  ).toBeVisible();
});

test("A3 — every core route sets a document title", async ({ page }) => {
  await page.goto(HOME);
  await expect(page).toHaveTitle("首页 · PetAccess");
  await page.goto(`${BASE}/#/search`);
  await expect(page).toHaveTitle("搜索场所 · PetAccess");
  await page.goto(`${BASE}/#/definitely-not-a-page`);
  await expect(page).toHaveTitle("页面不存在 · PetAccess");
});

test("B1 — deep link ?q= 回填输入框并自动查询；?lens= 切换视角", async ({ page }) => {
  await page.goto(`${BASE}/#/search?q=咖啡`);
  await expect(page.getByTestId("search-input")).toHaveValue("咖啡");
  await expect(page.locator('[data-testid^="result-"]').first()).toBeVisible();

  await page.goto(`${BASE}/#/search?lens=presence`);
  await expect(page.getByTestId("lens-hint")).toContainText("现场是否有动物出现");
});

test("B2 — 页面内搜索后 back/forward 恢复对应 query 与结果", async ({ page }) => {
  await page.goto(`${BASE}/#/search`);
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await expect(page).toHaveURL(/q=%E5%92%96%E5%95%A1/);
  await expect(page.locator('[data-testid^="result-"]').first()).toBeVisible();

  await page.goBack();
  await expect(page).not.toHaveURL(/q=/);
  await expect(page.getByTestId("search-input")).toHaveValue("");

  await page.goForward();
  await expect(page).toHaveURL(/q=%E5%92%96%E5%95%A1/);
  await expect(page.getByTestId("search-input")).toHaveValue("咖啡");
  await expect(page.locator('[data-testid^="result-"]').first()).toBeVisible();
});

test("E2 — service failure renders unified presentation, never backend internals", async ({
  page,
}) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({
        error: {
          message: "Internal Server Error: psycopg2.OperationalError at SQLAlchemy query",
        },
      }),
    }),
  );
  await page.goto(HOME);
  await expect(page.locator('[data-state="ERROR"], .state-message').first()).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const needle of [
    "SQLAlchemy",
    "FastAPI",
    "Tauri",
    "Rust",
    "psycopg2",
    "Internal Server Error",
    "OperationalError",
  ]) {
    expect(text, `page must not leak ${needle}`).not.toContain(needle);
  }
});
