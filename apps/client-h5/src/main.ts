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

const router = createRouter({ history: createWebHashHistory(), routes });
createApp(App).use(router).mount("#app");
