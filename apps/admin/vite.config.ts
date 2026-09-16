import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

/**
 * Same rule as the H5: the admin calls a relative `/api` base, so both the dev
 * server and `vite preview` must proxy it — `preview` does not inherit
 * `server.proxy`, and a missing proxy surfaces as a 404 that looks like an
 * application bug rather than a wiring one.
 *
 * Override the target when the API is not on the default port, e.g. the review
 * run uses :8010: `VITE_API_PROXY=http://127.0.0.1:8010`.
 */
const apiTarget = process.env.VITE_API_PROXY ?? "http://127.0.0.1:8000";
const apiProxy = { "/api": { target: apiTarget, changeOrigin: true } };

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: apiProxy,
  },
  preview: {
    proxy: apiProxy,
  },
});
