/**
 * Place dossier route-race regression.
 *
 * A slow response for a previous place must never overwrite the currently
 * selected place's identity, Rule, Reality, or Evidence. We exercise hash
 * navigation in the SAME SPA document; two page.goto calls would reboot Vue
 * and conceal this race.
 */
import { expect, test } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test("late previous-place response never contaminates the current dossier", async ({ page }) => {
  await page.route(`**/api/v1/places/${CAFE_ID}`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 900));
    await route.continue();
  });

  await page.goto(`${BASE}/#/place/${CAFE_ID}`);
  await page.evaluate((id) => {
    window.location.hash = `#/place/${id}`;
  }, MALL_ID);

  const dossier = page.getByTestId("place-workspace");
  await expect(dossier).toHaveAttribute("data-ui-entity-id", MALL_ID);
  await expect(dossier).toContainText("云栖中心", { timeout: 15000 });

  // Wait until the original endpoint has had time to resolve. No old name
  // should leak into any visible part of the new Place workspace.
  await page.waitForTimeout(1100);
  await expect(dossier).toHaveAttribute("data-ui-entity-id", MALL_ID);
  await expect(dossier).toContainText("云栖中心");
  await expect(dossier).not.toContainText("星河咖啡");
});

test("operator claim cannot inherit the previous place's owner and zone context", async ({
  page,
}) => {
  await page.route(`**/api/v1/places/${CAFE_ID}`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 900));
    await route.continue();
  });

  await page.goto(`${BASE}/#/place/${CAFE_ID}/operator-claim`);
  await page.evaluate((id) => {
    window.location.hash = `#/place/${id}/operator-claim`;
  }, MALL_ID);

  const claim = page.getByTestId("operator-claim-page");
  await expect(claim).toContainText("云栖中心", { timeout: 15000 });
  await page.waitForTimeout(1100);
  await expect(claim).toContainText("云栖中心");
  await expect(claim).not.toContainText("星河咖啡");
});
