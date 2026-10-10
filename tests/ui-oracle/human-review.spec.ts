/**
 * UI Oracle — human-review.spec.ts (v0.2.4)
 *
 * Captures the named HUMAN_REVIEW screenshots per §47 (evidence artifacts
 * only: fixed viewport, deterministic data, animations disabled). Every shot
 * is gated by Capture State Integrity (O6): navigate → settle → read ACTUAL
 * DOM state (data-ui-page/state/fixture/h1/counts), compare against the
 * shot's `expect`, and only matching shots are written to the package with a
 * `valid: true` metadata file; invalid shots go to `_invalid/` with their
 * mismatch and are excluded from HUMAN_REVIEW_INDEX.html.
 *
 * §51: Reality first-viewport gate — screenshots are captured from page top;
 * the v4 Reality page puts the timeline in the first viewport, so no
 * scrollTo is used to prove the timeline exists.
 *
 * Output: artifacts/blind-ui-productization-v4/HUMAN_REVIEW/<phase>/…
 */
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const OUT = path.resolve("artifacts/blind-ui-productization-v4/HUMAN_REVIEW");
const API = "http://127.0.0.1:8012/api/v1";

interface StateExpect {
  page?: string;
  state?: string;
  fixture?: string;
  h1?: string;
  entityId?: string;
  selectedId?: string;
  count?: number;
  /** Generic data-ui-count key assertions (e.g. contribution choice-count). */
  counts?: Record<string, number>;
}

interface Shot {
  name: string;
  phase: string;
  width: number;
  height: number;
  route: string;
  auth?: boolean;
  emptySearch?: boolean;
  openFilter?: boolean;
  /** Click a testid after settle (e.g. an entry option) before asserting state. */
  clickTestid?: string;
  /** Wait for a testid to appear after the click (form step rendered). */
  waitTestid?: string;
  /** v0.2.4 §15: `?view=` for Place dossier panes. */
  view?: "overview" | "space" | "rules" | "reality" | "evidence";
  expect: StateExpect;
  note: string;
}
const SHOTS: Shot[] = [
  // ---- 1. Search (§47 search: 4) -----------------------------------------
  {
    name: "search_desktop_ready",
    phase: "phase-a-search",
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
    note: "v0.2.4 §11/§12：list-detail；Has a toolbar 结果数|筛选；row 92–108 / 4 semantic lines",
  },
  {
    name: "search_desktop_empty",
    phase: "phase-a-search",
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
    note: "v0.2.4 §14：inline empty，无 card/shadow；右侧 onboarding inline copy",
  },
  {
    name: "search_mobile_ready",
    phase: "phase-a-search",
    width: 430,
    height: 932,
    route: "/#/search",
    expect: {
      page: "search",
      state: "ready",
      fixture: "search-ready-v1",
      h1: "搜索场所规则",
    },
    note: "v0.2.4 §13：single column，rows 88–104 / ≤4 lines，toolbar 结果N|筛选",
  },
  {
    name: "search_mobile_filter",
    phase: "phase-a-search",
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
    note: "v0.2.4 §13：筛选 bottom sheet",
  },

  // ---- 2. Place（§47 place: 5）------------------------------------------
  {
    name: "place_desktop_overview",
    phase: "phase-b-place",
    width: 1440,
    height: 900,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    view: "overview",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.4 §16：Overview 五块（Identity/Decision/Reality/Space/Evidence），不再是无限长页",
  },
  {
    name: "place_desktop_rules",
    phase: "phase-b-place",
    width: 1440,
    height: 900,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e?view=rules",
    view: "rules",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.4 §23：规则 view（当前规则/条件/例外/依据/折叠历史）",
  },
  {
    name: "place_desktop_unknown",
    phase: "phase-b-place",
    width: 1440,
    height: 900,
    route: "/#/place/3b5a341a-e550-5f0c-b35a-319ed43bd840",
    view: "overview",
    expect: {
      page: "place",
      state: "unknown",
      fixture: "place-unknown-v1",
      entityId: "3b5a341a-e550-5f0c-b35a-319ed43bd840",
      h1: "星河咖啡·栖霞分店",
    },
    note: "v0.2.4 §27：UNKNOWN 只渲染有数据的部分，不渲染空 section 全家福",
  },
  {
    name: "place_mobile_overview",
    phase: "phase-b-place",
    width: 430,
    height: 932,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    view: "overview",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.4 §28：首屏 ≤22 lines（Place+tabs+Decision+Reality teaser）",
  },
  {
    name: "place_mobile_rules",
    phase: "phase-b-place",
    width: 430,
    height: 932,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e?view=rules",
    view: "rules",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
      h1: "云栖中心·测试商场",
    },
    note: "v0.2.4 §15 mobile：horizontal scroll text tab；规则 view 折叠历史",
  },

  // ---- 3. Home + Map（§47 home/map: 4）----------------------------------
  {
    name: "home_desktop",
    phase: "phase-c-home-map",
    width: 1440,
    height: 900,
    route: "/#/",
    expect: {
      page: "home",
      state: "ready",
      fixture: "home-ready-v1",
      h1: "去之前，先看规则与现场。",
    },
    note: "v0.2.4 §29：max 960；divider rows，不做大白卡/卡片行",
  },
  {
    name: "home_mobile",
    phase: "phase-c-home-map",
    width: 430,
    height: 932,
    route: "/#/",
    expect: {
      page: "home",
      state: "ready",
      fixture: "home-ready-v1",
      h1: "去之前，先看规则与现场。",
    },
    note: "v0.2.4 §29/§31：mobile 单列 rows + lenses",
  },
  {
    name: "map_desktop",
    phase: "phase-c-home-map",
    width: 1440,
    height: 900,
    route: "/#/map",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.4 §32：desktop List+Map；results divider rows；selected preview 5 项",
  },
  {
    name: "map_mobile_ready",
    phase: "phase-c-home-map",
    width: 430,
    height: 932,
    route: "/#/map",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.4 §33：mobile map，未选中态",
  },
  {
    name: "map_mobile_selected_sheet",
    phase: "phase-c-home-map",
    width: 430,
    height: 932,
    route: "/#/map?place=8412b521-5e1c-505d-9dec-568acb860c76",
    expect: {
      page: "map",
      state: "ready",
      fixture: "map-ready-v1",
      h1: "规则地图",
    },
    note: "v0.2.4 §33：selected place → bottom sheet（tabbar 上方，3–4 行）",
  },

  // ---- 4. Reality（§47 reality: 3）---------------------------------------
  {
    name: "reality_desktop_ready",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/place/8412b521-5e1c-505d-9dec-568acb860c76/reality",
    expect: {
      page: "reality",
      state: "ready",
      fixture: "reality-ready-v1",
      h1: "现场轨迹",
    },
    note: "v0.2.4 §34/§51：timeline 首屏（first event top ≤360），从 page top capture",
  },
  {
    name: "reality_desktop_empty",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e/reality",
    expect: {
      page: "reality",
      state: "empty",
      fixture: "reality-empty-v1",
      h1: "现场轨迹",
    },
    note: "v0.2.4 §36：inline empty，无大卡",
  },
  {
    name: "reality_mobile_ready",
    phase: "phase-d-rest",
    width: 430,
    height: 932,
    route: "/#/place/8412b521-5e1c-505d-9dec-568acb860c76/reality",
    expect: {
      page: "reality",
      state: "ready",
      fixture: "reality-ready-v1",
      h1: "现场轨迹",
    },
    note: "v0.2.4 §34：mobile timeline-first",
  },

  // ---- 5. Evidence（§47 evidence: 3）-------------------------------------
  {
    name: "evidence_desktop_ready",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/place/8412b521-5e1c-505d-9dec-568acb860c76/evidence",
    expect: {
      page: "evidence",
      state: "ready",
      fixture: "evidence-records-v1",
      h1: "证据与来源",
    },
    note: "v0.2.4 §38/§52：record identity + provenance 前 3 步首屏可见",
  },
  {
    name: "evidence_desktop_empty",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e/evidence",
    expect: {
      page: "evidence",
      state: "empty",
      fixture: "evidence-empty-v1",
      h1: "证据与来源",
    },
    note: "v0.2.4 §40：记录存在时不再显示「0 条依据」",
  },
  {
    name: "evidence_mobile_ready",
    phase: "phase-d-rest",
    width: 430,
    height: 932,
    route: "/#/place/8412b521-5e1c-505d-9dec-568acb860c76/evidence",
    expect: {
      page: "evidence",
      state: "ready",
      fixture: "evidence-records-v1",
      h1: "证据与来源",
    },
    note: "v0.2.4 §38：mobile record identity + provenance",
  },

  // ---- 6. Contribution（§47 contribution: 4）-----------------------------
  {
    name: "contribution_desktop_choose-type",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/contribute/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    auth: true,
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
      counts: { "choice-count": 5 },
    },
    note: "v0.2.4 §41：5 choice rows（icon+title+desc+chevron），至少 4 行首屏可见",
  },
  {
    name: "contribution_desktop_step-1",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/contribute/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    auth: true,
    clickTestid: "entry-quick",
    waitTestid: "quick-submit",
    expect: {
      page: "contribution",
      state: "step-1",
      fixture: "contribution-step-1-v1",
      h1: "现场贡献",
    },
    note: "v0.2.4 §43：聚焦步骤（步骤 1/3），一屏一个问题",
  },
  {
    name: "contribution_desktop_step-2",
    phase: "phase-d-rest",
    width: 1440,
    height: 900,
    route: "/#/contribute/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    auth: true,
    clickTestid: "entry-reality-observed_presence",
    waitTestid: "reality-submit",
    expect: {
      page: "contribution",
      state: "step-2",
      fixture: "contribution-step-2-v1",
      h1: "现场贡献",
    },
    note: "v0.2.4 §43：reality 父流程表单（步骤 2/3）",
  },
  {
    name: "contribution_mobile_choose-type",
    phase: "phase-d-rest",
    width: 430,
    height: 932,
    route: "/#/contribute/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    auth: true,
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
      counts: { "choice-count": 5 },
    },
    note: "v0.2.4 §41/§53：mobile 至少 4 choice rows 首屏可见",
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
  const email = `human-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Human Review 探针", email, password: "passw0rd123" },
  });
  expect(reg.ok()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

/** Read the REAL page state from the DOM — never hand-written. (O6) */
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

test("human review v0.2.4 — named screenshots with Capture State Integrity", async ({
  page,
  request,
}, testInfo) => {
  const project = testInfo.project?.name ?? "";
  const isDesktopProject = project === "oracle-desktop";
  const rows: Array<{
    name: string;
    phase: string;
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

    const phaseDir = path.join(OUT, shot.phase);
    mkdirSync(phaseDir, { recursive: true });

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

    // O6: assert the real DOM state BEFORE saving (v0.2.4 §48).
    const actual = await readActualState(page);
    const { ok, mismatches } = assertState(actual, shot.expect);
    const meta = {
      name: shot.name,
      phase: shot.phase,
      viewport: `${shot.width}x${shot.height}`,
      route: shot.route,
      expected: shot.expect,
      actual,
      valid: ok,
      mismatches,
      note: shot.note,
      generatedAt: new Date().toISOString(),
    };

    // §51：从 page top capture（Reality timeline 在首屏，不需 scrollTo）。
    if (ok) {
      const file = path.join(phaseDir, `${shot.name}.png`);
      await page.screenshot({ path: file });
      writeFileSync(
        path.join(phaseDir, `${shot.name}.json`),
        JSON.stringify(meta, null, 2),
        "utf8",
      );
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
    <dt>Phase</dt><dd>${r.phase}</dd>
    <dt>Viewport</dt><dd>${r.viewport}</dd>
    <dt>Route</dt><dd><code>${r.route}</code></dd>
    <dt>State integrity</dt><dd>${r.valid ? "VALID — actual DOM 与 expected 一致" : `INVALID — ${r.mismatches.join("; ")}`}</dd>
    <dt>PNG bytes</dt><dd>${r.bytes}</dd>
    <dt>Known notes</dt><dd>${r.note}</dd>
  </dl>
  ${r.valid ? `<img src="${r.phase}/${r.name}.png" alt="${r.name} — VALID" loading="lazy" />` : ""}
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
<title>PetAccess v0.2.4 — Blind UI Productization Human Review 包</title>
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
  <h1>PetAccess v0.2.4 — Blind UI Productization Human Review 包（${valid.length} VALID / ${rows.length} total）</h1>
  <p>每张截图都先通过 Capture State Integrity（route/page/state/fixture/h1/selected/count 来自真实 DOM），
  valid 才进入本包；Agent 不代替用户做视觉签字。HTML 不做任何美学评价。</p>
  ${cards}
  <p class="status">机器门禁与状态完整性验证详见 docs/reports/BLIND_UI_V4_PRODUCTIZATION_REPORT.md。</p>
</body>
</html>`,
    "utf8",
  );

  expect(invalid, `invalid capture states: ${invalid.map((i) => i.name).join(", ")}`).toHaveLength(
    0,
  );
});
