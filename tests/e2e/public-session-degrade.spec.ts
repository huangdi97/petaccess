import { expect, test } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test.beforeEach(async ({ page }) => {
  // Simulate a stale/corrupted local credential. Public Rule/Reality surfaces
  // must fail open to anonymous access instead of becoming account outages.
  await page.addInitScript(() => localStorage.setItem("pa_token", "stale.invalid.token"));
});

test("public Place dossier remains readable with a broken local session", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}`);
  await expect(page.locator("[data-ui='place-identity']")).toContainText("云栖中心", {
    timeout: 15000,
  });
  await expect(page.getByTestId("section-answer")).toBeVisible();
  await expect(page.getByText("账号状态暂不可用；公开规则与现场信息仍可查看。")).toBeVisible();
});

test("public Search and Map remain usable with a broken local session", async ({ page }) => {
  await page.goto(`${BASE}/#/search?q=云栖`);
  await expect(page.getByTestId(`result-${MALL_ID}`)).toBeVisible({ timeout: 15000 });

  await page.goto(`${BASE}/#/map?place=${MALL_ID}`);
  await expect(page.getByTestId("map")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("place-preview")).toContainText("云栖中心");
});
