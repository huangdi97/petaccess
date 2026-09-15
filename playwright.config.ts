import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5175",
    headless: true,
  },
  webServer: {
    // The H5 bundle requests a relative /api/v1, and `vite preview` only proxies
    // it when the target is supplied — point it at the E2E API port (:8010).
    command: "pnpm --filter @petaccess/client-h5 exec vite preview --port 5175 --strictPort",
    url: "http://127.0.0.1:5175",
    reuseExistingServer: true,
    timeout: 30000,
    env: { VITE_API_PROXY: "http://127.0.0.1:8010" },
  },
});
