/**
 * Automated accessibility audit over the real pages.
 *
 * Scope, stated up front because "a11y PASS" without a scope is a claim nobody
 * can check: this covers what a machine can decide — names, labels, heading
 * structure, focus visibility and order, target size, colour-only encoding,
 * reduced-motion support. It cannot decide whether the wording makes sense to a
 * screen-reader user, and it does not attempt to.
 *
 * axe-core is not a dependency here on purpose: it is not installed in this
 * repository, and an audit that only runs when someone remembers to install a
 * tool is not a gate. Everything below is plain DOM + keyboard.
 *
 * Usage: node scripts/a11y_audit.mjs [--json out.json]
 */
import fs from "node:fs";
import path from "node:path";

import { chromium } from "playwright";

const H5 = process.env.H5_URL ?? "http://127.0.0.1:5175";
const ADMIN = process.env.ADMIN_URL ?? "http://127.0.0.1:5173";

const FIXTURE = {
  mall: "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e",
  cafe: "8412b521-5e1c-505d-9dec-568acb860c76",
};

const CONSUMER_PAGES = [
  ["home", ""],
  ["search", "#/search"],
  ["map", "#/map"],
  ["place-conditional", `#/place/${FIXTURE.mall}`],
  ["why", `#/place/${FIXTURE.mall}/why`],
  ["place-unknown", `#/place/${FIXTURE.cafe}`],
  ["contribute", "#/contribute"],
  ["mine", "#/mine"],
  ["pets", "#/pets"],
  ["settings", "#/settings"],
  ["boundary", "#/boundary"],
  ["privacy", "#/privacy"],
];

/**
 * Admin routes are history-mode, not hash-mode, and there is no `/review` or
 * `/publish` path — the review queue is `/rule-candidates`, and publishing is
 * an action on a candidate rather than a page of its own. An earlier pass of
 * this audit used invented hash routes, so every "admin page" was really the
 * login screen audited seven times.
 */
const ADMIN_PAGES = [
  ["login", "/login"],
  ["dashboard", "/dashboard"],
  ["rule-candidates", "/rule-candidates"],
  ["evidence", "/evidence"],
  ["sources", "/sources"],
  ["regulations", "/regulations"],
  ["audit", "/audit"],
  ["places", "/places"],
  ["conflicts", "/conflicts"],
  ["match-debugger", "/match-debugger"],
];

/** Injected into the page: pure DOM checks, no library. */
const AUDIT = () => {
  const out = { issues: [], stats: {} };
  const add = (rule, severity, detail, selector) =>
    out.issues.push({ rule, severity, detail, selector: selector ?? null });

  const isVisible = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    const s = getComputedStyle(el);
    return s.visibility !== "hidden" && s.display !== "none" && s.opacity !== "0";
  };

  const accessibleName = (el) => {
    const aria = el.getAttribute("aria-label");
    if (aria && aria.trim()) return aria.trim();
    const labelledby = el.getAttribute("aria-labelledby");
    if (labelledby) {
      const text = labelledby
        .split(/\s+/)
        .map((id) => document.getElementById(id)?.textContent ?? "")
        .join(" ")
        .trim();
      if (text) return text;
    }
    if (el.tagName === "INPUT" || el.tagName === "SELECT" || el.tagName === "TEXTAREA") {
      if (el.id) {
        const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
        if (label?.textContent?.trim()) return label.textContent.trim();
      }
      const wrapping = el.closest("label");
      if (wrapping?.textContent?.trim()) return wrapping.textContent.trim();
      const title = el.getAttribute("title");
      if (title && title.trim()) return title.trim();
      const placeholder = el.getAttribute("placeholder");
      // A placeholder is a weak name (it vanishes on input) but it is a name;
      // reported at info level rather than as a violation.
      if (placeholder && placeholder.trim()) return `[placeholder] ${placeholder.trim()}`;
    }
    const text = (el.innerText ?? el.textContent ?? "").trim();
    if (text) return text;
    const img = el.querySelector?.("img[alt]");
    if (img?.getAttribute("alt")?.trim()) return img.getAttribute("alt").trim();
    return "";
  };

  const describe = (el) => {
    const id = el.id ? `#${el.id}` : "";
    const cls =
      el.className && typeof el.className === "string" ? `.${el.className.split(/\s+/)[0]}` : "";
    const t = (el.innerText ?? "").trim().slice(0, 24);
    return `${el.tagName.toLowerCase()}${id}${cls}${t ? ` "${t}"` : ""}`;
  };

  // 1. document language
  const lang = document.documentElement.getAttribute("lang");
  if (!lang) add("html-lang", "serious", "<html> has no lang attribute", "html");

  // 2. headings
  const headings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].filter(isVisible);
  const h1s = headings.filter((h) => h.tagName === "H1");
  out.stats.headings = headings.length;
  if (h1s.length === 0) add("heading-h1", "serious", "no visible <h1> on the page");
  if (h1s.length > 1)
    add("heading-h1", "moderate", `${h1s.length} visible <h1> elements`, describe(h1s[0]));
  let prev = 0;
  for (const h of headings) {
    const level = Number(h.tagName[1]);
    if (prev && level > prev + 1) {
      add("heading-order", "moderate", `heading level jumps ${prev} -> ${level}`, describe(h));
    }
    prev = level;
  }

  // 3. accessible names on interactive elements
  const interactive = [
    ...document.querySelectorAll(
      'button, a[href], input:not([type="hidden"]), select, textarea, [role="button"], [role="tab"], [role="link"]',
    ),
  ].filter(isVisible);
  out.stats.interactive = interactive.length;
  for (const el of interactive) {
    const name = accessibleName(el);
    if (!name)
      add("control-name", "serious", "interactive element has no accessible name", describe(el));
    else if (name.startsWith("[placeholder]"))
      add("control-name", "minor", `named only by placeholder: ${name.slice(14)}`, describe(el));
  }

  // 4. inputs need a real label (placeholder alone is reported above)
  for (const el of document.querySelectorAll("input:not([type=hidden]),select,textarea")) {
    if (!isVisible(el)) continue;
    const hasLabel =
      el.getAttribute("aria-label") ||
      el.getAttribute("aria-labelledby") ||
      (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) ||
      el.closest("label");
    if (!hasLabel) {
      add("input-label", "serious", "form control without a <label> or aria-label", describe(el));
    }
  }

  // 5. images
  for (const img of document.querySelectorAll("img")) {
    if (!isVisible(img)) continue;
    if (img.getAttribute("alt") === null)
      add("img-alt", "serious", "<img> without an alt attribute", describe(img));
  }

  // 6. positive tabindex breaks natural order
  for (const el of document.querySelectorAll("[tabindex]")) {
    const v = Number(el.getAttribute("tabindex"));
    if (v > 0)
      add("tabindex-positive", "moderate", `tabindex=${v} overrides DOM order`, describe(el));
  }

  // 7. touch targets (mobile only — judged by viewport width)
  if (window.innerWidth <= 480) {
    for (const el of interactive) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      // WCAG 2.5.8 target size (minimum) is 24x24; 44 is the comfortable
      // guideline. Flag below 24 as a violation, below 44 as advisory.
      if (r.width < 24 || r.height < 24)
        add(
          "target-size",
          "serious",
          `target ${Math.round(r.width)}x${Math.round(r.height)} < 24px`,
          describe(el),
        );
      else if (r.width < 44 || r.height < 44)
        add(
          "target-size",
          "minor",
          `target ${Math.round(r.width)}x${Math.round(r.height)} < 44px guideline`,
          describe(el),
        );
    }
  }

  // 8. status must not be encoded by colour alone — every status badge needs text
  for (const el of document.querySelectorAll("[class*=status],[class*=badge],[class*=Status]")) {
    if (!isVisible(el)) continue;
    if (!(el.innerText ?? "").trim() && !el.getAttribute("aria-label")) {
      add(
        "status-color-only",
        "serious",
        "status indicator with no text or aria-label",
        describe(el),
      );
    }
  }

  // 9. motion preferences honoured
  const sheets = [...document.styleSheets];
  let reducesMotion = false;
  for (const sheet of sheets) {
    let rules;
    try {
      rules = sheet.cssRules;
    } catch {
      continue; // cross-origin
    }
    for (const rule of rules ?? []) {
      if (rule.media?.mediaText?.includes("prefers-reduced-motion")) reducesMotion = true;
    }
  }
  out.stats.honoursReducedMotion = reducesMotion;
  if (!reducesMotion)
    add("reduced-motion", "moderate", "no prefers-reduced-motion rule found in any stylesheet");

  return out;
};

/** Tab through the page and check the focus ring is actually visible. */
const FOCUS_CHECK = async (page) => {
  const results = { stops: 0, invisibleFocus: [], order: [] };
  await page.evaluate(() => document.body.focus());
  for (let i = 0; i < 40; i++) {
    await page.keyboard.press("Tab");
    const info = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      const s = getComputedStyle(el);
      const hasRing =
        (s.outlineStyle !== "none" && parseFloat(s.outlineWidth) > 0) ||
        s.boxShadow !== "none" ||
        s.borderColor !== s.backgroundColor;
      return {
        tag: el.tagName.toLowerCase(),
        text: (el.innerText ?? el.getAttribute("aria-label") ?? "").trim().slice(0, 30),
        hasRing,
        isBody: false,
      };
    });
    if (!info) break;
    results.stops++;
    if (!info.hasRing) results.invisibleFocus.push(`${info.tag} "${info.text}"`);
    results.order.push(`${info.tag}:${info.text}`);
  }
  return results;
};

/**
 * Wait until the page has actually settled.
 *
 * `networkidle` fires before the place page's second wave of requests, so a
 * 450 ms sleep afterwards audited a skeleton screen and reported a missing
 * <h1> that exists in the real render. An audit that invents defects is worse
 * than no audit: it trains the reader to ignore the report.
 */
async function settlePage(page) {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 10000,
    })
    .catch(() => {});
  await page.waitForTimeout(400);
}

async function main() {
  const jsonOut = process.argv.includes("--json")
    ? process.argv[process.argv.indexOf("--json") + 1]
    : null;
  const report = { consumer: {}, admin: {}, focus: {} };
  const browser = await chromium.launch();
  const severeCount = { serious: 0, moderate: 0, minor: 0 };

  try {
    // ---- consumer at the narrowest supported width ----
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    for (const [name, hash] of CONSUMER_PAGES) {
      await page.goto(`${H5}/${hash}`, { waitUntil: "networkidle" }).catch(() => {});
      await settlePage(page);
      const res = await page.evaluate(AUDIT);
      report.consumer[name] = res;
      for (const i of res.issues) severeCount[i.severity]++;
    }
    // keyboard walkthrough on the two most interaction-dense pages
    for (const [name, hash] of [
      ["home", ""],
      ["place", `#/place/${FIXTURE.mall}`],
    ]) {
      await page.goto(`${H5}/${hash}`, { waitUntil: "networkidle" }).catch(() => {});
      await settlePage(page);
      report.focus[`consumer:${name}`] = await FOCUS_CHECK(page);
    }
    await ctx.close();

    // ---- admin ----
    const actx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const apage = await actx.newPage();
    await apage.goto(`${ADMIN}/login`, { waitUntil: "networkidle" }).catch(() => {});
    await apage.waitForTimeout(400);
    await apage.fill('input[type="email"]', "admin@demo-petaccess.com").catch(() => {});
    await apage.fill('input[type="password"]', "admin12345").catch(() => {});
    // The submit control carries no `type` attribute (a bare <button> inside a
    // form defaults to submit), so selecting on type silently waits forever.
    await apage.click("form button").catch(() => {});
    await apage.waitForTimeout(2200);
    if (apage.url().includes("/login")) {
      console.log("[warn] admin login did not leave /login — admin rows below are the login page");
    }
    for (const [name, pathname] of ADMIN_PAGES) {
      await apage.goto(`${ADMIN}${pathname}`, { waitUntil: "networkidle" }).catch(() => {});
      await settlePage(apage);
      const res = await apage.evaluate(AUDIT);
      report.admin[name] = res;
      for (const i of res.issues) severeCount[i.severity]++;
    }
    report.focus["admin:rule-candidates"] = await FOCUS_CHECK(apage);
    await actx.close();
  } finally {
    await browser.close();
  }

  // ---- print ----
  let total = 0;
  for (const scope of ["consumer", "admin"]) {
    console.log(`\n=== ${scope} ===`);
    for (const [name, res] of Object.entries(report[scope])) {
      const serious = res.issues.filter((i) => i.severity === "serious");
      const moderate = res.issues.filter((i) => i.severity === "moderate");
      const minor = res.issues.filter((i) => i.severity === "minor");
      total += res.issues.length;
      const flag = serious.length ? "FAIL" : moderate.length ? "WARN" : "ok";
      console.log(
        `  ${flag.padEnd(4)} ${name.padEnd(18)} serious=${serious.length} moderate=${moderate.length} minor=${minor.length} controls=${res.stats.interactive}`,
      );
      for (const i of [...serious, ...moderate].slice(0, 6)) {
        console.log(`        - [${i.severity}] ${i.rule}: ${i.detail} ${i.selector ?? ""}`);
      }
    }
  }
  console.log("\n=== keyboard focus walkthrough ===");
  for (const [name, res] of Object.entries(report.focus)) {
    console.log(
      `  ${res.invisibleFocus.length ? "WARN" : "ok  "} ${name.padEnd(28)} tabStops=${res.stops} invisibleFocus=${res.invisibleFocus.length}`,
    );
    for (const f of res.invisibleFocus.slice(0, 4)) console.log(`        - no visible ring: ${f}`);
  }
  console.log(
    `\nTOTAL issues: ${total}  (serious=${severeCount.serious} moderate=${severeCount.moderate} minor=${severeCount.minor})`,
  );

  if (jsonOut) {
    fs.mkdirSync(path.dirname(jsonOut), { recursive: true });
    fs.writeFileSync(jsonOut, JSON.stringify(report, null, 2));
    console.log("json ->", jsonOut);
  }
  process.exitCode = severeCount.serious > 0 ? 1 : 0;
}

await main();
