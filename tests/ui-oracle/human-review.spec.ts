/**
 * UI Oracle — human-review.spec.ts (v0.2.3)
 *
 * Captures the named HUMAN_REVIEW screenshots per phase (evidence artifacts
 * only: fixed viewport, deterministic data, animations disabled, clock
 * frozen). Every shot is gated by Capture State Integrity (v0.2.3 §14):
 *
 *   - navigate → settle → read ACTUAL page state from the DOM
 *     (data-ui-page / data-ui-state / data-ui-fixture / h1 / counts),
 *     never from test intent;
 *   - compare against the shot's `expect` contract;
 *   - only shots where every expected field matches are written to the
 *     human-review package with a `valid: true` metadata file; invalid shots
 *     are still written to a `_invalid` folder with their mismatch so the
 *     failure is visible, but are excluded from HUMAN_REVIEW_INDEX.html.
 *
 * Output: artifacts/blind-ui-compiler-v2/HUMAN_REVIEW/<phase>/…
 */
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const OUT = path.resolve("artifacts/blind-ui-compiler-v2/HUMAN_REVIEW");
const API = "http://127.0.0.1:8012/api/v1";

interface StateExpect {
  page?: string;
  state?: string;
  fixture?: string;
  h1?: string;
  entityId?: string;
  selectedId?: string;
  count?: number;
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
  expect: StateExpect;
  note: string;
}

const SHOTS: Shot[] = [
  // ---- Phase A: Search -------------------------------------------------
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
    note: "桌面：Rail 68 / Topbar 60 / Results 400 全出血 + Detail 704 内容列",
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
    note: "空态只存在于 ResultsPane；右侧 onboarding copy（§23）",
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
    note: "移动单列：row 108–128、radius 0、≤5 行文本（§24）",
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
    note: "筛选 bottom sheet：top 340–480、radius 16、5 rows（§25）",
  },

  // ---- Phase B: Place ---------------------------------------------------
  {
    name: "place_desktop_ready",
    phase: "phase-b-place",
    width: 1440,
    height: 900,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
      h1: "云栖中心·测试商场",
    },
    note: "Dossier x≈100 w∈820–860 + Inspector x≈1010 w∈320–350 sticky（§27）",
  },
  {
    name: "place_desktop_unknown",
    phase: "phase-b-place",
    width: 1440,
    height: 900,
    route: "/#/place/3b5a341a-e550-5f0c-b35a-319ed43bd840",
    expect: {
      page: "place",
      state: "unknown",
      fixture: "place-unknown-v1",
      entityId: "3b5a341a-e550-5f0c-b35a-319ed43bd840",
      h1: "星河咖啡·栖霞分店",
    },
    note: "无已发布结论 → UNKNOWN 诚实态（未知 ≠ 允许）",
  },
  {
    name: "place_mobile_ready",
    phase: "phase-b-place",
    width: 430,
    height: 932,
    route: "/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
    expect: {
      page: "place",
      state: "ready",
      fixture: "place-ready-v1",
      entityId: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
      h1: "云栖中心·测试商场",
    },
    note: "移动单列：首屏 name/query/decision/1 condition/Reality teaser（§34）",
  },

  // ---- Phase C: Home + Map ---------------------------------------------
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
      h1: "去之前，先看看这里的规则和现场。",
    },
    note: "Task Launcher：location → query → search → recent/nearby → lens（§36）",
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
    note: "Spatial workspace：rail + 400 result pane + full map + 筛选 N（§37）",
  },
];

async function freezeMotion(page: import("@playwright/test").Page): Promise<void> {
  await page.addStyleTag({ content: "* { transition: none !important; animation: none !important; }" });
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
  const login = await request.post(`${API}/auth/login`, { data: { email, password: "passw0rd123" } });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

/** Read the REAL page state from the DOM — never hand-written. (v0.2.3 §15) */
async function readActualState(
  page: import("@playwright/test").Page,
): Promise<Record<string, unknown>> {
  return page.evaluate(() => {
    const host = document.querySelector("[data-ui-page]");
    const h1 = document.querySelector("h1");
    const countEl = document.querySelector("[data-ui-count='result-rows']");
    const selected = document.querySelector("[data-ui*='selected']");
    const entityEl = document.querySelector("[data-ui-entity-id]");
    return {
      route: location.hash,
      page: host?.getAttribute("data-ui-page") ?? null,
      state: host?.getAttribute("data-ui-state") ?? null,
      fixture: host?.getAttribute("data-ui-fixture") ?? null,
      h1: h1 ? (h1.textContent ?? "").trim() : null,
      entityId: entityEl?.getAttribute("data-ui-entity-id") ?? null,
      selectedId: selected?.getAttribute("data-ui") ?? null,
      count: countEl ? Number(countEl.textContent ?? NaN) || null : null,
    };
  });
}

function assertState(
  actual: Record<string, unknown>,
  expect: StateExpect,
): { ok: boolean; mismatches: string[] } {
  const mismatches: string[] = [];
  const check = (key: string, exp: unknown): void => {
    if (exp === undefined) return;
    if (String(actual[key]) !== String(exp)) {
      mismatches.push(`${key}: expected=${String(exp)} actual=${String(actual[key])}`);
    }
  };
  check("page", expect.page);
  check("state", expect.state);
  check("fixture", expect.fixture);
  check("h1", expect.h1);
  check("entityId", expect.entityId);
  check("selectedId", expect.selectedId);
  check("count", expect.count);
  return { ok: mismatches.length === 0, mismatches };
}

test("human review v0.2.3 — named screenshots with Capture State Integrity", async (
  { page, request },
  testInfo,
) => {
  const project = testInfo.project.name;
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
    // Each shot renders in exactly one project (desktop shots under
    // oracle-desktop, mobile shots under oracle-mobile) so viewport and
    // touch behaviour match the shot's contract.
    const wantDesktop = shot.width >= 1000;
    if (wantDesktop !== isDesktopProject) continue;

    const phaseDir = path.join(OUT, shot.phase);
    mkdirSync(phaseDir, { recursive: true });

    await page.setViewportSize({ width: shot.width, height: shot.height });
    // Clock frozen BEFORE navigation so relative timestamps are deterministic.
    await page.clock.install({ time: new Date("2026-09-15T04:00:00Z") }).catch(() => {});

    // Fresh SPA boot per shot: navigate to the shot's own route, then reload
    // so the app reboots directly at that URL with zero leaked selection or
    // route state from a previous shot (O6 honesty). Route mocks persist
    // across reloads, so emptySearch interception still applies.
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

    // O6: assert the real DOM state BEFORE saving (v0.2.3 §14).
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
      // Invalid shots: keep the evidence for debugging, but NOT in the index.
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
<title>PetAccess v0.2.3 — Blind UI Compiler Human Review 包</title>
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
  <h1>PetAccess v0.2.3 — Blind UI Compiler Human Review 包（${valid.length} VALID / ${rows.length} total）</h1>
  <p>每张截图都先通过 Capture State Integrity（route/page/state/fixture/h1/selected/count 来自真实 DOM），
  valid 才进入本包；Agent 不代替用户做视觉签字。HTML 不做任何美学评价。</p>
  ${cards}
  <p class="status">机器门禁与状态完整性验证详见 docs/reports/BLIND_UI_V2_FINAL_REPORT.md。</p>
</body>
</html>`,
    "utf8",
  );

  // The test itself fails when any shot was invalid — the package must be
  // trustworthy or visibly incomplete.
  expect(invalid, `invalid capture states: ${invalid.map((i) => i.name).join(", ")}`).toHaveLength(0);
});
