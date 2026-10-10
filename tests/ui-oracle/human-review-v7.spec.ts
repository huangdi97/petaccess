/**
 * UI Oracle — human-review-v7.spec.ts (v0.2.7 Final Product Craft, §36–37)
 *
 * Curated HUMAN_REVIEW screenshots for the v7 craft candidate. Same engine as
 * the v0.2.4/v0.2.5 packs: fixed viewport, deterministic clock, motion frozen,
 * every shot gated by Capture State Integrity (O6) — the ACTUAL DOM state
 * (data-ui-page/state/fixture/h1/entity/selected/count) is read from the page
 * and must match the shot's `expect` before the PNG is written.
 *
 * §36 minimum list (13 shots, 1440×900 / 430×932, viewport capture):
 *   01 home desktop · 02 search desktop · 03 place desktop overview ·
 *   04 map desktop · 05 map mobile ready · 06 map mobile half ·
 *   07 map mobile expanded · 08 reality desktop · 09 evidence desktop ·
 *   10 contribution desktop choose · 11 contribution desktop step1 ·
 *   12 contribution desktop step2 · 13 contribution mobile step1
 *
 * The INDEX pairs each shot with the frozen RC visual baseline ("before")
 * from tests/visual/*-snapshots where the same route was captured, so the
 * human can see the craft delta side by side. metadata 只证明真实状态，
 * 不宣称视觉通过；Agent 不代替用户做视觉签字。
 *
 * Output: artifacts/ui-product-craft-v7/HUMAN_REVIEW/…
 */
import { existsSync, mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const OUT = path.resolve("artifacts/ui-product-craft-v7/HUMAN_REVIEW");
const BEFORE_DIR = path.resolve("tests/visual/consumer.spec.ts-snapshots");
const API = "http://127.0.0.1:8012/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e"; // ready fixture
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76"; // canonical v0.9 empty fixture

interface StateExpect {
  page?: string;
  state?: string;
  fixture?: string;
  h1?: string;
  entityId?: string;
  selectedId?: string;
  count?: number;
  counts?: Record<string, number>;
}

interface Shot {
  name: string;
  width: number;
  height: number;
  route: string;
  auth?: boolean;
  clickTestid?: string;
  waitTestid?: string;
  expect: StateExpect;
  note: string;
  /** before 对照：tests/visual 已冻结的 RC baseline PNG（存在才显示）。 */
  before?: string;
}

const SHOTS: Shot[] = [
  {
    name: "01_home_desktop",
    width: 1440,
    height: 900,
    route: "/",
    before: "home-fixture-h5-1440-win32.png",
    expect: {
      page: "home",
      state: "ready",
      fixture: "home-ready-v1",
      h1: "去之前，先看规则与现场。",
    },
    note: "v0.2.7：Home task launcher 保持；本页无 craft 改动（基线对照）。",
  },
  {
    name: "02_search_desktop",
    width: 1440,
    height: 900,
    route: "/#/search",
    before: "search-fixture-h5-1440-win32.png",
    expect: {
      page: "search",
      state: "ready-selected",
      fixture: "search-ready-v1",
      h1: "搜索场所规则",
      selectedId: "search-selected-row",
    },
    note: "v0.2.7 §22：detail secondary evidence grouping（reality+evidence 归组、顶部细分隔线）。",
  },
  {
    name: "03_place_desktop_overview",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}`,
    before: "place-conditional-h5-1440-win32.png",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      h1: "云栖中心·测试商场",
      entityId: MALL_ID,
    },
    note: "v0.2.7 §23：Place 尽量不动，仅 spacing/hierarchy 收口。",
  },
  {
    name: "04_map_desktop",
    width: 1440,
    height: 900,
    route: "/#/map",
    before: "map-h5-1440-win32.png",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.7 §8–11：abstract urban canvas（道路层级/街区/开放空间/水系/体块），selected marker scale+halo。",
  },
  {
    name: "05_map_mobile_ready",
    width: 430,
    height: 932,
    route: "/#/map",
    before: "map-h5-390-win32.png",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.7 §8：mobile canvas 同样抽象城市基底；地图不抢 overlay。",
  },
  {
    name: "06_map_mobile_half",
    width: 430,
    height: 932,
    route: `/#/map?place=${CAFE_ID}`,
    before: "map-sheet-h5-390-win32.png",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.7 §12：half sheet 仅 craft handle/metadata/status 层级。",
  },
  {
    name: "07_map_mobile_expanded",
    width: 430,
    height: 932,
    route: `/#/map?place=${CAFE_ID}`,
    clickTestid: "sheet-handle",
    waitTestid: "sheet-verdict",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.7 §13：expanded 只加真实信息（结论/证据与来源），无伪造填充。",
  },
  {
    name: "08_reality_desktop",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}/reality`,
    before: "reality-trace-h5-1440-win32.png",
    expect: {
      page: "reality",
      state: "ready",
      fixture: "reality-ready-v1",
      h1: "现场轨迹",
    },
    note: "v0.10-R1：published presence / staff / facility 共用时间轴；事件、地点、核验/证据分层。",
  },
  {
    name: "09_evidence_desktop",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}/evidence`,
    expect: {
      page: "evidence",
      state: "ready",
      fixture: "evidence-records-v1",
      h1: "证据与来源",
    },
    note: "v0.10-R1：真实 v0.9 Evidence Record；规则依据与现场依据并维、Observed/Submitted/Reviewed 分开。",
  },
  {
    name: "10_contribution_desktop_choose",
    width: 1440,
    height: 900,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    before: "contribute-h5-1440-win32.png",
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
      counts: { "choice-count": 5 },
    },
    note: "v0.2.7 §15–16：desktop main+context 双栏（context rail 只放真实上下文）。",
  },
  {
    name: "11_contribution_desktop_step1",
    width: 1440,
    height: 900,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-quick",
    waitTestid: "quick-submit",
    expect: {
      page: "contribution",
      state: "step-1",
      fixture: "contribution-step-1-v1",
      h1: "现场贡献",
    },
    note: "v0.2.7 §17：progress quieter、question 更强；context rail 持续。",
  },
  {
    name: "12_contribution_desktop_step2",
    width: 1440,
    height: 900,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-observed_presence",
    waitTestid: "reality-submit",
    expect: {
      page: "contribution",
      state: "step-2",
      fixture: "contribution-step-2-v1",
      h1: "现场贡献",
    },
    note: "v0.2.7 §19：When/Where/What field group 20–28px 稳定节奏。",
  },
  {
    name: "13_contribution_mobile_step1",
    width: 430,
    height: 932,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-quick",
    waitTestid: "quick-submit",
    before: "contribute-h5-390-win32.png",
    expect: {
      page: "contribution",
      state: "step-1",
      fixture: "contribution-step-1-v1",
      h1: "现场贡献",
    },
    note: "v0.2.7：mobile 单列不变；context rail 仅 desktop 渲染。",
  },
];

async function freezeMotion(page: import("@playwright/test").Page): Promise<void> {
  await page.addStyleTag({
    content: "* { transition: none !important; animation: none !important; }",
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
}

async function settle(page: import("@playwright/test").Page): Promise<void> {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 15000,
    })
    .catch(() => {});
  await page.waitForTimeout(250);
}

async function signIn(request: import("@playwright/test").APIRequestContext): Promise<string> {
  const email = `human7-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Human Review v7 探针", email, password: "passw0rd123" },
  });
  expect(reg.ok()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

/** O6: read the REAL page state from the DOM — never hand-written. */
async function readActualState(
  page: import("@playwright/test").Page,
): Promise<Record<string, unknown>> {
  return page.evaluate(() => {
    const host = document.querySelector("[data-ui-page]");
    const h1 = document.querySelector("h1");
    const countEl = document.querySelector("[data-ui-count='result-rows']");
    const selected = document.querySelector("[data-ui*='selected']");
    const entityEl =
      document.querySelector("[data-ui-entity-id]") ?? document.querySelector("[data-entity-id]");
    const counts: Record<string, number> = {};
    for (const el of document.querySelectorAll("[data-ui-count]")) {
      const key = el.getAttribute("data-ui-count") ?? "";
      if (key) counts[key] = Number(el.textContent ?? NaN) || 0;
    }
    return {
      route: location.hash,
      page: host?.getAttribute("data-ui-page") ?? null,
      state: host?.getAttribute("data-ui-state") ?? null,
      fixture: host?.getAttribute("data-ui-fixture") ?? null,
      h1: h1 ? (h1.textContent ?? "").trim() : null,
      entityId:
        entityEl?.getAttribute("data-ui-entity-id") ??
        entityEl?.getAttribute("data-entity-id") ??
        null,
      selectedId: selected?.getAttribute("data-ui") ?? null,
      count: countEl ? Number(countEl.textContent ?? NaN) || null : null,
      counts,
    };
  });
}

function assertState(
  actual: Record<string, unknown>,
  expectState: StateExpect,
): { ok: boolean; mismatches: string[] } {
  const mismatches: string[] = [];
  const check = (key: string, exp: unknown): void => {
    if (exp === undefined) return;
    if (String(actual[key]) !== String(exp)) {
      mismatches.push(`${key}: expected=${String(exp)} actual=${String(actual[key])}`);
    }
  };
  check("page", expectState.page);
  check("state", expectState.state);
  check("fixture", expectState.fixture);
  check("h1", expectState.h1);
  check("entityId", expectState.entityId);
  check("selectedId", expectState.selectedId);
  check("count", expectState.count);
  for (const [key, exp] of Object.entries(expectState.counts ?? {})) {
    const counts = (actual.counts ?? {}) as Record<string, number>;
    if (counts[key] !== exp) {
      mismatches.push(`counts.${key}: expected=${String(exp)} actual=${String(counts[key])}`);
    }
  }
  return { ok: mismatches.length === 0, mismatches };
}

test("human review v0.2.7 — named screenshots with Capture State Integrity", async ({
  page,
  request,
}, testInfo) => {
  const project = testInfo.project?.name ?? "";
  const isDesktopProject = project === "oracle-desktop";
  const rows: Array<{
    name: string;
    viewport: string;
    route: string;
    valid: boolean;
    bytes: number;
    note: string;
    mismatches: string[];
    before: string | null;
  }> = [];

  for (const shot of SHOTS) {
    const wantDesktop = shot.width >= 1000;
    if (wantDesktop !== isDesktopProject) continue;

    mkdirSync(OUT, { recursive: true });

    await page.setViewportSize({ width: shot.width, height: shot.height });
    await page.clock.install({ time: new Date("2026-09-15T04:00:00Z") }).catch(() => {});

    if (shot.auth) {
      const token = await signIn(request);
      await page.goto("/");
      await page.evaluate((t) => localStorage.setItem("pa_token", t), token);
    }
    await page.goto(shot.route);
    await page.reload();
    await freezeMotion(page);
    await settle(page);

    if (shot.clickTestid) {
      await page
        .getByTestId(shot.clickTestid)
        .click()
        .catch(() => {});
      if (shot.waitTestid) {
        await page
          .waitForSelector(`[data-testid='${shot.waitTestid}']`, { timeout: 5000 })
          .catch(() => {});
      }
      await settle(page);
    }

    // O6: assert the real DOM state BEFORE saving (§37).
    const actual = await readActualState(page);
    const { ok, mismatches } = assertState(actual, shot.expect);
    const beforeFile =
      shot.before && existsSync(path.join(BEFORE_DIR, shot.before)) ? shot.before : null;
    const meta = {
      name: shot.name,
      viewport: `${shot.width}x${shot.height}`,
      route: shot.route,
      expected: shot.expect,
      actual,
      valid: ok,
      mismatches,
      before: beforeFile,
      note: shot.note,
      generatedAt: new Date().toISOString(),
    };

    if (ok) {
      const file = path.join(OUT, `${shot.name}.png`);
      await page.screenshot({ path: file });
      writeFileSync(path.join(OUT, `${shot.name}.json`), JSON.stringify(meta, null, 2), "utf8");
      rows.push({ ...meta, bytes: statSync(file).size });
    } else {
      const invalidDir = path.join(OUT, "_invalid");
      mkdirSync(invalidDir, { recursive: true });
      const file = path.join(invalidDir, `${shot.name}.png`);
      await page.screenshot({ path: file });
      writeFileSync(
        path.join(invalidDir, `${shot.name}.json`),
        JSON.stringify(meta, null, 2),
        "utf8",
      );
      rows.push({ ...meta, bytes: statSync(file).size });
    }
  }

  const valid = rows.filter((r) => r.valid);
  const invalid = rows.filter((r) => !r.valid);
  const cards = rows
    .map(
      (r) => `<div class="card">
  <h2>${r.name} ${r.valid ? "✅" : "⛔"}</h2>
  <dl>
    <dt>Viewport</dt><dd>${r.viewport}</dd>
    <dt>Route</dt><dd><code>${r.route}</code></dd>
    <dt>State integrity</dt><dd>${r.valid ? "VALID — actual DOM 与 expected 一致" : `INVALID — ${r.mismatches.join("; ")}`}</dd>
    <dt>PNG bytes</dt><dd>${r.bytes}</dd>
    <dt>Known notes</dt><dd>${r.note}</dd>
  </dl>
  ${
    r.before
      ? `<div class="pair">
      <figure><figcaption>before（RC 冻结 baseline）</figcaption><img src="../../../../tests/visual/consumer.spec.ts-snapshots/${r.before}" alt="${r.name} before" loading="lazy" /></figure>
      <figure><figcaption>after（v0.2.7 craft）</figcaption>${r.valid ? `<img src="${r.name}.png" alt="${r.name} after — VALID" loading="lazy" />` : ""}</figure>
    </div>`
      : `${r.valid ? `<img src="${r.name}.png" alt="${r.name} — VALID" loading="lazy" />` : ""}`
  }
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
<title>PetAccess v0.2.7 Final Product Craft — Human Review Pack</title>
<style>
  body { font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif; margin: 24px auto; max-width: 1200px; padding: 0 16px; color: #1d2733; }
  h1 { font-size: 22px; }
  .card { border: 1px solid #e4e8ec; border-radius: 10px; padding: 16px; margin: 16px 0; }
  .card h2 { margin: 0 0 8px; font-size: 17px; }
  dl { display: grid; grid-template-columns: 120px 1fr; gap: 4px 12px; margin: 8px 0; font-size: 13px; }
  dt { color: #5c6772; } dd { margin: 0; }
  .pair { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; }
  figure { margin: 0; } figcaption { font-size: 12px; color: #5c6772; margin-bottom: 4px; }
  img { width: 100%; border: 1px solid #e4e8ec; border-radius: 8px; }
</style>
</head>
<body>
<h1>PetAccess v0.2.7 Final Product Craft · Human Review Pack（${valid.length} VALID / ${rows.length} total）</h1>
<p>截图必须通过 Capture State Integrity（route/page/state/fixture/h1/entity/count actual=expected）后才保存为 PNG。
metadata JSON 只证明真实页面状态，不宣称视觉通过。等待人工视觉判断（Agent 不代替签字）。</p>
${cards}
<footer>
<p>完整报告：<code>docs/reports/V0207_PRODUCT_CRAFT_FINAL_REPORT.md</code> · 状态：<code>UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW</code></p>
</footer>
</body>
</html>`,
    "utf8",
  );

  const summary = `[human-review-v7] ${project}: ${rows.length} shots, ${valid.length} VALID, ${
    invalid.length
  } INVALID: ${invalid.map((r) => r.name).join(", ") || "none"}`;
  console.log(summary);
  expect(invalid).toHaveLength(0);
});
