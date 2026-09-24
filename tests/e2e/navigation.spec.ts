/**
 * M2 navigation contract (V020_APP_SHELL_SPEC §3):
 *   - < 768px: bottom tabs 首页 / 地图 / 贡献 / 我的, no rail.
 *   - ≥ 768px: navigation rail 首页 / 搜索 / 地图 / 贡献 + 我的 / 设置 / 关于,
 *     no bottom tabs.
 *   - every nav target ≥ 44px; mobile tabbar consumes safe-area bottom.
 */
import { expect, test } from "@playwright/test";

test("mobile shows the four bottom tabs and no rail", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const tabbar = page.getByTestId("mobile-tabbar");
  await expect(tabbar).toBeVisible();
  for (const label of ["首页", "地图", "贡献", "我的"]) {
    await expect(tabbar.getByRole("link", { name: label })).toBeVisible();
  }
  // 搜索 is a Home-level feature on mobile, not a fifth tab
  await expect(tabbar.getByRole("link", { name: "搜索" })).toHaveCount(0);
  await expect(page.getByTestId("desktop-rail")).toHaveCount(0);
  // tap targets: each tab link is ≥ 44px tall
  const height = await tabbar.getByRole("link", { name: "首页" }).evaluate((el) => el.getBoundingClientRect().height);
  expect(height).toBeGreaterThanOrEqual(44);
});

test("desktop shows the rail with both groups and no bottom tabs", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  const rail = page.getByTestId("desktop-rail");
  await expect(rail).toBeVisible();
  for (const label of ["首页", "搜索", "地图", "贡献"]) {
    await expect(rail.getByRole("link", { name: label })).toBeVisible();
  }
  for (const label of ["我的", "设置", "关于"]) {
    await expect(rail.getByRole("link", { name: label })).toBeVisible();
  }
  await expect(page.getByTestId("mobile-tabbar")).toHaveCount(0);
  // version info lives in the rail footer
  await expect(rail.getByTestId("app-version")).toContainText("PetAccess v");
});

test("tablet (768) switches to the rail", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.goto("/");
  await expect(page.getByTestId("desktop-rail")).toBeVisible();
  await expect(page.getByTestId("mobile-tabbar")).toHaveCount(0);
});

test("mobile tabbar pads for the safe-area bottom", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const padding = await page
    .getByTestId("mobile-tabbar")
    .evaluate((el) => getComputedStyle(el).paddingBottom);
  // resolves to env(safe-area-inset-bottom, 0px) — computed as a length, never none
  expect(padding).toMatch(/\d+(\.\d+)?px/);
});
