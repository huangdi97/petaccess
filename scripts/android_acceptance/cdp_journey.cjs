/**
 * CDP journey over the debug WebView via Playwright connectOverCDP.
 *
 * Run: node --experimental-vm-modules? No — plain CJS:
 *   node cdp_journey.cjs
 * It drives the packaged Android app by hash-route navigation, reads the DOM
 * text of every surface, and writes evidence JSON + screenshots.
 */
const { chromium } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const CDP = "http://127.0.0.1:9223";
const OUT = path.join(
  "E:\\AI\\宠物管理\\artifacts\\android_acceptance\\runtime",
  "cdp_journey_playwright.json",
);

const routes = [
  ["", "R01", "home"],
  ["search", "R02", "search"],
  ["map", "R03", "map"],
  ["contribute", "R04", "contribute"],
  ["mine", "R05", "mine"],
  ["settings", "R06", "settings"],
  ["privacy", "R07", "privacy"],
  ["about", "R08", "about"],
];

async function main() {
  const browser = await chromium.connectOverCDP(CDP);
  const ctx = browser.contexts()[0] || (await browser.newContext());
  const pages = ctx.pages();
  const page = pages[0];
  if (!page) throw new Error("no page in CDP context");

  const rows = [];
  for (const [route, tag, state] of routes) {
    await page.evaluate((r) => {
      location.hash = "#" + r;
    }, route);
    await page.waitForTimeout(2500);
    const text = await page.evaluate(() =>
      document.body ? document.body.innerText.slice(0, 1200) : "",
    );
    const safe = route.replace(/[\\/:]/g, "_") || "home";
    const shot = path.join(
      "E:\\AI\\宠物管理\\artifacts\\android_acceptance\\screenshots",
      `phoneM__${safe}__${state}__${tag}.png`,
    );
    await page.screenshot({ path: shot });
    rows.push({ tag, route, state, text, shot });
    console.log(`  ${tag} ${route || "/"}: ${text.slice(0, 160).replace(/\n/g, " | ")}`);
  }
  fs.writeFileSync(OUT, JSON.stringify(rows, null, 2));
  await browser.close();
  console.log("CDP PLAYWRIGHT JOURNEY OK");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
