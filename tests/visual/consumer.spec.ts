/**
 * Consumer H5 — real render, real data, three viewports.
 *
 * These are the pages a real user would land on. Nothing here is mocked: the
 * API is the same one the E2E suite uses, so an empty list means the data is
 * empty, not that the harness is.
 */
import { expect } from "@playwright/test";

import { FIXTURE, freezeClock, settle, shot, test } from "./fixtures";

test.beforeEach(async ({ page }) => {
  await freezeClock(page);
});

test("home — decision home, search-first", async ({ page }) => {
  await page.goto("/");
  await settle(page);
  await shot(page, "home");
});

test("search — results", async ({ page }) => {
  await page.goto("/#/search");
  await settle(page);
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await settle(page);
  await shot(page, "search-results");
});

test("search — empty result", async ({ page }) => {
  await page.goto("/#/search");
  await settle(page);
  await page.getByTestId("search-input").fill("不存在的场所zzz");
  await page.getByTestId("search-btn").click();
  await settle(page);
  await shot(page, "search-empty");
});

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

test("place detail — RESTRICTED (real seeded rules)", async ({ page }) => {
  await page.goto(`/#/place/${FIXTURE.mall}`);
  await settle(page);
  // Named for what the page actually answers. It used to be
  // `place-conditional`, but no seeded place resolves to CONDITIONAL at place
  // level: the mall's answer badge is 「✕ 明确限制」, and CONDITIONAL only shows
  // up on individual zone rows.
  await expect(
    page.locator("[data-testid='answer-ordinary'] [data-status='RESTRICTED']"),
  ).toBeVisible();
  await shot(page, "place-restricted");
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

  // The sheet opens by selecting a marker. It does NOT open from a list row —
  // a list row is `@click="open(p.id)"` and navigates straight to the place
  // page. This test used to tap a list row, which made `map-sheet` a
  // byte-identical copy of `place-unknown` (same MD5 at all three viewports):
  // two baselines, one image, and zero coverage of the sheet.
  //
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
