/**
 * G17 Playwright E2E: H5 core journey against the real stack
 * (API on :8010, H5 on :5175, seeded demo data).
 */
import { expect, test } from "@playwright/test";

const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76"; // deterministic seed UUID

test("health and home render nearby places", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "附近场所" })).toBeVisible();
  await expect(page.getByText("星河咖啡·测试店").first()).toBeVisible();
  await expect(page.getByText("青岚公园·演示").first()).toBeVisible();
});

test("place detail shows one-sentence answer with zones and provenance", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}`);
  const answer = page.getByTestId("answer");
  await expect(answer).toBeVisible();
  // design #48: actionable answer + obligations + source + last verification
  // anonymous visit → no pet profile yet (explicit, never guessed)
  await expect(answer).toContainText("未选择宠物档案");
  await expect(answer).toContainText("有条件进入");
  await expect(answer).toContainText("需牵引");
  await expect(answer).toContainText("最近核验：");
  // zone breakdown: indoor restricted, outdoor conditional, service dog allowed
  const zones = page.getByTestId("zones");
  await expect(zones).toContainText("室内堂食区");
  await expect(zones).toContainText("限制");
  await expect(zones).toContainText("户外座位区");
  // observations coexist with rules but do not change the answer
  await expect(page.getByText("no_interaction_observed").first()).toBeVisible();
});

test("mode switch re-evaluates: service dog → allowed", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}`);
  await expect(page.getByTestId("answer-status")).toHaveText("有条件进入");
  await page.getByRole("button", { name: "服务犬通行" }).click();
  await expect(page.getByTestId("answer-status")).toHaveText("可以进入");
  await page.getByRole("button", { name: "带宠出行" }).click();
  await expect(page.getByTestId("answer-status")).toHaveText("有条件进入");
});

test("search finds place by fuzzy name", async ({ page }) => {
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河");
  await page.getByTestId("search-btn").click();
  await expect(page.getByText("星河咖啡·测试店")).toBeVisible();
});

test("register → create pet → answer carries pet context → quick confirm", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;

  // register
  await page.goto("/#/onboarding");
  await page.getByRole("button", { name: "注册", exact: true }).click();
  await page.locator("input").nth(0).fill("E2E 用户");
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill("passw0rd123");
  await page.getByRole("button", { name: "注册并开始" }).click();
  await expect(page).toHaveURL(/#\/$/);

  // create pet 豆豆
  await page.goto("/#/pet/new");
  await page.getByTestId("pet-name").fill("豆豆");
  await page.getByTestId("pet-weight").fill("9.5");
  await page.getByTestId("pet-save").click();
  await expect(page).toHaveURL(/#\/$/);

  // place answer references the pet
  await page.goto(`/#/place/${CAFE_ID}`);
  await expect(page.getByTestId("answer")).toContainText("对于：豆豆");

  // quick confirm requires auth → succeeds and records
  await page.getByRole("button", { name: "仍有效" }).first().click();
  await expect(page.getByTestId("quick-msg")).toContainText("已记录");
});
