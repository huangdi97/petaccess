import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const win = process.platform === "win32";
const venvPython = JSON.stringify(
  path.resolve(__dirname, ".venv", win ? "Scripts" : "bin", win ? "python.exe" : "python"),
);

/**
 * `webServer.env` REPLACES the child environment 鈥?it is not merged. Spreading
 * `process.env` back in is not belt-and-braces: without it the spawned shell
 * has no `PATH`, so `pnpm` is "not found", the preview never binds :5178, and
 * the only symptom is an opaque "Timed out waiting 60000ms from
 * config.webServer". The API and admin servers masked this for a while because
 * they happened to already be running and `reuseExistingServer` skipped the
 * launch entirely.
 */
const feEnv = { ...process.env, VITE_API_PROXY: "http://127.0.0.1:8014" };

/**
 * The visual suite does NOT run against the dev database.
 *
 * It runs against `petaccess_visual`, dropped and re-seeded from the fixed demo
 * dataset immediately before the API starts (see `scripts/visual_db_reset.py`).
 * Reason: the dev database grows. The audit log, the candidate queue and the
 * observation list all accumulate rows, so a full-page baseline of
 * `/admin/audit` is stale the moment anything else touches the stack. Re-running
 * the committed baselines in compare mode failed 8/8 admin list pages 鈥?the
 * audit baseline alone had drifted to 130 890 px tall and no longer finished
 * capturing inside the 20 s timeout.
 *
 * The dev database is never touched: `run_demo_seed()` truncates the candidate,
 * dispute and audit tables, and the reset script refuses to run against a
 * protected database name.
 */
const visualDbUrl =
  "postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess_visual";
const apiEnv = { ...process.env, DATABASE_URL: visualDbUrl };

/**
 * Tablet viewport, Chromium 鈥?deliberately NOT `devices["iPad (gen 7)"]`.
 *
 * That device resolves to WebKit, and this environment cannot load the apps
 * under WebKit: every module request (`/@vite/client`, `/node_modules/.vite/
 * deps/vue.js`, `/src/main.ts`) comes back 404 with "Load request cancelled".
 * WebKit still renders `index.html`, so the run does not error 鈥?it screenshots
 * an empty document and reports PASS. All 17 tablet baselines were 6.2 KB
 * blank pages next to 100鈥?20 KB real ones at the other two viewports.
 *
 * A blank baseline is worse than a missing one: it looks like coverage and
 * silently encodes nothing. So the tablet rows measure *layout at 768 px*,
 * which is what this suite is for, and WebKit stays out until it can actually
 * load a page here. `assertRendered` in tests/visual/fixtures.ts now fails the
 * run if a page screenshots empty, so this cannot come back unnoticed.
 */
const tablet = {
  viewport: { width: 768, height: 1024 },
  deviceScaleFactor: 2,
  isMobile: false,
  hasTouch: true,
  userAgent: devices["iPad (gen 7)"].userAgent,
};

/**
 * Visual regression / UI reality run.
 *
 * Separate from `playwright.config.ts` because the two have different jobs:
 * that one asserts behaviour, this one asserts *appearance* 鈥?same pages, same
 * fixtures, three viewports, compared against committed baselines.
 *
 * Snapshots are only meaningful if they are deterministic, so:
 *   - the clock is frozen per test (relative "3 澶╁墠" labels would drift),
 *   - animations and the caret are disabled in `toHaveScreenshot`,
 *   - the API is started by this config rather than by hand.
 */
export default defineConfig({
  testDir: "./tests/visual",
  timeout: 60000,
  expect: {
    toHaveScreenshot: {
      // Anti-aliasing and font rasterisation differ enough between machines
      // that a 0 threshold would make every baseline update a chore.
      maxDiffPixelRatio: 0.02,
      animations: "disabled",
      caret: "hide",
      scale: "css",
      // The 5s default is not enough for a full-page shot of the longer admin
      // tables at 768脳1024 @2x 鈥?the audit log alone is a few thousand pixels
      // tall and the capture times out rather than diffing.
      timeout: 20000,
    },
  },
  use: {
    headless: true,
    // Reuse an installed browser when the pinned Chromium revision is absent
    // (Goal 搂11: never download a browser while a compatible one exists locally).
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  },
  // Availability is probed over TCP (`port`), not HTTP (`url`), and the servers
  // are started without `--strictPort`. Both are deliberate:
  //
  //   - An HTTP probe can fail transiently, and any probe failure makes
  //     Playwright fall through to launching its own copy of a server that is
  //     already up. With `--strictPort` that launch dies on "port already in
  //     use" and takes the whole run with it; without it the stray copy just
  //     moves to the next free port and the original keeps serving. The probe
  //     is then free to succeed on retry.
  //   - It is worth being able to start these by hand: the frontend reads its
  //     API target from `VITE_API_PROXY` at config-load time, so a preview
  //     started without it silently proxies to :8000 and every page renders
  //     銆屽姞杞藉け璐ャ€?鈥?see `assertNotErrorState` in tests/visual/fixtures.ts.
  webServer: [
    {
      // Reset first, then serve 鈥?in one command, because Playwright gives no
      // ordering guarantee between `globalSetup` and `webServer`, and a reset
      // that lands after the API has connected would drop the database out from
      // under it.
      //
      // `reuseExistingServer: false` is the other half of that: the reset has to
      // happen on every run, so there is nothing worth reusing. Port 8014 keeps
      // this instance away from the hand-started dev API on 8010.
      command: `${venvPython} ${path.resolve(__dirname, "scripts", "visual_db_reset.py")} && ${venvPython} ${path.resolve(__dirname, "scripts", "dev_api_server.py")} --db-name petaccess_visual --role VISUAL --port 8014`,
      cwd: path.resolve(__dirname, "services/api"),
      url: "http://127.0.0.1:8014/health",
      reuseExistingServer: false,
      timeout: 180000,
      env: apiEnv,
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      // `--host 127.0.0.1` is not cosmetic: with the default `localhost` bind
      // the preview can end up on ::1 only, and the probe targets 127.0.0.1.
      command: "pnpm --filter @petaccess/client-h5 exec vite preview --host 127.0.0.1 --port 5178",
      port: 5178,
      reuseExistingServer: true,
      timeout: 60000,
      env: feEnv,
    },
    {
      command: "pnpm --filter @petaccess/admin exec vite --host 127.0.0.1 --port 5173",
      port: 5173,
      reuseExistingServer: true,
      timeout: 60000,
      env: feEnv,
    },
  ],
  projects: [
    {
      name: "h5-390",
      testMatch: /consumer.*\.spec\.ts/,
      use: { ...devices["Pixel 5"], baseURL: "http://127.0.0.1:5178" },
    },
    {
      // Tablet width, Chromium 鈥?see the note above `tablet` for why this is
      // not `devices["iPad (gen 7)"]` (WebKit) any more.
      name: "h5-768",
      testMatch: /consumer.*\.spec\.ts/,
      use: { ...tablet, baseURL: "http://127.0.0.1:5178" },
    },
    {
      name: "h5-1440",
      testMatch: /consumer.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
        baseURL: "http://127.0.0.1:5178",
      },
    },
    {
      name: "admin-1440",
      testMatch: /admin.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
        baseURL: "http://127.0.0.1:5173",
      },
    },
    {
      name: "admin-768",
      testMatch: /admin.*\.spec\.ts/,
      use: { ...tablet, baseURL: "http://127.0.0.1:5173" },
    },
  ],
});
