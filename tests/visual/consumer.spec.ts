/**
 * Consumer H5 — real render, real data, three viewports (390 / 768 / 1440).
 *
 * M2 baseline families (V020 goal §48): Home empty / Home fixture / Search
 * empty / Search fixture / Offline / Error, on both mobile and desktop, light
 * theme. "Fixture" shots render the reseeded visual database; "empty" shots
 * intercept the API to force zero published places; Offline and Error force
 * the edge states directly. Nothing here invents production data.
 */
import { expect } from "@playwright/test";

import { FIXTURE, freezeClock, settle, shot, test } from "./fixtures";

test.beforeEach(async ({ page }) => {
  await freezeClock(page);
});

// ------------------------------------------------------------------ home ----
test("home-fixture — decision home, search-first, real seeded data", async ({ page }) => {
  await page.goto("/");
  await settle(page);
  await shot(page, "home-fixture");
});

test("home-empty — zero published places renders the product empty state", async ({ page }) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.route("**/api/v1/places?**", (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto("/");
  await settle(page);
  await expect(page.getByTestId("home-empty")).toBeVisible();
  await shot(page, "home-empty");
});

test("offline — global offline banner over the home", async ({ page }) => {
  // Load the shell first, THEN drop the network: navigator.onLine flips and the
  // shell's GlobalOfflineBanner must appear. Setting offline before goto() would
  // block the page load itself.
  await page.goto("/");
  await page.context().setOffline(true);
  await page.evaluate(() => window.dispatchEvent(new Event("offline")));
  await settle(page);
  await expect(page.getByTestId("global-offline-banner")).toBeVisible();
  await shot(page, "offline", { allowErrorState: true });
});

test("error — service failure renders the unified error state, never a crash", async ({ page }) => {
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
  await shot(page, "error", { allowErrorState: true });
});

// ---------------------------------------------------------------- search ----
test("search-fixture — results with rule + reality metadata", async ({ page }) => {
  await page.goto("/#/search");
  await settle(page);
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await settle(page);
  await shot(page, "search-fixture");
});

test("search-empty — required copy, not a fake empty", async ({ page }) => {
  await page.goto("/#/search");
  await settle(page);
  await page.getByTestId("search-input").fill("不存在的场所zzz");
  await page.getByTestId("search-btn").click();
  await settle(page);
  await expect(page.getByTestId("search-empty")).toContainText("没有找到已收录场所");
  await shot(page, "search-empty");
});

// ------------------------------------------------------------- other pages ----
test("map — tab shell and list fallback", async ({ page }) => {
  await page.goto("/#/map");
  await settle(page);
  await shot(page, "map");
});

test("place detail — UNKNOWN (no published rule)", async ({ page }) => {
  await page.goto(`/#/place/${FIXTURE.unknown}`);
  await settle(page);
  // A baseline is only evidence about UNKNOWN if the page really is UNKNOWN.
  // Without this the shot stayed green on a page whose answer badge read
  // 「✕ 明确限制」 — the opposite of what the file name promised. Scoped to the
  // answer block on purpose: UNKNOWN also appears on individual zone rows of
  // other places, so an unscoped match would pass on the wrong page.
  await expect(
    page.locator("[data-testid='answer-ordinary'] [data-status='UNKNOWN']"),
  ).toBeVisible();
  await shot(page, "place-unknown");
});

test("place detail — CONDITIONAL (real seeded rules)", async ({ page }) => {
  await page.goto(`/#/place/${FIXTURE.mall}`);
  await settle(page);
  // Named for what the page actually answers. The mall's place-level answer
  // resolves CONDITIONAL (carrier required) via its governing template rule.
  await expect(
    page.locator("[data-testid='answer-ordinary'] [data-status='CONDITIONAL']"),
  ).toBeVisible();
  await shot(page, "place-conditional");
});

test("rule trace — 为什么？", async ({ page }) => {
  await page.goto(`/#/place/${FIXTURE.mall}/why`);
  await settle(page);
  await shot(page, "rule-trace");
});

test("contribution", async ({ page }) => {
  await page.goto("/#/contribute");
  await settle(page);
  await shot(page, "contribute");
});

test("mine — profile and settings hub", async ({ page }) => {
  await page.goto("/#/mine");
  await settle(page);
  await shot(page, "mine");
});

test("boundary — coexistence preference", async ({ page }) => {
  await page.goto("/#/boundary");
  await settle(page);
  await shot(page, "boundary");
});

test("map bottom sheet", async ({ page }) => {
  await page.goto("/#/map");
  await settle(page);

  // The sheet opens by selecting a marker. It does NOT open from a list row.
  // A multi-member cluster zooms instead of selecting, so zoom until single
  // pins appear. The visual database is reset to a fixed dataset before every
  // run, so this takes the same number of clicks every time.
  for (let i = 0; i < 4 && (await page.locator("[data-testid^='pin-']").count()) === 0; i += 1) {
    await page.locator("[data-testid^='cluster-']").first().click();
    await page.waitForTimeout(200);
  }
  await page.locator("[data-testid^='pin-']").first().click();

  // If the sheet never opened, fail here rather than quietly writing another
  // baseline of the wrong page.
  await expect(page.getByTestId("sheet-open-detail")).toBeVisible();
  await page.waitForTimeout(600);
  await shot(page, "map-sheet");
});
