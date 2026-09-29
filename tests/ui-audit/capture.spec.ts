/**
 * M3 UI 取证截图 — 修改前（current）与最终（m3-final）共用同一 spec。
 *
 * 每个 scenario 一个 test；project 名称 = viewport（ui-360/ui-430/ui-800/
 * ui-1280/ui-1440），截图写入 artifacts/ui-audit/{stage}/{viewport}/{scenario}.png。
 *
 * 状态语义（不得伪造 domain）：
 *   - ready    真实 seed 数据的页面
 *   - loading  API 延迟 2s（骨架可见）
 *   - empty    拦截 nearby/search → 空 items（产品空态）
 *   - error    拦截 → 500（统一错误态）
 *   - offline  先加载成功再断网 → GlobalOfflineBanner
 *   - stale    localStorage 预置旧 recent + 时钟冻结（可构造时截取）
 */
import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const STAGE = process.env.UI_AUDIT_STAGE ?? "current";

function outPath(viewport: string, scenario: string): string {
  return path.resolve("artifacts/ui-audit", STAGE, viewport, `${scenario}.png`);
}

async function shot(page: import("@playwright/test").Page, viewport: string, scenario: string) {
  const p = outPath(viewport, scenario);
  mkdirSync(path.dirname(p), { recursive: true });
  await page.screenshot({ path: p, fullPage: true });
}

async function settle(page: import("@playwright/test").Page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 12000,
    })
    .catch(() => {});
  await page.waitForTimeout(300);
}

const JSON_EMPTY_PAGE = { items: [], total: 0, limit: 20, offset: 0 };

// ------------------------------------------------------------------ ready ---

for (const [slug, url, testid] of [
  ["home", "/", "consumer-app-shell"],
  ["search", "/#/search", "search-input"],
] as const) {
  test(`${slug}-ready`, async ({ page }, testInfo) => {
    const viewport = testInfo.project.name;
    await page.goto(url);
    await settle(page);
    await expect(page.getByTestId(testid).first()).toBeVisible();
    await shot(page, viewport, `${slug}-ready`);
  });
}

// ------------------------------------------------------------ state matrix ---

test("home-loading", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places/nearby**", async (route) => {
    await new Promise((r) => setTimeout(r, 2000));
    await route.continue();
  });
  await page.goto("/");
  await page.waitForTimeout(700);
  await shot(page, viewport, "home-loading");
});

test("home-empty", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ json: JSON_EMPTY_PAGE }),
  );
  await page.goto("/");
  await settle(page);
  await expect(page.getByTestId("home-empty")).toBeVisible();
  await shot(page, viewport, "home-empty");
});

test("home-error", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: {} }),
    }),
  );
  await page.goto("/");
  await settle(page);
  await expect(page.locator('[data-state="ERROR"]').first()).toBeVisible();
  await shot(page, viewport, "home-error");
});

test("home-offline", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.goto("/");
  await settle(page);
  await page.context().setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event("offline")));
  await page.waitForTimeout(300);
  await expect(page.getByTestId("global-offline-banner")).toBeVisible();
  await shot(page, viewport, "home-offline");
});

test("search-loading", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places?**", async (route) => {
    await new Promise((r) => setTimeout(r, 2000));
    await route.continue();
  });
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await page.waitForTimeout(700);
  await shot(page, viewport, "search-loading");
});

test("search-empty", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.goto("/#/search");
  await settle(page);
  await page.getByTestId("search-input").fill("不存在的场所zzz");
  await page.getByTestId("search-btn").click();
  await settle(page);
  await expect(page.getByTestId("search-empty")).toContainText("没有找到已收录场所");
  await shot(page, viewport, "search-empty");
});

test("search-error", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places?**", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: {} }),
    }),
  );
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await settle(page);
  await expect(page.locator('[data-state="ERROR"]').first()).toBeVisible();
  await shot(page, viewport, "search-error");
});

test("search-offline", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.goto("/#/search");
  await settle(page);
  await page.context().setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event("offline")));
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await page.waitForTimeout(300);
  await shot(page, viewport, "search-offline");
});

// ------------------------------------------------------------ other pages ---
for (const [slug, url, testid] of [
  ["map", "/#/map", "map"],
  ["place", "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e", "section-answer"],
  ["contribute", "/#/contribute", "contribute-needs-place"],
  ["mine", "/#/mine", "consumer-app-shell"],
] as const) {
  test(`${slug}-ready`, async ({ page }, testInfo) => {
    const viewport = testInfo.project.name;
    await page.goto(url);
    await settle(page);
    await expect(page.getByTestId(testid).first()).toBeVisible();
    await shot(page, viewport, `${slug}-ready`);
  });
}
