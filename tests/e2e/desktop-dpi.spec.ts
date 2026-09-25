/**
 * M8 DESKTOP_FINAL — Windows DPI matrix QA (M2 §7 deferred item).
 *
 * The physical resolutions from the M2 contract (1280×720 / 1440×900 /
 * 1920×1080) at Windows DPI 100/125/150 % produce logical CSS viewports of
 * `physical / scale`. We simulate each cell with that logical viewport plus a
 * `deviceScaleFactor` equal to the DPI scale — deliberately NOT a claim of
 * having switched the real display's DPI, which headless Win32 cannot do
 * reliably (see V010_DESKTOP_REPORT limitations).
 *
 * `deviceScaleFactor` is fixed at context creation, so each cell gets its own
 * `describe` + `test.use` block instead of `setViewportSize` (which only
 * resizes, never rescales).
 *
 * Assertions per cell: no horizontal overflow on the main consumer surfaces,
 * the desktop rail is the active navigation ≥ 768px logical, and the page
 * actually rendered (not an error/empty shell).
 */
import { expect, test, type Page } from "@playwright/test";

/** 云栖中心·测试商场 — richest seeded page. */
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

/** @see apps/client-h5/src/composables/useBreakpoint.ts — lg = 768px. */
const RAIL_BREAKPOINT = 768;

interface DpiCell {
  /** display name, e.g. "1280x720@100" */
  name: string;
  /** physical resolution as stated in the M2 contract (naming only). */
  physical: string;
  /** logical CSS viewport that physical/scale resolves to. */
  width: number;
  height: number;
  /** DPI scale, expressed as a ratio (100% → 1, 125% → 1.25, 150% → 1.5). */
  scale: number;
}

const CELLS: DpiCell[] = [
  { name: "1280x720@100", physical: "1280×720", width: 1280, height: 720, scale: 1.0 },
  { name: "1280x720@125", physical: "1280×720", width: 1024, height: 576, scale: 1.25 },
  { name: "1280x720@150", physical: "1280×720", width: 853, height: 480, scale: 1.5 },
  { name: "1440x900@100", physical: "1440×900", width: 1440, height: 900, scale: 1.0 },
  { name: "1440x900@125", physical: "1440×900", width: 1152, height: 720, scale: 1.25 },
  { name: "1440x900@150", physical: "1440×900", width: 960, height: 600, scale: 1.5 },
  { name: "1920x1080@100", physical: "1920×1080", width: 1920, height: 1080, scale: 1.0 },
  { name: "1920x1080@125", physical: "1920×1080", width: 1536, height: 864, scale: 1.25 },
  { name: "1920x1080@150", physical: "1920×1080", width: 1280, height: 720, scale: 1.5 },
];

const SURFACES: { name: string; path: string }[] = [
  { name: "home", path: "/" },
  { name: "search", path: "/#/search" },
  { name: "map", path: "/#/map" },
  { name: "place", path: `/#/place/${MALL_ID}` },
  { name: "contribute", path: "/#/contribute" },
  { name: "mine", path: "/#/mine" },
];

/** Content is skeleton-led; let the page settle like the visual fixtures. */
async function settle(page: Page) {
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 10000,
    })
    .catch(() => {});
  await page.waitForTimeout(300);
}

for (const cell of CELLS) {
  test.describe(`DPI ${cell.name} (${cell.physical} @ ${Math.round(cell.scale * 100)}%)`, () => {
    test.use({
      viewport: { width: cell.width, height: cell.height },
      deviceScaleFactor: cell.scale,
    });

    for (const surface of SURFACES) {
      test(`${surface.name} renders, no overflow, desktop rail`, async ({ page }) => {
        await page.goto(surface.path);
        await settle(page);

        // The page must have rendered real content, not an error/empty shell.
        const mounted = await page.evaluate(() => {
          const el = document.querySelector("#app");
          return el ? (el.textContent?.trim().length ?? 0) : 0;
        });
        expect(mounted, `${surface.path} @ ${cell.name}`).toBeGreaterThan(0);

        // No horizontal overflow at ANY logical width.
        const size = await page.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
        }));
        expect(size.scrollWidth, `${surface.path} @ ${cell.name}`).toBeLessThanOrEqual(
          size.innerWidth + 1,
        );

        // All cells resolve to ≥ 768 logical px → the rail is the active nav.
        expect(cell.width, `${cell.name} must stay desktop (>= lg)`).toBeGreaterThanOrEqual(
          RAIL_BREAKPOINT,
        );
        await expect(page.getByTestId("desktop-rail"), `${cell.name} rail`).toBeVisible();
        await expect(page.getByTestId("mobile-tabbar"), `${cell.name} tabbar`).toHaveCount(0);

        // The simulated scale must actually be in effect (guard against a cell
        // silently running at scale 1).
        const dpr = await page.evaluate(() => window.devicePixelRatio);
        expect(dpr, `${cell.name} devicePixelRatio`).toBeCloseTo(cell.scale, 2);
      });
    }
  });
}
