/**
 * PaIcon size regression spec (VIS fix on Android API 35).
 *
 * PaIcon used to bind its size ladder (CSS variables like --pa-size-icon-md)
 * to the SVG width/height *attributes*. SVG presentation attributes reject
 * `var(...)` ("Expected length"), so every icon rendered threw console
 * errors on Android. Sizes are now applied via inline style, where CSS
 * variables are valid. This spec fails if any icon render re-introduces the
 * SVG attribute error.
 */
import { expect, test } from "@playwright/test";

async function collectConsoleErrors(page: import("@playwright/test").Page) {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  await page.goto("/");
  // Wait for the app shell + first render; the icons draw on mount.
  await expect(page.getByTestId("home-title")).toBeVisible();
  await page.waitForTimeout(1200);
  return errors;
}

test("no SVG width/height attribute length errors from icons", async ({ page }) => {
  const errors = await collectConsoleErrors(page);
  const svgLength = errors.filter(
    (e) => e.includes("attribute width") || e.includes("attribute height"),
  );
  expect(svgLength).toEqual([]);
});

test("icons render with non-empty size (no zero-size svg)", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("home-title")).toBeVisible();
  const icons = page.locator("svg.pa-icon").first();
  await expect(icons).toBeVisible();
  const box = await icons.boundingBox();
  expect(box).not.toBeNull();
  if (box) {
    expect(box.width).toBeGreaterThan(0);
    expect(box.height).toBeGreaterThan(0);
  }
});
