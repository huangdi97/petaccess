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
  await page.getByRole("tab", { name: "注册", exact: true }).click();
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

  const oldZonesRequested = page.waitForRequest((request) =>
    request.url().includes(`/api/v1/places/${CAFE_ID}/zones`),
  );
  await page.goto(`/#/contribute/${CAFE_ID}`);
  await oldZonesRequested;
  await page.goto(`/#/contribute/${MALL_ID}`);
  const context = page.locator('[data-ui="contribution-context-place"]');
  await expect(context).toContainText("云栖中心·测试商场", { timeout: 15000 });

  releaseOldZones?.();
  await expect(context).toContainText("云栖中心·测试商场");
  await expect(context).not.toContainText("星河咖啡");
  await expect(page).toHaveURL(new RegExp(`#/contribute/${MALL_ID}$`));
});

test("unresolved place scope blocks fact submission and offers a real retry", async ({
  page,
  request,
}) => {
  const email = `scope-${Date.now()}@example.com`;
  const registered = await request.post("http://127.0.0.1:8010/api/v1/auth/register", {
    data: { display_name: "贡献范围校验", email, password: "passw0rd123" },
  });
  expect(registered.ok(), await registered.text()).toBeTruthy();
  const token = (await registered.json()).access_token as string;
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);

  await page.route(`**/api/v1/places/${MALL_ID}/zones`, (route) =>
    route.fulfill({ status: 503, json: { detail: "unavailable" } }),
  );
  await page.goto(`/#/contribute/${MALL_ID}`);

  const failure = page.getByTestId("contribution-context-error");
  await expect(failure).toContainText("无法确认当前场所及区域");
  await expect(page.getByTestId("entry-rule")).toHaveCount(0);
  await expect(page.getByTestId("entry-reality-observed_presence")).toHaveCount(0);

  await page.unroute(`**/api/v1/places/${MALL_ID}/zones`);
  await failure.getByRole("button", { name: "重试" }).click();
  await expect(page.getByTestId("entry-rule")).toBeVisible();
});

test("scoped Reality contribution selects only a zone owned by the current place", async ({
  page,
  request,
}) => {
  const created = await request.post("http://127.0.0.1:8010/api/v1/auth/register", {
    data: {
      display_name: "区域事实测试",
      email: `zone-flow-${Date.now()}@example.com`,
      password: "passw0rd123",
    },
  });
  expect(created.ok(), await created.text()).toBeTruthy();
  const token = (await created.json()).access_token as string;
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);

  const zonesResponse = await request.get(`http://127.0.0.1:8010/api/v1/places/${MALL_ID}/zones`);
  expect(zonesResponse.ok(), await zonesResponse.text()).toBeTruthy();
  const zones = (await zonesResponse.json()) as { id: string }[];
  expect(zones.length).toBeGreaterThan(0);
  const zoneId = zones[0]!.id;

  await page.goto(`/#/contribute/${MALL_ID}?zone=${zoneId}`);
  await page.getByTestId("entry-reality-observed_presence").click();
  await page.getByTestId("entry-next").click();
  await expect(page.locator("#reality-zone")).toHaveValue(zoneId);

  // A zone that is not in the loaded place dossier can never become
  // an implicit submission target merely because it appears in a URL.
  await page.goto(`/#/contribute/${MALL_ID}?zone=00000000-0000-0000-0000-000000000000`);
  await page.getByTestId("entry-reality-observed_presence").click();
  await page.getByTestId("entry-next").click();
  await expect(page.locator("#reality-zone")).toHaveValue("");
});
