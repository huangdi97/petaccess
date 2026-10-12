/**
 * Full packaged-Android Consumer journey over the debug Tauri WebView.
 *
 * This is semantic runtime evidence, not a screenshot carousel: each route
 * must render the expected canonical data-ui-page surface without horizontal
 * overflow. Screenshots and the DOM snapshot are written together.
 */
const { chromium } = require("@playwright/test");
const fs = require("node:fs");
const path = require("node:path");

const CDP = process.env.PETACCESS_ANDROID_CDP ?? "http://127.0.0.1:9223";
const ROOT = path.resolve(__dirname, "..", "..");
const EVIDENCE_ROOT =
  process.env.PETACCESS_ANDROID_EVIDENCE_DIR ??
  path.join(ROOT, "artifacts", "android_acceptance");
const RUNTIME_DIR = path.join(EVIDENCE_ROOT, "runtime");
const SCREENSHOT_DIR = path.join(EVIDENCE_ROOT, "screenshots");
const OUT = path.join(RUNTIME_DIR, "cdp_journey_playwright.json");
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

const routes = [
  { hash: "#/", tag: "R01", name: "home", expectedPage: "home" },
  { hash: "#/search", tag: "R02", name: "search", expectedPage: "search" },
  { hash: "#/map", tag: "R03", name: "map", expectedPage: "map" },
  {
    hash: `#/place/${PLACE_ID}`,
    tag: "R04",
    name: "place-overview",
    expectedPage: "place",
  },
  {
    hash: `#/place/${PLACE_ID}?view=rules`,
    tag: "R05",
    name: "place-rules",
    expectedPage: "place",
  },
  {
    hash: `#/place/${PLACE_ID}?view=space`,
    tag: "R06",
    name: "place-space",
    expectedPage: "place",
  },
  {
    hash: `#/place/${PLACE_ID}/reality`,
    tag: "R07",
    name: "reality",
    expectedPage: "reality",
  },
  {
    hash: `#/place/${PLACE_ID}/evidence`,
    tag: "R08",
    name: "evidence",
    expectedPage: "evidence",
  },
  { hash: "#/contribute", tag: "R09", name: "contribute-entry", expectedPage: "contribution" },
  { hash: "#/mine", tag: "R10", name: "mine", expectedPage: "mine" },
  { hash: "#/settings", tag: "R11", name: "settings", expectedPage: "settings" },
  { hash: "#/privacy", tag: "R12", name: "privacy", expectedPage: "privacy" },
  { hash: "#/about", tag: "R13", name: "about", expectedPage: "about" },
];

function safeName(value) {
  return value.replace(/[^a-z0-9_-]+/gi, "_");
}

async function main() {
  fs.mkdirSync(RUNTIME_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const browser = await chromium.connectOverCDP(CDP);
  const context = browser.contexts()[0] || (await browser.newContext());
  const pages = context.pages();
  const page = pages[0];
  if (!page) throw new Error("no page in CDP context");

  const rows = [];
  let failed = false;

  for (const route of routes) {
    const startedAt = Date.now();
    await page.evaluate((hash) => {
      location.hash = hash;
    }, route.hash);

    const surface = page.locator(`[data-ui-page="${route.expectedPage}"]`).first();
    let routeError = null;
    try {
      await surface.waitFor({ state: "visible", timeout: 15000 });
      await page.waitForTimeout(800);
    } catch (error) {
      routeError = `surface timeout: ${error.message}`;
    }

    const snapshot = await page.evaluate(() => {
      const root = document.documentElement;
      const body = document.body;
      const ui = document.querySelector("[data-ui-page]");
      return {
        url: location.href,
        title: document.title,
        shell: !!document.querySelector("[data-testid=consumer-app-shell]"),
        uiPage: ui?.getAttribute("data-ui-page") ?? null,
        uiState: ui?.getAttribute("data-ui-state") ?? null,
        uiFixture: ui?.getAttribute("data-ui-fixture") ?? null,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
        document: {
          scrollWidth: root?.scrollWidth ?? body?.scrollWidth ?? 0,
          scrollHeight: root?.scrollHeight ?? body?.scrollHeight ?? 0,
        },
        horizontalOverflow:
          (root?.scrollWidth ?? body?.scrollWidth ?? 0) > window.innerWidth + 1,
        text: body?.innerText.slice(0, 1600) ?? "",
      };
    });

    if (!snapshot.shell) routeError ??= "Consumer shell missing";
    if (snapshot.uiPage !== route.expectedPage) {
      routeError ??= `expected ${route.expectedPage}, got ${snapshot.uiPage}`;
    }
    if (snapshot.horizontalOverflow) {
      routeError ??= `horizontal overflow ${snapshot.document.scrollWidth} > ${snapshot.viewport.width}`;
    }

    const shot = path.join(
      SCREENSHOT_DIR,
      `phoneM__${safeName(route.name)}__${route.tag}.png`,
    );
    await page.screenshot({ path: shot });

    const row = {
      ...route,
      elapsedMs: Date.now() - startedAt,
      ok: routeError === null,
      error: routeError,
      snapshot,
      screenshot: shot,
    };
    rows.push(row);
    if (!row.ok) failed = true;

    console.log(
      `  ${route.tag} ${route.name}: ${row.ok ? "PASS" : "FAIL"} | ${snapshot.uiPage}/${snapshot.uiState ?? "-"} | overflow=${snapshot.horizontalOverflow}`,
    );
  }

  fs.writeFileSync(
    OUT,
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        cdp: CDP,
        result: failed ? "FAIL" : "PASS",
        routes: rows,
      },
      null,
      2,
    ),
  );
  await browser.close();

  if (failed) {
    console.error(`CDP JOURNEY FAIL — see ${OUT}`);
    process.exit(1);
  }
  console.log(`CDP JOURNEY PASS — ${rows.length}/${rows.length} routes`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
