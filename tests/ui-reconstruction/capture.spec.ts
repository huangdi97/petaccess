/**
 * UI Reconstruction capture — BEFORE (baseline) and AFTER (final / phase) stages.
 *
 * Mirrors tests/ui-audit/capture.spec.ts but targets the reconstruction artifact
 * tree (artifacts/ui-reconstruction/{stage}/{viewport}/{scenario}.png) and covers
 * all seven consumer pages + key states. Stage is set by UI_RECONSTRUCTION_STAGE:
 *   baseline | phase1 | phase2 | phase3 | final
 *
 * States (never fabricated): ready (real seed), loading (delayed API),
 * empty (mocked empty items), error (500), offline (post-load disconnect),
 * unknown / conflict where the page renders them.
 */
import { mkdirSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const STAGE = process.env.UI_RECONSTRUCTION_STAGE ?? "baseline";

function outPath(viewport: string, scenario: string): string {
  return path.resolve("artifacts/ui-reconstruction", STAGE, viewport, `${scenario}.png`);
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

// Place fixture used by the visual seed (petaccess_visual).
const FIXTURE_PLACE = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

// ------------------------------------------------------------------ ready ---

const READY_PAGES: [string, string][] = [
  ["home", "/"],
  ["search", "/#/search"],
  ["map", "/#/map"],
  ["place", `/#/place/${FIXTURE_PLACE}`],
  ["reality", `/#/place/${FIXTURE_PLACE}/reality`],
  ["contribute", "/#/contribute"],
  ["mine", "/#/mine"],
];

for (const [slug, url] of READY_PAGES) {
  test(`${slug}-ready`, async ({ page }, testInfo) => {
    const viewport = testInfo.project.name;
    await page.goto(url);
    await settle(page);
    await expect(page.getByTestId("consumer-app-shell").first()).toBeVisible();
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
  await page.route("**/api/v1/places/nearby**", (route) => route.fulfill({ json: JSON_EMPTY_PAGE }));
  await page.goto("/");
  await settle(page);
  await expect(page.getByTestId("home-empty")).toBeVisible();
  await shot(page, viewport, "home-empty");
});

test("home-error", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: {} }) }),
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
    route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: {} }) }),
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

test("place-unknown", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.goto("/#/place/00000000-0000-0000-0000-000000000000");
  await settle(page);
  await shot(page, viewport, "place-unknown");
});

test("map-provider-error", async ({ page }, testInfo) => {
  const viewport = testInfo.project.name;
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: {} }) }),
  );
  await page.goto("/#/map");
  await settle(page);
  await expect(page.locator('[data-state="ERROR"]').first()).toBeVisible();
  await shot(page, viewport, "map-provider-error");
});
