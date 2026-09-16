/**
 * Consumer H5 — real render, real data, three viewports.
 *
 * These are the pages a real user would land on. Nothing here is mocked: the
 * API is the same one the E2E suite uses, so an empty list means the data is
 * empty, not that the harness is.
 */
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
  await page.goto(`/#/place/${FIXTURE.cafe}`);
  await settle(page);
  await shot(page, "place-unknown");
});

test("place detail — CONDITIONAL (real seeded rule)", async ({ page }) => {
  await page.goto(`/#/place/${FIXTURE.mall}`);
  await settle(page);
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
  // The mock map is the only "map" available without a real tile provider, so
  // the sheet is opened from the list — the same entry point a user has.
  await page.getByTestId("view-list").click();
  await page.locator("[data-testid^='place-']").first().click();
  await page.waitForTimeout(600);
  await shot(page, "map-sheet");
});
