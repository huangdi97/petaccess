import { expect, test } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

async function injectExpiredSession(page: import("@playwright/test").Page) {
  await page.addInitScript(() => localStorage.setItem("pa_token", "expired-e2e-token"));
}

test("Reality remains public while expired private session hides confirmation writes", async ({
  page,
}) => {
  await injectExpiredSession(page);
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality`);

  await expect(page.getByTestId("reality-workspace")).toBeVisible();
  await expect(page.getByTestId("reality-private-session-note")).toContainText("登录状态已失效", {
    timeout: 15000,
  });
  await expect(page.getByTestId("trace-observations")).toBeVisible();
  await expect(page.getByRole("button", { name: "我现在也看到了" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "设施还在" })).toHaveCount(0);
});

test("Evidence remains public while expired private session offers sign-in, not dispute write", async ({
  page,
}) => {
  await injectExpiredSession(page);
  await page.goto(`${BASE}/#/place/${MALL_ID}/evidence`);

  await expect(page.getByTestId("evidence-workspace")).toBeVisible();
  await expect(page.getByTestId("evidence-private-context-note")).toContainText("登录状态已失效", {
    timeout: 15000,
  });
  await expect(page.getByTestId("evidence-head")).toBeVisible();
  await expect(page.getByTestId("reality-dispute-open")).toHaveCount(0);
  const signIn = page.getByTestId("reality-dispute-sign-in").first();
  await expect(signIn).toBeVisible();
  await expect(signIn).toContainText("登录后提出异议");
});
