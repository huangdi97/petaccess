import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import App from "./App.vue";
import { routes } from "./router";
import "./styles.css";

const router = createRouter({ history: createWebHistory(), routes });

// naive auth guard: every route except /login requires a token
router.beforeEach((to) => {
  const token = localStorage.getItem("admin_token");
  if (to.name !== "login" && !token) return { name: "login" };
  if (to.name === "login" && token) return { name: "dashboard" };
  return true;
});

createApp(App).use(router).mount("#app");
