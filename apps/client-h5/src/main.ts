import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import { routes } from "./router";
import { bindStorage, configureApi } from "@petaccess/client-core";
import { bootStage } from "./config/bootTrace";
import { detectRuntimeKind, resolveApiEndpoint } from "./config/endpoints";
import "./styles.css";

bootStage("INDEX_LOADED");

bindStorage({
  get: (k) => localStorage.getItem(k) ?? undefined,
  set: (k, v) => localStorage.setItem(k, v),
  remove: (k) => localStorage.removeItem(k),
});

// REG-003 fix: packaged Tauri runtimes (Windows/Android) have no Vite proxy,
// so the API endpoint is resolved per runtime instead of defaulting to the
// H5-only relative /api/v1 path.
const kind = detectRuntimeKind(navigator.userAgent, "__TAURI_INTERNALS__" in window);
const env = {
  VITE_API_BASE: import.meta.env.VITE_API_BASE as string | undefined,
  VITE_TAURI_API_BASE: import.meta.env.VITE_TAURI_API_BASE as string | undefined,
  VITE_TAURI_ANDROID_API_BASE: import.meta.env.VITE_TAURI_ANDROID_API_BASE as string | undefined,
};
configureApi(resolveApiEndpoint(env, kind));

bootStage("VUE_CREATED");

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  // M3 (A2): back/forward restores the exact scroll position; fresh navigation
  // starts at the top so a deep link never lands mid-page.
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, top: 0 };
    return { top: 0 };
  },
});

// M3 (A3): every route carries meta.title; the document title echoes the
// current surface so tab-switching and history entries stay identifiable.
router.afterEach((to) => {
  document.title = to.meta.title ? `${String(to.meta.title)} · PetAccess` : "PetAccess";
});

router
  .isReady()
  .then(() => bootStage("ROUTER_READY"))
  .catch(() => bootStage("ROUTER_FAILED"));

createApp(App).use(router).mount("#app");
