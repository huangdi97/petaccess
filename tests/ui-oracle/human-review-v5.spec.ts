/**
 * UI Oracle — human-review-v5.spec.ts (v0.2.5 Human Visual Closure, §42–44)
 *
 * Named HUMAN_REVIEW screenshots for the v5 human visual acceptance candidate.
 * Same engine as the v0.2.4 pack: fixed viewport, deterministic clock,
 * motion frozen, every shot gated by Capture State Integrity (O6) — the ACTUAL
 * DOM state (data-ui-page/state/fixture/h1/entity/selected/count) is read from
 * the page and must match the shot's `expect` before the PNG is written.
 * metadata 只证明真实状态，不宣称视觉通过；Agent 不代替用户做视觉签字。
 *
 * §42 list (~27 curated shots, 1440×900 / 430×932, viewport capture):
 * search(4): desktop ready/empty, mobile ready/filter
 * place(5): desktop overview/rules/unknown, mobile overview/rules
 * home(2): desktop/mobile
 * map(4): desktop, mobile ready, mobile selected half, mobile selected expanded
 * reality(3): desktop ready/empty, mobile ready
 * evidence(3): desktop ready/empty, mobile ready
 * contribution(6): desktop choose/step1/step2/done, mobile choose/step1
 *
 * Output: artifacts/ui-human-closure-v5/HUMAN_REVIEW/…
 */
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const OUT = path.resolve("artifacts/ui-human-closure-v5/HUMAN_REVIEW");
const API = "http://127.0.0.1:8012/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e"; // ready fixture
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76"; // reality/evidence fixture
const BRANCH_ID = "3b5a341a-e550-5f0c-b35a-319ed43bd840"; // unknown fixture

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
  emptySearch?: boolean;
  openFilter?: boolean;
  clickTestid?: string;
  waitTestid?: string;
  /** Submit a reality contribution (entry-reality → fill date → submit) for the done shot. */
  submitReality?: boolean;
  expect: StateExpect;
  note: string;
}

const SHOTS: Shot[] = [
  // ---- 1. Search (§42: 4) -------------------------------------------------
  {
    name: "search_desktop_ready",
    width: 1440,
    height: 900,
    route: "/#/search",
    expect: {
      page: "search",
      state: "ready-selected",
      fixture: "search-ready-v1",
      h1: "搜索场所规则",
      selectedId: "search-selected-row",
    },
    note: "v0.2.5 §17/§19：list-detail；toolbar 结果N|筛选；selected tint 轻、status 不抢 Place Name",
  },
  {
    name: "search_desktop_empty",
    width: 1440,
    height: 900,
    route: "/#/search",
    emptySearch: true,
    expect: {
      page: "search",
      state: "empty",
      fixture: "search-empty-v1",
      h1: "搜索场所规则",
    },
    note: "v0.2.5 §18：仅左侧一个 primary「提交场所线索」，右侧纯 onboarding 文案",
  },
  {
    name: "search_mobile_ready",
    width: 430,
    height: 932,
    route: "/#/search",
    expect: {
      page: "search",
      state: "ready",
      fixture: "search-ready-v1",
      h1: "搜索场所规则",
    },
    note: "v0.2.5 §19：单列，≤4 semantic lines/row，toolbar 结果N|筛选",
  },
  {
    name: "search_mobile_filter",
    width: 430,
    height: 932,
    route: "/#/search",
    openFilter: true,
    expect: {
      page: "search",
      state: "filter",
      fixture: "search-filter-v1",
      h1: "搜索场所规则",
    },
    note: "v0.2.5 §19：Filter 非独立大按钮（toolbar 内）",
  },

  // ---- 2. Place (§42: 5) --------------------------------------------------
  {
    name: "place_desktop_overview",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}`,
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: MALL_ID,
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.5 §10/§11：main column 820；Identity/Decision/Reality/Space/Evidence",
  },
  {
    name: "place_desktop_rules",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}?view=rules`,
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: MALL_ID,
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.5 §12–14：Rule Groups 带回文章节（contextLabel/subjectAction/status/condition/source）",
  },
  {
    name: "place_desktop_unknown",
    width: 1440,
    height: 900,
    route: `/#/place/${BRANCH_ID}`,
    expect: {
      page: "place",
      state: "unknown",
      fixture: "place-unknown-v1",
      entityId: BRANCH_ID,
      h1: "星河咖啡·栖霞分店",
    },
    note: "v0.2.5 §15：Unknown Overview 最小化；自然语言 copy，无工程不变量",
  },
  {
    name: "place_mobile_overview",
    width: 430,
    height: 932,
    route: `/#/place/${MALL_ID}`,
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: MALL_ID,
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.5 §11/§28：Space/Evidence summary row 在首屏，不再大片空白",
  },
  {
    name: "place_mobile_rules",
    width: 430,
    height: 932,
    route: `/#/place/${MALL_ID}?view=rules`,
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: MALL_ID,
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.5 §12：mobile rule groups，divider 而非 card wall",
  },

  // ---- 3. Home (§42: 2) ---------------------------------------------------
  {
    name: "home_desktop",
    width: 1440,
    height: 900,
    route: "/#/",
    expect: {
      page: "home",
      state: "ready",
      fixture: "home-ready-v1",
      h1: "去之前，先看看这里的规则和现场。",
    },
    note: "v0.2.5 §20/§21：附近已有依据 / 附近待补充 consumer copy",
  },
  {
    name: "home_mobile",
    width: 430,
    height: 932,
    route: "/#/",
    expect: {
      page: "home",
      state: "ready",
      fixture: "home-ready-v1",
      h1: "去之前，先看看这里的规则和现场。",
    },
    note: "v0.2.5 §20：mobile 单列 rows",
  },

  // ---- 4. Map (§42: 4) ---------------------------------------------------
  {
    name: "map_desktop",
    width: 1440,
    height: 900,
    route: "/#/map",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.5 §22：desktop List+Map；selected preview",
  },
  {
    name: "map_mobile_ready",
    width: 430,
    height: 932,
    route: "/#/map",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.5 §22/§25：mobile map 填满视口；segmented 地图|列表",
  },
  {
    name: "map_mobile_selected_half",
    width: 430,
    height: 932,
    route: `/#/map?place=${CAFE_ID}`,
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.5 §23/§24：half 态 bottom sheet（drag handle+名称+状态+类型·距离+关键条件+最近现场+查看场所 →）",
  },
  {
    name: "map_mobile_selected_expanded",
    width: 430,
    height: 932,
    route: `/#/map?place=${CAFE_ID}`,
    clickTestid: "sheet-handle",
    waitTestid: "map-mobile-sheet",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.5 §23：expanded 态（drag handle 点击展开）",
  },

  // ---- 5. Reality (§42: 3) ------------------------------------------------
  {
    name: "reality_desktop_ready",
    width: 1440,
    height: 900,
    route: `/#/place/${CAFE_ID}/reality`,
    expect: {
      page: "reality",
      state: "ready",
      fixture: "reality-ready-v1",
      h1: "现场轨迹",
    },
    note: "v0.2.5 §35：timeline 首屏；Date=metadata、Time=strong、Fact=body strong、待核验=小号 muted",
  },
  {
    name: "reality_mobile_ready",
    width: 430,
    height: 932,
    route: `/#/place/${CAFE_ID}/reality`,
    expect: {
      page: "reality",
      state: "ready",
      fixture: "reality-ready-v1",
      h1: "现场轨迹",
    },
    note: "v0.2.5 §35：mobile timeline-first",
  },
  {
    name: "reality_desktop_empty",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}/reality`,
    expect: {
      page: "reality",
      state: "empty",
      fixture: "reality-empty-v1",
      h1: "现场轨迹",
    },
    note: "v0.2.5 §35：inline empty",
  },

  // ---- 6. Evidence (§42: 3) ----------------------------------------------
  {
    name: "evidence_desktop_ready",
    width: 1440,
    height: 900,
    route: `/#/place/${CAFE_ID}/evidence`,
    expect: {
      page: "evidence",
      state: "ready",
      fixture: "evidence-records-v1",
      h1: "证据与来源",
    },
    note: "v0.2.5 §36：record identity 更强；2 条现场记录·8 个来源·3 个待核验 层级明确",
  },
  {
    name: "evidence_mobile_ready",
    width: 430,
    height: 932,
    route: `/#/place/${CAFE_ID}/evidence`,
    expect: {
      page: "evidence",
      state: "ready",
      fixture: "evidence-records-v1",
      h1: "证据与来源",
    },
    note: "v0.2.5 §36：mobile record identity + provenance",
  },
  {
    name: "evidence_desktop_empty",
    width: 1440,
    height: 900,
    route: `/#/place/${MALL_ID}/evidence`,
    expect: {
      page: "evidence",
      state: "empty",
      fixture: "evidence-empty-v1",
      h1: "证据与来源",
    },
    note: "v0.2.5 §36：inline empty",
  },

  // ---- 7. Contribution (§42: 6) ------------------------------------------
  {
    name: "contribution_desktop_choose",
    width: 1440,
    height: 900,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
      counts: { "choice-count": 5 },
    },
    note: "v0.2.5 §28/§31：5 option rows；提交内容会进入人工核验",
  },
  {
    name: "contribution_desktop_step1",
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
    note: "v0.2.5 §29–32：ContributionStepShell（place context + progress + title/desc + footer）+ radio option rows",
  },
  {
    name: "contribution_desktop_step2",
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
    note: "v0.2.5 §33：reality 表单按真实字段 cluster（什么时候/在哪里/你看到了什么）",
  },
  {
    name: "contribution_desktop_done",
    width: 1440,
    height: 900,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-observed_presence",
    waitTestid: "reality-submit",
    submitReality: true,
    expect: {
      page: "contribution",
      state: "done",
      fixture: "contribution-done-v1",
      h1: "现场贡献",
    },
    note: "v0.2.5 §34：已提交待核验 · 感谢提供事实记录…查看我的贡献 →/返回场所 →",
  },
  {
    name: "contribution_mobile_choose",
    width: 430,
    height: 932,
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
      counts: { "choice-count": 5 },
    },
    note: "v0.2.5 §28：mobile 5 option rows",
  },
  {
    name: "contribution_mobile_step1",
    width: 430,
    height: 932,
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
    note: "v0.2.5 §29–32：mobile step shell，min-height 440–520",
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
  const email = `human5-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Human Review v5 探针", email, password: "passw0rd123" },
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
    const entityEl = document.querySelector("[data-ui-entity-id]");
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
      entityId: entityEl?.getAttribute("data-ui-entity-id") ?? null,
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

test("human review v0.2.5 — named screenshots with Capture State Integrity", async ({
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
  }> = [];

  for (const shot of SHOTS) {
    const wantDesktop = shot.width >= 1000;
    if (wantDesktop !== isDesktopProject) continue;

    mkdirSync(OUT, { recursive: true });

    await page.setViewportSize({ width: shot.width, height: shot.height });
    await page.clock.install({ time: new Date("2026-09-15T04:00:00Z") }).catch(() => {});

    if (shot.emptySearch) {
      await page.route("**/api/v1/places?**", (route) =>
        route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
      );
    }
    if (shot.auth) {
      const token = await signIn(request);
      await page.goto("/");
      await page.evaluate((t) => localStorage.setItem("pa_token", t), token);
    }
    await page.goto(shot.route);
    await page.reload();
    await freezeMotion(page);
    await settle(page);
    if (shot.emptySearch) {
      await page.getByTestId("search-input").fill("不存在的场所zzz");
      await page.getByTestId("search-btn").click();
      await settle(page);
    }

    if (shot.openFilter) {
      await page.getByTestId("filter-toggle").click();
      await page.waitForSelector("[data-ui='search-filter-sheet']").catch(() => {});
      await page.waitForTimeout(300);
    }

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

    if (shot.submitReality) {
      await page.getByTestId("reality-date").fill("2026-09-20");
      await page.getByTestId("reality-submit").click();
      await page
        .waitForSelector("[data-testid='contribute-result']", { timeout: 15000 })
        .catch(() => {});
      await settle(page);
    }

    // O6: assert the real DOM state BEFORE saving (§43).
    const actual = await readActualState(page);
    const { ok, mismatches } = assertState(actual, shot.expect);
    const meta = {
      name: shot.name,
      viewport: `${shot.width}x${shot.height}`,
      route: shot.route,
      expected: shot.expect,
      actual,
      valid: ok,
      mismatches,
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
  ${r.valid ? `<img src="${r.name}.png" alt="${r.name} — VALID" loading="lazy" />` : ""}
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
<title>PetAccess v0.2.5 — Human Visual Closure Review 候选包</title>
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
  <h1>PetAccess v0.2.5 — Human Visual Closure Review 候选包（${valid.length} VALID / ${rows.length} total）</h1>
  <p>每张截图都先通过 Capture State Integrity（route/page/state/fixture/h1/entity/selected/count 来自真实 DOM），
  valid 才进入本包；metadata 只证明真实状态，不宣称视觉通过；Agent 不代替用户做视觉签字。</p>
  ${cards}
  <p class="status">机器门禁与状态完整性验证详见 docs/reports/UI_HUMAN_CLOSURE_V5_REPORT.md。</p>
</body>
</html>`,
    "utf8",
  );

  expect(invalid, `invalid capture states: ${invalid.map((i) => i.name).join(", ")}`).toHaveLength(
    0,
  );
});
