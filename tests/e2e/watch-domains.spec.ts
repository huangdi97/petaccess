import { expect, test, type APIRequestContext } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const API = "http://127.0.0.1:8010/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

async function signIn(request: APIRequestContext): Promise<string> {
  const email = `watch-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const registered = await request.post(`${API}/auth/register`, {
    data: { display_name: "关注测试用户", email, password: "passw0rd123" },
  });
  expect(registered.ok(), await registered.text()).toBeTruthy();
  return (await registered.json()).access_token as string;
}

test("Place keeps Rule Watch and Reality Watch independent", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);

  await page.goto(`${BASE}/#/place/${MALL_ID}`);
  await expect(page.getByTestId("watch-rule")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("watch-reality")).toBeVisible();

  await page.getByTestId("watch-rule").click();
  await expect(page.getByTestId("watch-rule")).toContainText("规则变化已关注");
  await expect(page.getByTestId("watch-reality")).toContainText("关注现场更新");

  await page.getByTestId("watch-reality").click();
  await expect(page.getByTestId("watch-reality")).toContainText("现场更新已关注");

  await page.goto(`${BASE}/#/notifications`);
  await expect(page.getByTestId("notifications-page")).toBeVisible();
  await expect(page.locator(".notification-row")).toHaveCount(2);
  await expect(page.locator(".notification-row").filter({ hasText: "规则变化" })).toHaveCount(1);
  await expect(page.locator(".notification-row").filter({ hasText: "现场更新" })).toHaveCount(1);
});

test("cancelled watch stays absent after notification-page reload", async ({ page, request }) => {
  const token = await signIn(request);
  const headers = { Authorization: `Bearer ${token}` };
  const created = await request.post(`${API}/watches`, {
    headers,
    data: {
      watch_domain: "reality",
      target_type: "place",
      target_id: MALL_ID,
      channels: ["in_app"],
    },
  });
  expect(created.ok(), await created.text()).toBeTruthy();

  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
  await page.goto(`${BASE}/#/notifications`);
  const row = page.locator(".notification-row").filter({ hasText: "现场更新" });
  await expect(row).toBeVisible({ timeout: 15000 });
  await row.getByRole("button", { name: "取消关注" }).click();
  await expect(row).toHaveCount(0);

  await page.reload();
  await expect(page.locator(".notification-row").filter({ hasText: "现场更新" })).toHaveCount(0);
});

test("failed unwatch retains the server subscription and allows retry", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  const headers = { Authorization: `Bearer ${token}` };
  const created = await request.post(`${API}/watches`, {
    headers,
    data: {
      watch_domain: "rule",
      target_type: "place",
      target_id: MALL_ID,
      channels: ["in_app"],
    },
  });
  expect(created.ok(), await created.text()).toBeTruthy();

  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
  await page.route("**/api/v1/watches/*", async (route) => {
    if (route.request().method() === "DELETE") {
      await route.fulfill({ status: 503, json: { detail: "unavailable" } });
    } else {
      await route.continue();
    }
  });
  await page.goto(`${BASE}/#/notifications`);
  const row = page.locator(".notification-row").filter({ hasText: "规则变化" });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: /取消关注/ }).click();
  await expect(row).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("取消关注失败");
  await expect(row.getByRole("button", { name: /取消关注/ })).toBeEnabled();
});
