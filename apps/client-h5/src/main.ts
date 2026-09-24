import { createApp } from "vue";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import { routes } from "./router";
import { bindStorage, configureApi } from "@petaccess/client-core";
import "./styles.css";

bindStorage({
  get: (k) => localStorage.getItem(k) ?? undefined,
  set: (k, v) => localStorage.setItem(k, v),
  remove: (k) => localStorage.removeItem(k),
});
configureApi((import.meta.env.VITE_API_BASE as string | undefined) ?? "/api/v1");

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

createApp(App).use(router).mount("#app");
