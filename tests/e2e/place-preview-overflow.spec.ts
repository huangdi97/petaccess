/**
 * Search workspace overflow regression (VIS-002 lineage, UI reconstruction).
 *
 * `.result-row__reality` and the DecisionInspector rows must not force the
 * document wider than the viewport on split-layout widths. The right-side
 * inspector is the new `decision-inspector` surface (Design Freeze §9).
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

  const result = page.getByTestId("result-星河咖啡·测试店");
  await expect(result).toBeVisible({ timeout: 15000 });
  // The detail inspector must have mounted for the overflow scenario.
  await expect(page.getByTestId("decision-inspector")).toBeVisible({ timeout: 15000 });

  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }));
  expect(
    overflow.scrollWidth,
    `search+inspector overflow at ${overflow.innerWidth}px`,
  ).toBeLessThanOrEqual(overflow.innerWidth + 1);
});

test("no horizontal overflow at each split-layout viewport once inspector is populated", async ({
  page,
}) => {
  for (const width of SPLIT_WIDTHS) {
    await page.setViewportSize({ width, height: width >= 1024 ? 800 : 1200 });
    await page.goto("/#/search");
    await page.getByTestId("search-input").fill("星河");
    await page.getByTestId("search-btn").click();
    await expect(page.getByTestId("decision-inspector")).toBeVisible({ timeout: 15000 });

    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
    }));
    expect(overflow.scrollWidth, `overflow at ${width}px`).toBeLessThanOrEqual(
      overflow.innerWidth + 1,
    );
  }
});
