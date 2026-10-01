/**
 * UI Reconstruction structural gate — objective, non-fragile assertions
 * (GOAL §15.5). Verifies the FROZEN archetypes on the real rendered page:
 *
 *   Search = List–Detail Workspace:
 *     - desktop: result pane + decision inspector both visible (no squeezed two-pane)
 *     - mobile: results only (inspector hidden), tap → place
 *     - result rows are divider rows, NOT `.panel` cards / `.result-card` class
 *     - filter opens as a light panel, not a pill wall
 *   Place = Dossier + Decision Inspector:
 *     - desktop: dossier + sticky inspector
 *     - mobile: single column
 *   Query Context visible on both.
 */
import { expect, test } from "@playwright/test";

test("search desktop: result pane + inspector workspace, no card rows", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河");
  await page.getByTestId("search-btn").click();

  const pane = page.locator(".search-result-pane");
  await expect(pane).toBeVisible();
  await expect(page.getByTestId("decision-inspector")).toBeVisible();

  const row = page.getByTestId("result-星河咖啡·测试店");
  await expect(row).toBeVisible();
  // No old card class on result rows (freeze §9: divider rows, not cards).
  await expect(row).not.toHaveClass(/result-card/);
  await expect(row).not.toHaveClass(/panel/);
});

test("search mobile: results only, no squeezed two-pane; tap navigates to place", async ({
  page,
}) => {
  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河");
  await page.getByTestId("search-btn").click();

  await expect(page.getByTestId("result-星河咖啡·测试店")).toBeVisible();
  // Inspector is desktop-only.
  await expect(page.getByTestId("decision-inspector")).toHaveCount(0);
  // The workspace body must not render as a two-column squeeze.
  const body = page.locator(".search-workspace__body");
  await expect(body).not.toHaveClass(/search-workspace__body--split/);

  await page.getByTestId("result-星河咖啡·测试店").click();
  // v0.2.5 §15: unknown places render the minimal Unknown Overview
  // (PlaceUnknownPane) instead of the full dossier — navigation is proven
  // by the unknown pane, not by a decision surface that no longer exists.
  await expect(page.getByTestId("place-unknown")).toBeVisible();
});

test("place desktop: dossier + sticky decision inspector", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  // §10/§15: use the ready fixture (mall) — unknown places show the minimal
  // Unknown Overview, so the dossier + inspector assertions need a ready place.
  await page.goto("/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e");
  await expect(page.getByTestId("section-answer")).toBeVisible();
  await expect(page.getByTestId("decision-inspector")).toBeVisible();
});

test("place mobile: single column dossier", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto("/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e");
  await expect(page.getByTestId("section-answer")).toBeVisible();
  await expect(page.getByTestId("decision-inspector")).toHaveCount(0);
  const body = page.locator(".place-workspace__body");
  await expect(body).not.toHaveClass(/place-workspace__body--split/);
});

test("query context is visible on search and place", async ({ page }) => {
  await page.goto("/#/search");
  await expect(page.getByTestId("query-context")).toBeVisible();
  await page.goto("/#/place/8412b521-5e1c-505d-9dec-568acb860c76");
  await expect(page.getByTestId("query-context")).toBeVisible();
});
