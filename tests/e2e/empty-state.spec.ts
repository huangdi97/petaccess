/**
 * v0.1.0 Empty-First product copy (Phase K) regression spec.
 *
 * The shared E2E database is demo-seeded, so "empty world" surfaces must not
 * be produced by an empty DB — they are forced with API route interception,
 * and the assertions pin the exact required copy strings. The 404 case goes
 * through the real API and asserts the explicit ERROR state block, never a
 * blank document.
 */
import { expect, test } from "@playwright/test";

test("home shows the global empty state when no published places exist", async ({ page }) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto("/");

  const empty = page.getByTestId("home-empty");
  await expect(empty).toBeVisible();
  await expect(empty).toContainText("当前还没有已发布的场所数据");

  // The two first-class exits: the map and the contribution flow.
  const mapLink = page.getByTestId("home-empty-map");
  const contributeLink = page.getByTestId("home-empty-contribute");
  await expect(mapLink).toBeVisible();
  await expect(contributeLink).toBeVisible();
  await expect(mapLink).toHaveAttribute("href", /\/map/);
  await expect(contributeLink).toHaveAttribute("href", /\/contribute/);

  // Empty world is a normal state, not a crash: no ERROR banner anywhere.
  await expect(page.locator('[data-state="ERROR"]')).toHaveCount(0);
});

test("search empty result uses the required copy", async ({ page }) => {
  // Deterministic zero-result page, independent of the demo-seeded DB.
  await page.route(/\/api\/v1\/places\?/, (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("完全不存在的场所 zzzz");
  await page.getByTestId("search-btn").click();

  const empty = page.getByTestId("search-empty");
  await expect(empty).toBeVisible();
  await expect(empty).toContainText("没有找到已收录场所");
});

test("place detail 404 does not crash into a blank page", async ({ page }) => {
  await page.goto("/#/place/00000000-0000-0000-0000-000000000000");
  // Whether the API answers 404 or is unreachable, the view must render the
  // explicit ERROR state block with a retry path — never a blank document.
  await expect(page.locator('[data-state="ERROR"]').first()).toBeVisible();
  await expect(page.getByRole("button", { name: "重试" }).first()).toBeVisible();
});
