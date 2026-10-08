/**
 * Contribution must not reuse an earlier route's place context.
 *
 * A delayed zones request for A may resolve after the user opens B.
 * No A context can appear on B's form, which submits using the route ID.
 */
import { expect, test } from "@playwright/test";

const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test("late place A response cannot overwrite place B contribution context", async ({ page }) => {
  await page.goto("/#/onboarding");
  await page.getByRole("button", { name: "注册", exact: true }).click();
  await page.locator('input[autocomplete="name"]').fill("场所切换验收");
  await page.locator('input[type="email"]').fill(`place-switch-${Date.now()}@example.com`);
  await page.locator('input[type="password"]').fill("passw0rd123");
  await page.getByRole("button", { name: "注册并开始" }).click();
  await expect(page).toHaveURL(/#\/$/);

  let releaseOldZones: (() => void) | undefined;
  const oldZonesHeld = new Promise<void>((resolve) => {
    releaseOldZones = resolve;
  });
  await page.route(`**/api/v1/places/${CAFE_ID}/zones`, async (route) => {
    await oldZonesHeld;
    await route.continue();
  });

  await page.goto(`/#/contribute/${CAFE_ID}`);
  await page.waitForRequest((request) =>
    request.url().includes(`/api/v1/places/${CAFE_ID}/zones`),
  );
  await page.goto(`/#/contribute/${MALL_ID}`);
  const context = page.locator('[data-ui="contribution-context-place"]');
  await expect(context).toContainText("云栖中心·测试商场", { timeout: 15000 });

  releaseOldZones?.();
  await expect(context).toContainText("云栖中心·测试商场");
  await expect(context).not.toContainText("星河咖啡");
  await expect(page).toHaveURL(new RegExp(`#/contribute/${MALL_ID}$`));
});
