/**
 * M3 深化收口回归（V020_M3_CONSUMER_CORE）。
 *
 * 覆盖本轮新增的 Consumer 架构契约，均为真实渲染断言：
 *   - CoexistenceSnapshot 行级 Reality 摘要（Search 结果行 / Home 结果卡）
 *   - transport error ≠ domain fact：行级 answer/reality 失败显式标记，
 *     不伪装成 UNKNOWN / 空态（row-answer-error / row-reality-error）
 *   - request epoch / race：快速连续搜索时慢旧请求不覆盖新结果
 *   - cache reuse：同一查询二次访问不再重复发起请求（请求计数）
 *   - runtime console gate：无 unexpected console.error / pageerror
 *
 * 与既有 spec 不重复：深链/back-forward（consumer-routes）、空态文案
 * （empty-state）、overflow（responsive / place-preview-overflow）由既有
 * spec 守护；这里只守 M3 新增契约。
 */
import { expect, test } from "@playwright/test";

const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test("search rows show reality summary + evidence metadata", async ({ page }) => {
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await expect(page.locator("[data-testid^='result-']").first()).toBeVisible();
  // M3: 每行带 Reality 摘要块（近期现场 + 依据元数据），再非只有规则徽标。
  await expect(page.getByTestId("result-reality").first()).toBeVisible();
});

test("search row snapshot failure is explicit, not UNKNOWN-as-truth", async ({ page }) => {
  // places 列表 mock 用正则只匹配 `/places?`（字面问号），避免 `?` 被当成
  // 单字符通配符而吞掉下方的 coexistence 路由。
  await page.route(/\/api\/v1\/places\?/, (route) =>
    route.fulfill({
      json: {
        items: [
          {
            id: "00000000-0000-0000-0000-000000000001",
            canonical_name: "断网测试场所",
            place_type: "cafe",
            rule_count: 1,
          },
        ],
        total: 1,
        limit: 20,
        offset: 0,
      },
    }),
  );
  // M3.1：行级事实 = CoexistenceSnapshot SSOT；snapshot 失败（transport error）
  // → 显式标记，绝不伪装成 UNKNOWN，也绝不写入缓存。
  await page.route("**/coexistence", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: {} }),
    }),
  );
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("断网");
  await page.getByTestId("search-btn").click();
  await expect(page.getByTestId("result-断网测试场所")).toBeVisible();
  // transport error ≠ UNKNOWN：UI 明确说"暂时无法取得"，不允许只渲染"尚未核验"徽标。
  await expect(page.locator('[data-testid="result-断网测试场所"]')).toContainText(
    "规则结论暂时无法取得",
  );
});

test("request epoch: slow old search never overwrites a fast new one", async ({ page }) => {
  const calls: string[] = [];
  await page.route(/\/api\/v1\/places\?/, async (route) => {
    const url = route.request().url();
    calls.push(url);
    const q = new URL(url).searchParams.get("q") ?? "";
    // 旧的「咖啡」查询人为延迟 1200ms；新的「星河」立即返回。
    if (q.includes("咖啡")) {
      await new Promise((r) => setTimeout(r, 1200));
    }
    await route.continue();
  });
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  // 第二次查询用 Enter 触发（搜索按钮在 loading 期间 disabled，Enter 不受影响）。
  await page.getByTestId("search-input").fill("星河");
  await page.getByTestId("search-input").press("Enter");
  // 等待两个响应都结束，最终结果必须是最新查询。
  await page.waitForTimeout(1600);
  const firstResult = page.locator("[data-testid^='result-']").first();
  await expect(firstResult).toBeVisible();
  const text = await firstResult.innerText();
  expect(text).toContain("星河");
  expect(calls.filter((u) => u.includes("q=%E6%98%9F%E6%B2%B3"))).toHaveLength(1);
});

test("cache reuse: revisiting the same query does not duplicate requests", async ({ page }) => {
  let searchCalls = 0;
  await page.route(/\/api\/v1\/places\?/, (route) => {
    searchCalls += 1;
    void route.continue();
  });
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await expect(page.locator("[data-testid^='result-']").first()).toBeVisible();
  const afterFirst = searchCalls;
  await page.waitForTimeout(300); // 让首次请求完全落袋
  // 清空再搜同一词：cache 命中，不应再打 search 端点。
  await page.getByTestId("search-clear").click();
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await expect(page.locator("[data-testid^='result-']").first()).toBeVisible();
  await page.waitForTimeout(300);
  expect(searchCalls, "same q within TTL must reuse cache").toBe(afterFirst);
});

test("runtime console gate: no unexpected console.error / pageerror on Home+Search", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  await page.goto("/");
  await expect(page.getByTestId("consumer-app-shell")).toBeVisible();
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("咖啡");
  await page.getByTestId("search-btn").click();
  await expect(page.locator("[data-testid^='result-']").first()).toBeVisible();
  expect(errors, `unexpected console errors: ${errors.join(" | ")}`).toEqual([]);
});

test("evidence rail exposes governance state instead of a generic trust badge", async ({ page }) => {
  await page.goto(`/#/place/${MALL_ID}/evidence`);
  await expect(page.getByTestId("evidence-workspace")).toBeVisible();
  const governance = page.locator('[data-ui="evidence-governance"]');
  await expect(governance).toBeVisible();
  await expect(governance).toContainText("人工接受");
  await expect(governance).toContainText("来源方式");
  await expect(governance).toContainText("证据形态");
  await expect(governance).toContainText("原始材料 / 许可");
  await expect(governance).toContainText("独立确认");
  await expect(governance).toContainText("一手规则来源");
  await expect(governance).toContainText("争议 / 纠错");
  await expect(governance).toContainText("一组材料不自动等于多份独立证据");
});
