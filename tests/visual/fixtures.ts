import { expect, type Page, test } from "@playwright/test";

/** Deterministic seed UUIDs (see `services/api/app/db/seed.py`). */
export const FIXTURE = {
  /** 星河咖啡·测试店 — a place with no published rules, i.e. the honest UNKNOWN. */
  cafe: "8412b521-5e1c-505d-9dec-568acb860c76",
  /** 云栖中心·测试商场 — the only seeded place with a real (conditional) rule. */
  mall: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
  /** 广场公园（黄浦段） */
  park: "ece60f6d-ab40-4d80-9570-db11b4593fab",
} as const;

/**
 * Freeze the clock so relative timestamps ("3 天前") render identically on
 * every run — otherwise every baseline diff is a lie about the data.
 */
export async function freezeClock(page: Page) {
  await page.clock.install({ time: new Date("2026-09-15T04:00:00Z") });
}

export async function settle(page: Page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  // The H5 renders skeletons before data, and its slower pages (place detail
  // fans out to eight endpoints) are still on skeletons when `networkidle`
  // fires. Screenshotting then captures a loading state and calls it a page —
  // the baseline would then be wrong in a way no diff would ever flag.
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 10000,
    })
    .catch(() => {});
  await page.waitForTimeout(400);
}

/**
 * A page that failed to load must never become a baseline.
 *
 * `toHaveScreenshot` compares pixels and has no opinion about whether those
 * pixels are correct — a screenshot of 「加载失败」 matches a screenshot of
 * 「加载失败」 forever. This was not hypothetical: a mis-proxied preview made
 * the map page fail every request, and the only reason it surfaced is that one
 * test needed a click that the error page does not offer. The other ten pages
 * would have written broken baselines and passed.
 *
 * `[data-state="ERROR"]` is the shared state block, so this catches every view
 * that has one. NETWORK_ERROR names the case explicitly because an unstyled
 * crash is still a failure worth failing on.
 */
export async function assertNotErrorState(page: Page) {
  const err = page.locator('[data-state="ERROR"], [data-state="NETWORK_ERROR"]');
  const count = await err.count();
  if (count > 0) {
    const text = (await err.first().innerText()).replace(/\s+/g, " ").trim();
    throw new Error(
      `页面处于错误态，拒绝写入基线（${count} 处）：${text}\n` +
        `URL: ${page.url()}\n` +
        `多半是 API 不可达或代理指向了错误的端口 —— 修好数据源再生成基线。`,
    );
  }
}

/**
 * A page that rendered nothing must never become a baseline either.
 *
 * Same failure mode as an error page, one layer down. When WebKit could not
 * load any module in this environment it still rendered `index.html`, so the
 * tests "passed" and wrote 17 baselines of a blank document — 6.2 KB against
 * 100–220 KB for the same pages at the other viewports. Nothing failed,
 * nothing was covered, and the diff tool would have called it stable forever.
 *
 * The check is on the Vue mount point rather than `document.body.innerText`,
 * because some real pages are legitimately short (an empty search result is
 * mostly a heading and one sentence) while a page that never booted has an
 * *empty root*.
 */
export async function assertRendered(page: Page) {
  const root = await page.evaluate(() => {
    const el = document.querySelector("#app, #root, [data-app-root]");
    if (!el) return { found: false, text: "", children: 0 };
    return {
      found: true,
      text: (el.innerText ?? "").replace(/\s+/g, " ").trim(),
      children: el.children.length,
    };
  });

  if (!root.found) throw new Error("找不到应用挂载点（#app / #root / [data-app-root]）");
  if (root.children === 0 || root.text.length < 10) {
    throw new Error(
      `页面挂载点为空，拒绝写入基线 —— 应用没启动，或模块加载失败。\n` +
        `挂载点子元素: ${root.children}，文本长度: ${root.text.length}\n` +
        `URL: ${page.url()}\n` +
        `先确认服务真的在提供 JS，而不是只返回了 index.html。`,
    );
  }
}

/** Screenshot with the shared determinism knobs already applied. */
export async function shot(page: Page, name: string) {
  await assertRendered(page);
  await assertNotErrorState(page);
  await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
}

export { test };
