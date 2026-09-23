/**
 * v0.1.0 responsive sanity: the main consumer surfaces must not overflow
 * horizontally at the declared breakpoint matrix (Phase M / A7).
 *
 * Uses the same E2E webServer as the rest of the suite (demo-seeded E2E API),
 * so these are real renders, not mocks. Overflow = document.scrollWidth >
 * window.innerWidth is an assertion failure; a horizontal page is a broken
 * mobile/desktop layout.
 */
import { expect, test } from "@playwright/test";

const VIEWPORTS: { name: string; width: number; height: number }[] = [
  { name: "320", width: 320, height: 568 },
  { name: "390", width: 390, height: 844 },
  { name: "430", width: 430, height: 932 },
  { name: "768", width: 768, height: 1024 },
  { name: "1280", width: 1280, height: 800 },
  { name: "1440", width: 1440, height: 900 },
  { name: "1920", width: 1920, height: 1080 },
];

const PAGES: { name: string; path: string }[] = [
  { name: "home", path: "/" },
  { name: "search", path: "/#/search" },
  { name: "map", path: "/#/map" },
  { name: "contribute", path: "/#/contribute" },
  { name: "settings", path: "/#/settings" },
];

for (const vp of VIEWPORTS) {
  for (const page of PAGES) {
    test(`no horizontal overflow: ${page.name} @ ${vp.name}px`, async ({ page: p }) => {
      await p.setViewportSize({ width: vp.width, height: vp.height });
      await p.goto(page.path);
      // wait for route content (skeletons clear) like the visual fixtures do
      await p
        .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
          timeout: 10000,
        })
        .catch(() => {});
      await p.waitForTimeout(300);
      const overflow = await p.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
      }));
      expect(overflow.scrollWidth, `${page.path} @ ${vp.width}px`).toBeLessThanOrEqual(
        overflow.innerWidth + 1,
      );
    });
  }
}
