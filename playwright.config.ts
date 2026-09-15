import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig } from "@playwright/test";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The venv lives at the repo root while uvicorn must run from services/api,
// so the interpreter is addressed absolutely (quoted: the path is not ASCII).
const win = process.platform === "win32";
const venvPython = JSON.stringify(
  path.resolve(__dirname, ".venv", win ? "Scripts" : "bin", win ? "python.exe" : "python"),
);

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5175",
    headless: true,
  },
  webServer: [
    {
      // The API used to be started by hand in a spare terminal; when it died the
      // suite went red with "Not Found" and no hint why. Playwright owns it now,
      // so a run is self-contained (and reuses one that is already listening).
      command: `${venvPython} -m uvicorn app.main:app --host 127.0.0.1 --port 8010`,
      cwd: path.resolve(__dirname, "services/api"),
      url: "http://127.0.0.1:8010/health",
      reuseExistingServer: true,
      timeout: 60000,
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      // The H5 bundle requests a relative /api/v1, and `vite preview` only proxies
      // it when the target is supplied — point it at the E2E API port (:8010).
      command: "pnpm --filter @petaccess/client-h5 exec vite preview --port 5175 --strictPort",
      url: "http://127.0.0.1:5175",
      reuseExistingServer: true,
      timeout: 30000,
      env: { VITE_API_PROXY: "http://127.0.0.1:8010" },
    },
  ],
});
