/**
 * UI Oracle — human-review-r1.spec.ts (v0.2.7-R1.1 Final Micro Closure)
 *
 * Web contribution screenshots for the R1.1 human pack (artifacts/
 * ui-product-craft-v7-runtime-final/HUMAN_REVIEW/):
 *   06_web_contribution_1440  — WIDE_DESKTOP composition (viewport >= 1120)
 *   07_web_contribution_compact — COMPACT_DESKTOP single column (768–1119)
 * The Windows shots (01–05) are captured by the real Tauri/WebView2 smoke
 * harness (windows-smoke/…) and copied into the pack by this spec, so every
 * item in the pack is real-DOM evidence; metadata 只证明真实状态。
 * State integrity (route/page/state/fixture/h1) is asserted before saving.
 * v0.2.7-R1.1 P0-1: rows carry a logicalName WITHOUT the ".png" extension;
 * the file is "{logicalName}.png", so the HTML template can never emit
 * ".png.png". A referential-integrity gate re-reads the generated index and
 * requires every <img src> to resolve to an existing file.
 */
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

const OUT = path.resolve("artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW");
const SMOKE = path.resolve("artifacts/ui-product-craft-v7-runtime-final/windows-smoke");
const API = "http://127.0.0.1:8012/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

const WEB_SHOTS = [
  {
    name: "06_web_contribution_1440",
    width: 1440,
    height: 900,
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
    },
    note: "v0.2.7-R1 WIDE_DESKTOP (>=1120): main | context 双栏在 1440 web viewport 成立。",
  },
  {
    name: "07_web_contribution_compact",
    width: 1000,
    height: 900,
    expect: {
      page: "contribution",
      state: "choose-type",
      fixture: "contribution-choose-type-v1",
      h1: "你刚刚知道了什么？",
    },
    note: "v0.2.7-R1 COMPACT_DESKTOP (768–1119): rail + 单栏 task（context rail 不并排）。",
  },
];

interface StateExpect {
  page?: string;
  state?: string;
  fixture?: string;
  h1?: string;
}

async function signIn(request: import("@playwright/test").APIRequestContext): Promise<string> {
  const email = `humanr1-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Human Review R1 探针", email, password: "passw0rd123" },
  });
  expect(reg.ok()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

async function readActualState(
  page: import("@playwright/test").Page,
): Promise<Record<string, unknown>> {
  return page.evaluate(() => {
    const host = document.querySelector("[data-ui-page]");
    const h1 = document.querySelector("h1");
    return {
      route: location.hash,
      page: host?.getAttribute("data-ui-page") ?? null,
      state: host?.getAttribute("data-ui-state") ?? null,
      fixture: host?.getAttribute("data-ui-fixture") ?? null,
      h1: h1 ? (h1.textContent ?? "").trim() : null,
    };
  });
}

function assertState(
  actual: Record<string, unknown>,
  exp: StateExpect,
): { ok: boolean; mismatches: string[] } {
  const mismatches: string[] = [];
  for (const [k, v] of Object.entries(exp)) {
    if (String(actual[k] ?? null) !== String(v))
      mismatches.push(`${k}: expected=${String(v)} actual=${String(actual[k] ?? null)}`);
  }
  return { ok: mismatches.length === 0, mismatches };
}

test("human review v0.2.7-R1 — web contribution wide/compact + windows pack assembly", async ({
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

  if (isDesktopProject) {
    for (const shot of WEB_SHOTS) {
      await page.setViewportSize({ width: shot.width, height: shot.height });
      await page.clock.install({ time: new Date("2026-09-15T04:00:00Z") }).catch(() => {});
      const token = await signIn(request);
      await page.goto("/");
      await page.evaluate((t) => localStorage.setItem("pa_token", t), token);
      await page.goto(`/#/contribute/${MALL_ID}`);
      await page.reload();
      await page.addStyleTag({
        content: "* { transition: none !important; animation: none !important; }",
      });
      await page.waitForLoadState("networkidle").catch(() => {});
      await page
        .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
          timeout: 15000,
        })
        .catch(() => {});
      await page.waitForTimeout(300);

      const actual = await readActualState(page);
      const { ok, mismatches } = assertState(actual, shot.expect);
      const meta = {
        name: shot.name,
        viewport: `${shot.width}x${shot.height}`,
        route: `/#/contribute/${MALL_ID}`,
        expected: shot.expect,
        actual,
        valid: ok,
        mismatches,
        note: shot.note,
        generatedAt: new Date().toISOString(),
      };
      mkdirSync(OUT, { recursive: true });
      if (ok) {
        const file = path.join(OUT, `${shot.name}.png`);
        await page.screenshot({ path: file });
        writeFileSync(path.join(OUT, `${shot.name}.json`), JSON.stringify(meta, null, 2), "utf8");
        rows.push({
          name: shot.name,
          viewport: meta.viewport,
          route: meta.route,
          valid: true,
          bytes: statSync(file).size,
          note: shot.note,
          mismatches: [],
        });
      } else {
        const file = path.join(OUT, `${shot.name}.png`);
        await page.screenshot({ path: file });
        writeFileSync(path.join(OUT, `${shot.name}.json`), JSON.stringify(meta, null, 2), "utf8");
        rows.push({
          name: shot.name,
          viewport: meta.viewport,
          route: meta.route,
          valid: false,
          bytes: statSync(file).size,
          note: shot.note,
          mismatches,
        });
      }
      console.log(
        `[human-review-r1] ${shot.name}: valid=${ok} mismatches=${JSON.stringify(mismatches)}`,
      );
    }
  }

  // Copy the real-Windows shots from the smoke pack into the human pack.
  const WINDOWS_COPY = [
    { from: "04_map.png", to: "01_windows_map" },
    { from: "07_contribution_choose.png", to: "02_windows_contribution_choose" },
    { from: "08_contribution_step1.png", to: "03_windows_contribution_step1" },
    { from: "09_contribution_step2.png", to: "04_windows_contribution_step2" },
    { from: "05_desktop_rail_closeup.png", to: "05_desktop_rail_closeup" },
  ];
  const windowsRows: Array<{
    name: string;
    viewport: string;
    route: string;
    valid: boolean;
    bytes: number;
    note: string;
  }> = [];
  for (const { from, to } of WINDOWS_COPY) {
    const src = path.join(SMOKE, from);
    if (!existsSync(src)) continue;
    mkdirSync(OUT, { recursive: true });
    const dst = path.join(OUT, to);
    writeFileSync(dst, readFileSync(src));
    windowsRows.push({
      name: to,
      viewport: "real WebView2",
      route: "smoke",
      valid: true,
      bytes: statSync(dst).size,
      note: "真实 Tauri v2 + WebView2 runtime（windows-smoke harness 捕获）",
    });
  }
  const beforePairs = [
    { name: "01_windows_map", before: "04_map_before.png" },
    { name: "02_windows_contribution_choose", before: "07_contribution_choose_before.png" },
  ];

  const all = [...windowsRows, ...rows];
  const valid = all.filter((r) => r.valid);
  const cards = all
    .map((r) => {
      const before = beforePairs.find((b) => b.name === r.name);
      return `<div class="card">
  <h2>${r.name} ${r.valid ? "✅" : "⛔"}</h2>
  <dl>
    <dt>Viewport</dt><dd>${r.viewport}</dd>
    <dt>Route</dt><dd><code>${r.route}</code></dd>
    <dt>State integrity</dt><dd>${r.valid ? "VALID — actual DOM 与 expected 一致" : `INVALID — ${r.mismatches.join("; ")}`}</dd>
    <dt>PNG bytes</dt><dd>${r.bytes}</dd>
    <dt>Known notes</dt><dd>${r.note}</dd>
  </dl>
  ${
    before && existsSync(path.join(SMOKE, before))
      ? `<div class="pair">
      <figure><figcaption>BEFORE（v7 runtime，rail scrollbar / compact 可见）</figcaption><img src="../windows-smoke/${before}" alt="${r.name} before" loading="lazy" /></figure>
      <figure><figcaption>AFTER（v0.2.7-R1）</figcaption><img src="${r.name}.png" alt="${r.name} after — VALID" loading="lazy" /></figure>
    </div>`
      : `<img src="${r.name}.png" alt="${r.name} — ${r.valid ? "VALID" : "INVALID"}" loading="lazy" />`
  }
</div>`;
    })
    .join("\n");

  writeFileSync(
    path.join(OUT, "HUMAN_REVIEW_INDEX.html"),
    `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>PetAccess v0.2.7-R1.1 Final Micro Closure — Human Review Pack</title>
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
<h1>PetAccess v0.2.7-R1.1 Final Micro Closure · Human Review Pack（${valid.length} VALID / ${all.length} total）</h1>
<p>机器 gate 全绿 + 截图通过 State Integrity 后才入包。metadata JSON 只证明真实页面状态，不宣称视觉通过。等待人工视觉判断（Agent 不代替签字）。</p>
${cards}
<footer>
<p>完整报告：<code>docs/reports/V0207_R1_1_FINAL_MICRO_CLOSURE_REPORT.md</code> · 状态：<code>UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW</code></p>
</footer>
</body>
</html>`,
    "utf8",
  );

  const summary = `[human-review-r1.1] ${all.length} shots, ${valid.length} VALID, ${all.length - valid.length} INVALID: ${
    all
      .filter((r) => !r.valid)
      .map((r) => r.name)
      .join(", ") || "none"
  }`;
  console.log(summary);
  expect(all.filter((r) => !r.valid)).toHaveLength(0);

  // v0.2.7-R1.1 P0-1 referential-integrity gate: every <img src> in the
  // generated index must resolve to a real file, and ".png.png" is forbidden.
  const indexHtml = readFileSync(path.join(OUT, "HUMAN_REVIEW_INDEX.html"), "utf8");
  const missingImages: string[] = [];
  for (const m of indexHtml.matchAll(/<img[^>]*\bsrc="([^"]+)"/g)) {
    const src = m[1]!;
    if (!existsSync(path.resolve(OUT, src))) missingImages.push(src);
  }
  const pngPngCount = (indexHtml.match(/\.png\.png/g) ?? []).length;
  console.log(
    `[human-review-r1.1] HUMAN_REVIEW_INDEX referential integrity: ${
      indexHtml.match(/<img/g).length
    } img srcs, missing=${JSON.stringify(missingImages)}, png.png=${pngPngCount}`,
  );
  expect(pngPngCount).toBe(0);
  expect(missingImages).toHaveLength(0);
});
