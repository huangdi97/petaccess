import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  // Consumer UX Baseline v1: the home is the Decision Home (search-first).
  // The map is a first-class tab of its own, not the landing screen.
  { path: "/", name: "home", component: () => import("./views/HomeView.vue") },
  { path: "/map", name: "map", component: () => import("./views/MapView.vue") },
  {
    path: "/onboarding",
    name: "onboarding",
    component: () => import("./views/OnboardingView.vue"),
  },
  { path: "/search", name: "search", component: () => import("./views/SearchView.vue") },
  { path: "/place/:id", name: "place", component: () => import("./views/PlaceView.vue") },
  { path: "/pet/new", name: "pet-new", component: () => import("./views/PetNewView.vue") },
  // ---- v0.6: pet profile CRUD (UI_UX_IMPLEMENTATION_SPEC §6) ----
  { path: "/pets", name: "pets", component: () => import("./views/PetProfileView.vue") },
  {
    // `:id` is optional so the 贡献 tab has an entry point of its own
    // (Consumer UX Baseline v1 §21–23); without a place the view asks the user
    // to pick one instead of guessing.
    path: "/contribute/:id?",
    name: "contribute",
    component: () => import("./views/ContributeView.vue"),
  },
  { path: "/mine", name: "mine", component: () => import("./views/MineView.vue") },
  // ---- v0.6: privacy controls, notification centre, settings/methodology ----
  { path: "/privacy", name: "privacy", component: () => import("./views/PrivacyView.vue") },
  {
    path: "/notifications",
    name: "notifications",
    component: () => import("./views/NotificationsView.vue"),
  },
  { path: "/settings", name: "settings", component: () => import("./views/SettingsView.vue") },
  // ---- v0.5: explainable match + user coexistence boundary ----
  { path: "/boundary", name: "boundary", component: () => import("./views/BoundaryView.vue") },
  {
    path: "/place/:id/why",
    name: "match-explain",
    component: () => import("./views/MatchExplainView.vue"),
  },
];
