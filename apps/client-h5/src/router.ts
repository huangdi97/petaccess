import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  // Consumer UX Baseline v1: the home is the Decision Home (search-first).
  // The map is a first-class tab of its own, not the landing screen.
  {
    path: "/",
    name: "home",
    component: () => import("./views/HomeView.vue"),
    meta: { title: "首页" },
  },
  {
    path: "/map",
    name: "map",
    component: () => import("./views/MapView.vue"),
    meta: { title: "规则地图" },
  },
  {
    path: "/onboarding",
    name: "onboarding",
    component: () => import("./views/OnboardingView.vue"),
    meta: { title: "登录 / 注册" },
  },
  {
    path: "/search",
    name: "search",
    component: () => import("./views/SearchView.vue"),
    meta: { title: "搜索场所" },
  },
  {
    path: "/place/:id",
    name: "place",
    component: () => import("./views/PlaceView.vue"),
    meta: { title: "场所" },
  },
  {
    path: "/pet/new",
    name: "pet-new",
    component: () => import("./views/PetNewView.vue"),
    meta: { title: "新增宠物" },
  },
  // ---- v0.6: pet profile CRUD (UI_UX_IMPLEMENTATION_SPEC §6) ----
  {
    path: "/pets",
    name: "pets",
    component: () => import("./views/PetProfileView.vue"),
    meta: { title: "宠物档案" },
  },
  {
    // `:id` is optional so the 贡献 tab has an entry point of its own
    // (Consumer UX Baseline v1 §21–23); without a place the view asks the user
    // to pick one instead of guessing.
    path: "/contribute/:id?",
    name: "contribute",
    component: () => import("./views/ContributeView.vue"),
    meta: { title: "贡献" },
  },
  {
    path: "/mine",
    name: "mine",
    component: () => import("./views/MineView.vue"),
    meta: { title: "我的" },
  },
  // ---- v0.6: privacy controls, notification centre, settings/methodology ----
  {
    path: "/privacy",
    name: "privacy",
    component: () => import("./views/PrivacyView.vue"),
    meta: { title: "隐私" },
  },
  {
    path: "/notifications",
    name: "notifications",
    component: () => import("./views/NotificationsView.vue"),
    meta: { title: "通知" },
  },
  {
    path: "/settings",
    name: "settings",
    component: () => import("./views/SettingsView.vue"),
    meta: { title: "设置" },
  },
  // ---- v0.2.0 M2: 关于 page (desktop rail 关于 destination) ----
  {
    path: "/about",
    name: "about",
    component: () => import("./views/AboutView.vue"),
    meta: { title: "关于" },
  },
  // ---- v0.5: explainable match + user coexistence boundary ----
  {
    path: "/boundary",
    name: "boundary",
    component: () => import("./views/BoundaryView.vue"),
    meta: { title: "共处偏好" },
  },
  {
    path: "/place/:id/why",
    name: "match-explain",
    component: () => import("./views/MatchExplainView.vue"),
    meta: { title: "为什么" },
  },
  // M3: unknown paths land on the unified NotFound state instead of a blank
  // router warning (A1). Order matters: catch-all must be last.
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("./views/NotFoundView.vue"),
    meta: { title: "页面不存在" },
  },
];
