import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const win = process.platform === "win32";
const venvPython = JSON.stringify(
  path.resolve(__dirname, ".venv", win ? "Scripts" : "bin", win ? "python.exe" : "python"),
);
const feEnv = { ...process.env, VITE_API_PROXY: "http://127.0.0.1:8011" };
const visualDbUrl =
  "postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess_visual";

/**
 * UI reconstruction capture run — baseline / phase gates / final screenshots.
 * Same deterministic stack as playwright.visual.config.ts (petaccess_visual seed)
 * so before/after pairs are comparable. Stage is selected via
 * UI_RECONSTRUCTION_STAGE (baseline | phase1 | phase2 | phase3 | final).
 */
export default defineConfig({
  testDir: "./tests/ui-reconstruction",
  timeout: 90000,
  use: {
    headless: true,
    baseURL: "http://127.0.0.1:5175",
  },
  webServer: [
    {
      command: `${venvPython} ${path.resolve(__dirname, "scripts", "visual_db_reset.py")} && ${venvPython} ${path.resolve(__dirname, "scripts", "dev_api_server.py")} --db-name petaccess_visual --role VISUAL --port 8011`,
      cwd: path.resolve(__dirname, "services/api"),
      url: "http://127.0.0.1:8011/health",
      reuseExistingServer: false,
      timeout: 180000,
      env: { ...process.env, DATABASE_URL: visualDbUrl },
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: "pnpm --filter @petaccess/client-h5 exec vite preview --host 127.0.0.1 --port 5175",
      port: 5175,
      reuseExistingServer: true,
      timeout: 60000,
      env: feEnv,
    },
  ],
  projects: [
    { name: "ui-360", testMatch: /capture.*\.spec\.ts/, use: { viewport: { width: 360, height: 740 } } },
    { name: "ui-430", testMatch: /capture.*\.spec\.ts/, use: { viewport: { width: 430, height: 740 } } },
    {
      name: "ui-800",
      testMatch: /capture.*\.spec\.ts/,
      use: { viewport: { width: 800, height: 900 }, isMobile: false, hasTouch: true },
    },
    {
      name: "ui-1280",
      testMatch: /capture.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 800 } },
    },
    {
      name: "ui-1440",
      testMatch: /capture.*\.spec\.ts/,
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
    },
  ],
});
