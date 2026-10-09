/**
 * UI Reconstruction accessibility gate (AC-R2) — structural a11y assertions
 * on the seven consumer pages, run against the deterministic visual stack.
 *
 * Covers what is objectively assertable in a headless browser:
 *   - one h1 per page (semantic hierarchy, never a heading-less chrome page)
 *   - status is icon + text, never colour-only (`.status-badge__label`)
 *   - the Query Context editor is a labelled dialog; Escape closes it
 *   - shipped stylesheet honours prefers-reduced-motion
 *   - desktop rail links carry accessible names (aria-label)
 *   - mobile controls meet the 44px touch-target token
 *
 * Screen-reader specific behaviours (e.g. Android uiautomator text
 * visibility) are documented as PLATFORM_LIMITED in the audit report, not
 * asserted here.
 */
import { expect, test, type Page } from "@playwright/test";

/** 云栖中心·测试商场 — richest seeded place on the visual stack. */
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

const SEVEN_PAGES: [string, string][] = [
  ["home", "/"],
  ["search", "/#/search"],
  ["map", "/#/map"],
  ["place", `/#/place/${PLACE_ID}`],
  ["reality", `/#/place/${PLACE_ID}/reality`],
  ["evidence", `/#/place/${PLACE_ID}/evidence`],
  ["contribute", "/#/contribute"],
];

async function settle(page: Page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 12000,
    })
    .catch(() => {});
  await page.waitForTimeout(300);
}

test("every consumer page exposes exactly one h1", async ({ page }) => {
  for (const [name, url] of SEVEN_PAGES) {
    await page.goto(url);
    // Retry until the page is settled: the place dossier h1 renders only
    // after its snapshot resolves, so a one-shot count would race the API.
    await expect(page.locator("h1"), `${name} must have exactly one h1`).toHaveCount(1, {
      timeout: 20000,
    });
  }
});

test("status is icon + text, never colour-only", async ({ page }) => {
  await page.goto("/");
  await settle(page);
  const badges = page.locator(".status-badge");
  await expect(badges.first()).toBeVisible();
  const count = await badges.count();
  expect(count).toBeGreaterThan(0);
  for (let i = 0; i < Math.min(count, 6); i += 1) {
    const badge = badges.nth(i);
    await expect(badge.locator(".status-badge__label")).not.toBeEmpty();
    await expect(badge.locator(".status-badge__icon")).not.toBeEmpty();
    await expect(badge).toHaveAttribute("data-status");
  }
});

test("query context editor is a labelled dialog and restores focus", async ({ page }) => {
  await page.goto(`/#/place/${PLACE_ID}`);
  await settle(page);
  const trigger = page.getByTestId("query-context-edit");
  await trigger.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog).toHaveAttribute("aria-modal", "true");
  await expect(dialog).toHaveAttribute("aria-label");
  await expect(page.getByRole("button", { name: "普通携带" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
});

test("mobile search filter sheet owns focus and returns it on close", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto("/#/search?q=云栖");
  await settle(page);
  const trigger = page.getByTestId("filter-toggle");
  await trigger.click();
  const sheet = page.getByRole("dialog", { name: "筛选结果" });
  await expect(sheet).toBeVisible();
  await expect(sheet.locator('input[type="checkbox"]').first()).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(sheet).toBeHidden();
  await expect(trigger).toBeFocused();
  const hiddenPanel = page.locator(".pa-sheet__panel");
  await expect(hiddenPanel).toHaveAttribute("inert");
});

test("shipped stylesheet honours prefers-reduced-motion", async ({ page }) => {
  await page.goto("/");
  await settle(page);
  const hasReducedMotion = await page.evaluate(() =>
    Array.from(document.styleSheets).some((sheet) => {
      try {
        const text = Array.from(sheet.cssRules)
          .map((r) => (r instanceof CSSMediaRule ? r.conditionText : ""))
          .join(" ");
        return text.includes("prefers-reduced-motion");
      } catch {
        return false;
      }
    }),
  );
  expect(hasReducedMotion).toBe(true);
});

test("desktop rail links carry accessible names", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/#/map");
  await settle(page);
  const railLinks = page.locator(".desktop-rail a");
  const count = await railLinks.count();
  expect(count).toBeGreaterThanOrEqual(5);
  for (let i = 0; i < count; i += 1) {
    await expect(railLinks.nth(i)).toHaveAttribute("aria-label");
  }
});

test("mobile controls meet the 44px touch-target token", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 740 });
  await page.goto("/");
  await settle(page);
  const heights = await page.evaluate(() => {
    const pick = (sel: string): number[] => {
      const els = Array.from(document.querySelectorAll<HTMLElement>(sel));
      return els.map((el) => el.getBoundingClientRect().height);
    };
    return {
      primary: pick("button.primary"),
      pills: pick("button.pill"),
      tabs: pick(".mobile-tabbar a"),
      inputs: pick(".home-search input"),
    };
  });
  const min = (values: number[], where: string) => {
    if (!values.length) return;
    expect(Math.min(...values), `${where} must be >= 44px tall`).toBeGreaterThanOrEqual(44);
  };
  min(heights.primary, "primary buttons");
  min(heights.pills, "pill buttons");
  min(heights.tabs, "mobile tabbar items");
  min(heights.inputs, "primary search input");
});
