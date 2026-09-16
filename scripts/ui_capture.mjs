/**
 * Render the real pages and drop screenshots into `artifacts/ui-capture/`.
 *
 * This is the "actually look at it" half of a UI reality audit: the visual
 * regression suite (`playwright.visual.config.ts`) can only tell you that a
 * page *changed*, never that it looks right. Run this, open the PNGs, judge
 * them, then promote the good ones to baselines.
 *
 * Every shot is taken twice: `-fold` (the first screen, what a user sees
 * before scrolling) and `-full` (the whole page, for layout/overflow bugs).
 * The first screen is the one that decides whether the product reads as
 * finished, so it gets its own frame.
 *
 * Usage:  node scripts/ui_capture.mjs [consumer|admin|all] [viewport...]
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve("artifacts/ui-capture");
const H5 = process.env.H5_URL ?? "http://127.0.0.1:5175";
const ADMIN = process.env.ADMIN_URL ?? "http://127.0.0.1:5173";

const FIXTURE = {
  mall: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e", // conditional
  cafe: "8412b521-5e1c-505d-9dec-568acb860c76", // unknown
};

const VIEWPORTS = {
  360: { width: 360, height: 800 },
  390: { width: 390, height: 844 },
  768: { width: 768, height: 1024 },
  1440: { width: 1440, height: 900 },
};

const which = process.argv[2] ?? "all";
const only = process.argv.slice(3);
const viewports = only.length
  ? Object.fromEntries(Object.entries(VIEWPORTS).filter(([k]) => only.includes(k)))
  : VIEWPORTS;

async function settle(page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  // Pages that fan out to several endpoints keep skeletons up after networkidle
  // has already fired once; screenshotting then produces a picture of a
  // loading state, which is worse than useless in an audit.
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 10000,
    })
    .catch(() => console.log("  [warn] skeletons still present after 10s"));
  await page.waitForTimeout(350);
}

async function snap(page, dir, name) {
  const fold = path.join(dir, `${name}-fold.png`);
  await page.screenshot({ path: fold });
  const full = path.join(dir, `${name}-full.png`);
  await page.screenshot({ path: full, fullPage: true });
  console.log("  ->", path.relative(process.cwd(), fold));
}

async function runConsumer(browser) {
  for (const [vpName, viewport] of Object.entries(viewports)) {
    const dir = path.join(OUT, "consumer", vpName);
    fs.mkdirSync(dir, { recursive: true });
    const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    page.on("console", (m) => {
      if (m.type() === "error")
        console.log(`  [console.error ${vpName}] ${m.text().slice(0, 140)}`);
    });
    page.on("pageerror", (e) => console.log(`  [pageerror ${vpName}] ${String(e).slice(0, 140)}`));
    page.on("response", (r) => {
      if (r.status() >= 400 && r.url().includes("/api/")) {
        console.log(`  [http ${r.status()} ${vpName}] ${r.url().replace(/^https?:\/\/[^/]+/, "")}`);
      }
    });

    const shot = (n) => snap(page, dir, n);
    const go = async (hash) => {
      await page.goto(`${H5}/${hash}`, { waitUntil: "networkidle" });
      await settle(page);
    };

    console.log(`consumer @ ${vpName}`);
    await go("");
    await shot("01-home");

    await go("#/search");
    await shot("02-search");

    // Brand search: the disambiguation case. Two branches of one brand must
    // come back as two labelled rows.
    const searchInput = page.getByTestId("search-input");
    if (await searchInput.count()) {
      await searchInput.fill("星河咖啡");
      await page.getByTestId("search-btn").click();
      await settle(page);
      await shot("02b-search-brand");

      // Alias search: only the former name matches, so the row has to explain
      // why it is here.
      await searchInput.fill("青岚河滨绿地");
      await page.getByTestId("search-btn").click();
      await settle(page);
      await shot("02c-search-alias");
    }

    await go("#/map");
    await shot("03-map");

    await go(`#/place/${FIXTURE.mall}`);
    await shot("04-place-conditional");

    await go(`#/place/${FIXTURE.mall}/why`);
    await shot("05-why");

    await go(`#/place/${FIXTURE.cafe}`);
    await shot("06-place-unknown");

    await go("#/contribute");
    await shot("07-contribute");

    await go("#/mine");
    await shot("08-mine");

    await go("#/pets");
    await shot("09-pets");

    await go("#/settings");
    await shot("10-settings");

    await ctx.close();
  }
}

async function runAdmin(browser) {
  const adminViewports = Object.fromEntries(
    Object.entries(viewports).filter(([k]) => k === "768" || k === "1440"),
  );
  for (const [vpName, viewport] of Object.entries(adminViewports)) {
    const dir = path.join(OUT, "admin", vpName);
    fs.mkdirSync(dir, { recursive: true });
    const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => console.log(`  [pageerror ${vpName}] ${String(e).slice(0, 140)}`));
    page.on("response", (r) => {
      if (r.status() >= 400 && r.url().includes("/api/")) {
        console.log(`  [http ${r.status()} ${vpName}] ${r.url().replace(/^https?:\/\/[^/]+/, "")}`);
      }
    });

    console.log(`admin @ ${vpName}`);
    await page.goto(`${ADMIN}/login`, { waitUntil: "networkidle" });
    await settle(page);
    await snap(page, dir, "00-login");

    // Sign in through the real form so we capture whatever the app does with a
    // credential rather than injecting a token. Admin uses history routes and a
    // bare <button> inside the form — `button[type=submit]` matches nothing.
    await page.fill('input[type="email"]', "admin@demo-petaccess.com");
    await page.fill('input[type="password"]', "admin12345");
    await page.click("form button");
    await page.waitForTimeout(2200);

    const landed = page.url();
    console.log(`  (after login: ${landed})`);
    if (landed.includes("/login")) console.log("  [warn] still on /login — check credentials");

    // Real routes only. There is no /review or /publish page: the review queue
    // is /rule-candidates and publishing is an action on a candidate.
    const routes = [
      ["01-dashboard", "/dashboard"],
      ["02-rule-candidates", "/rule-candidates"],
      ["03-evidence", "/evidence"],
      ["04-sources", "/sources"],
      ["05-regulations", "/regulations"],
      ["06-audit", "/audit"],
      ["07-places", "/places"],
      ["08-conflicts", "/conflicts"],
      ["09-match-debugger", "/match-debugger"],
      ["10-ai-queue", "/ai-queue"],
    ];
    for (const [name, pathname] of routes) {
      await page.goto(`${ADMIN}${pathname}`, { waitUntil: "networkidle" });
      await settle(page);
      await snap(page, dir, name);
    }
    await ctx.close();
  }
}

fs.rmSync(OUT, { recursive: true, force: true });
const browser = await chromium.launch();
try {
  if (which === "all" || which === "consumer") await runConsumer(browser);
  if (which === "all" || which === "admin") await runAdmin(browser);
} finally {
  await browser.close();
}
console.log("done ->", OUT);
