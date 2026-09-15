import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

/**
 * The H5 bundle calls the API through a relative `/api/v1` base, so whichever
 * server is serving it must proxy that prefix. `vite preview` (used by the
 * Playwright run) does NOT inherit `server.proxy`, so the proxy is declared for
 * both — otherwise every data-driven E2E assertion fails on a 404 that looks
 * like an application bug.
 *
 * Override the target when the API is not on the default port, e.g. the E2E run
 * uses :8010: `VITE_API_PROXY=http://127.0.0.1:8010`.
 */
const apiTarget = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000";
const apiProxy = { "/api": { target: apiTarget, changeOrigin: true } };

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
});
