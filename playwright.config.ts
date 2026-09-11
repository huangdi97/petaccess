import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:5175",
    headless: true,
  },
  webServer: {
    command: "pnpm --filter @petaccess/client-h5 exec vite preview --port 5175 --strictPort",
    url: "http://127.0.0.1:5175",
    reuseExistingServer: true,
    timeout: 30000,
  },
});
