/**
 * UI Oracle — human-review.spec.ts
 *
 * Captures the 14 named HUMAN_REVIEW screenshots (evidence artifacts only:
 * fixed viewport, deterministic data, animations disabled, clock frozen).
 * Every shot is written to artifacts/blind-ui-recovery/HUMAN_REVIEW/ with a
 * HUMAN_REVIEW_INDEX.html that carries page / viewport / machine-contract
 * status / known notes — the HTML performs NO aesthetic evaluation (Blind-Model
 * rule). The machine PASS/WARN/FAIL per shot comes from the final compare
 * artifacts, not from reading the pixels.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const OUT = path.resolve("artifacts/blind-ui-recovery/HUMAN_REVIEW");
const API = "http://127.0.0.1:8012/api/v1";
const MALL = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";
const CAFE = "8412b521-5e1c-505d-9dec-568acb860c76";
const UNKNOWN = "3b5a341a-e550-5f0c-b35a-319ed43bd840";

interface Shot {
  name: string;
  width: number;
  height: number;
  route: string;
  contractId: string;
  auth?: boolean;
  emptySearch?: boolean;
  openFilter?: boolean;
  note: string;
}

const SHOTS: Shot[] = [
  { name: "01_search_desktop_ready", width: 1440, height: 900, route: "/#/search", contractId: "search.desktop", note: "结果列表 + detail 双栏" },
  { name: "02_search_desktop_empty", width: 1440, height: 900, route: "/#/search", contractId: "search.desktop", emptySearch: true, note: "无结果空态：主行动 + 导航保留" },
  { name: "03_search_desktop_selected", width: 1440, height: 900, route: "/#/search?q=%E6%98%9F%E6%B2%B3", contractId: "search.desktop", note: "选中行 + detail 决策锚点" },
  { name: "04_search_mobile_ready", width: 430, height: 932, route: "/#/search", contractId: "search.mobile", note: "移动单列列表" },
  { name: "05_search_mobile_filter", width: 430, height: 932, route: "/#/search", contractId: "search.mobile", openFilter: true, note: "筛选 bottom sheet（顶部圆角 + 拖拽把手）" },
  { name: "06_place_desktop_ready", width: 1440, height: 900, route: `/#/place/${MALL}`, contractId: "place.desktop", note: "dossier + sticky inspector" },
  { name: "07_place_desktop_unknown", width: 1440, height: 900, route: `/#/place/${UNKNOWN}`, contractId: "place.desktop", note: "无已发布规则 → UNKNOWN 诚实态" },
  { name: "08_place_mobile_ready", width: 430, height: 932, route: `/#/place/${MALL}`, contractId: "place.mobile", note: "移动单列 dossier" },
  { name: "09_home_desktop", width: 1440, height: 900, route: "/#/", contractId: "home", note: "无 hero / 无 pill wall；入口行 + nearby" },
  { name: "10_map_desktop", width: 1440, height: 900, route: "/#/map", contractId: "map", note: "空间 mock 地图 + 结果窗格 + 筛选 N" },
  { name: "11_reality_desktop", width: 1440, height: 900, route: `/#/place/${CAFE}/reality`, contractId: "reality", note: "事件时间线（非卡片）" },
  { name: "12_evidence_desktop", width: 1440, height: 900, route: `/#/place/${CAFE}/evidence`, contractId: "evidence", note: "provenance 链 + 三时间分离" },
  { name: "13_contribution_desktop", width: 1440, height: 900, route: `/#/contribute/${MALL}`, contractId: "contribution", auth: true, note: "第一屏：你刚刚知道了什么？5 选项" },
  { name: "14_contribution_mobile", width: 430, height: 932, route: `/#/contribute/${MALL}`, contractId: "contribution", auth: true, note: "移动端贡献入口（认证态）" },
];

async function freezeMotion(page: import("@playwright/test").Page): Promise<void> {
  await page.addStyleTag({ content: "* { transition: none !important; animation: none !important; }" });
  await page.emulateMedia({ reducedMotion: "reduce" });
}

async function settle(page: import("@playwright/test").Page): Promise<void> {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, { timeout: 15000 })
    .catch(() => {});
  await page.waitForTimeout(250);
}

async function signIn(request: import("@playwright/test").APIRequestContext): Promise<string> {
  const email = `human-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Human Review 探针", email, password: "passw0rd123" },
  });
  expect(reg.ok()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, { data: { email, password: "passw0rd123" } });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

function contractStatus(contractId: string): { PASS: number; WARN: number; FAIL: number } {
  try {
    const c = JSON.parse(
      readFileSync(path.resolve(`artifacts/blind-ui-recovery/reports/compare-${contractId}.json`), "utf8"),
    ) as { summary: { PASS: number; WARN: number; FAIL: number } };
    return c.summary;
  } catch {
    return { PASS: 0, WARN: 0, FAIL: 0 };
  }
}

test("human review — 14 named screenshots (evidence artifacts only)", async ({ page, request }) => {
  mkdirSync(OUT, { recursive: true });
  const rows: Array<{ name: string; viewport: string; route: string; contract: string; status: string; bytes: number; note: string }> = [];

  for (const shot of SHOTS) {
    await page.setViewportSize({ width: shot.width, height: shot.height });
    // Clock frozen BEFORE navigation so relative timestamps are deterministic.
    await page.clock.install({ time: new Date("2026-09-15T04:00:00Z") }).catch(() => {});

    if (shot.auth) {
      const token = await signIn(request);
      await page.goto("/");
      await page.evaluate((t) => localStorage.setItem("pa_token", t), token);
    }
    if (shot.emptySearch) {
      await page.route("**/api/v1/places?**", (route) =>
        route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
      );
      await page.goto(shot.route);
      await freezeMotion(page);
      await settle(page);
      await page.getByTestId("search-input").fill("不存在的场所zzz");
      await page.getByTestId("search-btn").click();
      await settle(page);
    } else {
      await page.goto(shot.route);
      await freezeMotion(page);
      await settle(page);
    }

    if (shot.openFilter) {
      await page.getByTestId("filter-toggle").click();
      await page.waitForSelector("[data-ui='search-filter-sheet']").catch(() => {});
      await page.waitForTimeout(300);
    }

    const file = path.join(OUT, `${shot.name}.png`);
    await page.screenshot({ path: file });
    const bytes = (await import("node:fs")).statSync(file).size;
    const s = contractStatus(shot.contractId);
    rows.push({
      name: shot.name,
      viewport: `${shot.width}x${shot.height}`,
      route: shot.route,
      contract: shot.contractId,
      status: `PASS=${s.PASS} WARN=${s.WARN} FAIL=${s.FAIL}`,
      bytes,
      note: shot.note,
    });
  }

  const cards = rows
    .map(
      (r) => `<div class="card">
  <h2>${r.name}</h2>
  <dl>
    <dt>Viewport</dt><dd>${r.viewport}</dd>
    <dt>Route</dt><dd><code>${r.route}</code></dd>
    <dt>Machine contract</dt><dd>${r.status}</dd>
    <dt>PNG bytes</dt><dd>${r.bytes}</dd>
    <dt>Known notes</dt><dd>${r.note}</dd>
  </dl>
  <img src="${r.name}.png" alt="${r.name} — 机器契约状态 ${r.status}" loading="lazy" />
</div>`,
    )
    .join("\n");

  writeFileSync(
    path.join(OUT, "HUMAN_REVIEW_INDEX.html"),
    `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PetAccess v0.2.2 — Blind-Model UI 人工视觉验收包</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 1100px; color: #222; }
  h1 { font-size: 1.4rem; }
  .card { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin: 1.2rem 0; }
  .card img { max-width: 100%; border: 1px solid #ddd; margin-top: 0.6rem; }
  dl { display: grid; grid-template-columns: 10rem 1fr; gap: 0.25rem 1rem; }
  dt { font-weight: 600; }
  dd { margin: 0; }
  .status { margin-top: 1rem; font-size: 0.9rem; color: #555; }
</style>
</head>
<body>
  <h1>PetAccess v0.2.2 — Blind-Model UI 人工视觉验收包（${rows.length} 张）</h1>
  <p>本页仅为人类视觉验收提供固定视口 / 确定性数据 / 冻结时钟的截图证据。机器契约状态来自 compare.ts 最终门禁；HTML 不做任何美学评价（Blind-Model 规则：Agent 不代替用户做视觉签字）。</p>
  ${cards}
  <p class="status">截图校验方式：文件存在、PNG magic、dimensions、non-zero bytes、hash distinct — 详见 BLIND_UI_FINAL_REPORT.md。</p>
</body>
</html>
`,
    "utf8",
  );
});
