/**
 * PlacePreview grid overflow regression (VIS-002, found on tablet 800dp).
 *
 * `.place-preview__row` is `display:grid; grid-template-columns: 5rem 1fr`.
 * Without `min-width: 0` on the grid child, a long value (rule summary /
 * address) forces the `1fr` track wider than its container, so the document
 * overflows horizontally on split-layout widths (>= lg). Only reachable when a
 * search produced results AND the right-side preview panel rendered — the
 * plain empty-search responsive spec never exercised it.
 */
import { expect, test } from "@playwright/test";

const SPLIT_WIDTHS = [768, 800, 1024];

test("search with results does not overflow horizontally on split-layout widths", async ({
  page,
}) => {
  await page.setViewportSize({ width: 800, height: 1200 });
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河");
  await page.getByTestId("search-btn").click();

  // One result row must render (demo DB has 星河咖啡·测试店 / 栖霞分店).
  const result = page.getByTestId("result-星河咖啡·测试店");
  await expect(result).toBeVisible({ timeout: 15000 });
  // The right-pane preview must have mounted for the overflow scenario.
  const preview = page.getByTestId("place-preview");
  await expect(preview).toBeVisible({ timeout: 15000 });

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  expect(
    overflow.scrollWidth,
    `search+preview overflow at ${overflow.innerWidth}px`,
  ).toBeLessThanOrEqual(overflow.innerWidth + 1);
});

test("no horizontal overflow at each split-layout viewport once preview is populated", async ({
  page,
}) => {
  for (const width of SPLIT_WIDTHS) {
    await page.setViewportSize({ width, height: width >= 1024 ? 800 : 1200 });
    await page.goto("/#/search");
    await page.getByTestId("search-input").fill("星河");
    await page.getByTestId("search-btn").click();
    await expect(page.getByTestId("place-preview")).toBeVisible({ timeout: 15000 });

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    expect(overflow.scrollWidth, `overflow at ${width}px`).toBeLessThanOrEqual(
      overflow.innerWidth + 1,
    );
  }
});
