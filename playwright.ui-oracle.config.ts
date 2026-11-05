/**
 * Playwright config for the UI Oracle run (see tools/ui-oracle/README.md).
 *
 * Same deterministic stack as playwright.ui-reconstruction.config.ts
 * (petaccess_visual seed + API :8012 + H5 preview :5176) so baseline and final
 * probes are comparable. Stage is set by UI_ORACLE_STAGE.
 *
 * Ports 8012/5176 are used instead of the shared 8011/5175 so the oracle can
 * run a fresh stack (picking up backend copy fixes) without killing any server
 * we did not start (process-ownership rules). `reuseExistingServer` reuses an
 * oracle stack left running between stage runs.
 */
import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const win = process.platform === "win32";
const venvPython = JSON.stringify(
  path.resolve(__dirname, ".venv", win ? "Scripts" : "bin", win ? "python.exe" : "python"),
);
const API_PORT = 8012;
const PREVIEW_PORT = 5176;
const feEnv = { ...process.env, VITE_API_PROXY: `http://127.0.0.1:${API_PORT}` };
const visualDbUrl =
  "postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess_visual";

export default defineConfig({
  testDir: "./tests/ui-oracle",
  timeout: 90000,
  // All three viewport projects share one deterministic visual database.
  // Run serially so governance fixtures created for one viewport can never
  // leak into another viewport's canonical Search/Home/Map screenshots.
  workers: 1,
  use: {
    headless: true,
    baseURL: `http://127.0.0.1:${PREVIEW_PORT}`,
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  },
  webServer: [
    {
      command: `${venvPython} ${path.resolve(__dirname, "scripts", "visual_db_reset.py")} && ${venvPython} ${path.resolve(__dirname, "scripts", "dev_api_server.py")} --db-name petaccess_visual --role VISUAL --port ${API_PORT}`,
      cwd: path.resolve(__dirname, "services/api"),
      url: `http://127.0.0.1:${API_PORT}/health`,
      reuseExistingServer: true,
      timeout: 180000,
      env: { ...process.env, DATABASE_URL: visualDbUrl },
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: `pnpm --filter @petaccess/client-h5 exec vite preview --host 127.0.0.1 --port ${PREVIEW_PORT}`,
      port: PREVIEW_PORT,
      reuseExistingServer: true,
      timeout: 60000,
      env: feEnv,
    },
  ],
  projects: [
    { name: "oracle-desktop", use: { viewport: { width: 1440, height: 900 } } },
    { name: "oracle-tablet", use: { viewport: { width: 800, height: 1080 }, hasTouch: true } },
    { name: "oracle-mobile", use: { viewport: { width: 430, height: 932 }, hasTouch: true } },
  ],
});
