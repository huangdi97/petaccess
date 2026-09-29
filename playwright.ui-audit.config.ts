import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const win = process.platform === "win32";
const venvPython = JSON.stringify(
  path.resolve(__dirname, ".venv", win ? "Scripts" : "bin", win ? "python.exe" : "python"),
);
const feEnv = { ...process.env, VITE_API_PROXY: "http://127.0.0.1:8015" };
const visualDbUrl =
  "postgresql+psycopg://petaccess:petaccess_dev_only@localhost:5432/petaccess_visual";

/**
 * UI audit capture run 鈥?M3 鍙栬瘉锛堜慨鏀瑰墠锛変笌鏈€缁堥獙鏀讹紙淇敼鍚庯級鍏辩敤銆? *
 * 涓?playwright.visual.config.ts 鐩稿悓鐨勬湇鍔℃爤锛歱etaccess_visual 纭畾鎬? * seed锛坴isual_db_reset.py锛夆啋 API :8015 鈫?H5 preview :5179銆俿pec 璐熻矗鎶? * 鐪熷疄娓叉煋鎴浘鍐欏叆 artifacts/ui-audit/{current,m3-final}/锛屼笉鍐欏熀绾裤€? */
export default defineConfig({
  testDir: "./tests/ui-audit",
  use: {
    headless: true,
    baseURL: "http://127.0.0.1:5179",
    // Reuse an installed browser when the pinned Chromium revision is absent
    // (Goal 搂11: never download a browser while a compatible one exists locally).
    ...(process.env.PLAYWRIGHT_CHANNEL ? { channel: process.env.PLAYWRIGHT_CHANNEL } : {}),
  },
  webServer: [
    {
      command: `${venvPython} ${path.resolve(__dirname, "scripts", "visual_db_reset.py")} && ${venvPython} ${path.resolve(__dirname, "scripts", "dev_api_server.py")} --db-name petaccess_visual --role VISUAL --port 8015`,
      cwd: path.resolve(__dirname, "services/api"),
      url: "http://127.0.0.1:8015/health",
      reuseExistingServer: false,
      timeout: 180000,
      env: { ...process.env, DATABASE_URL: visualDbUrl },
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: "pnpm --filter @petaccess/client-h5 exec vite preview --host 127.0.0.1 --port 5179",
      port: 5179,
      reuseExistingServer: true,
      timeout: 60000,
      env: feEnv,
    },
  ],
  projects: [
    {
      name: "ui-360",
      testMatch: /capture.*\.spec\.ts/,
      use: { viewport: { width: 360, height: 740 } },
    },
    {
      name: "ui-430",
      testMatch: /capture.*\.spec\.ts/,
      use: { viewport: { width: 430, height: 740 } },
    },
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
