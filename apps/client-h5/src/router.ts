import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  { path: "/", name: "home", component: () => import("./views/HomeView.vue") },
  {
    path: "/onboarding",
    name: "onboarding",
    component: () => import("./views/OnboardingView.vue"),
  },
  { path: "/search", name: "search", component: () => import("./views/SearchView.vue") },
  { path: "/place/:id", name: "place", component: () => import("./views/PlaceView.vue") },
  { path: "/pet/new", name: "pet-new", component: () => import("./views/PetNewView.vue") },
  {
    path: "/contribute/:id",
    name: "contribute",
    component: () => import("./views/ContributeView.vue"),
  },
  { path: "/mine", name: "mine", component: () => import("./views/MineView.vue") },
  // ---- v0.5: explainable match + user coexistence boundary ----
  { path: "/boundary", name: "boundary", component: () => import("./views/BoundaryView.vue") },
  {
    path: "/place/:id/why",
    name: "match-explain",
    component: () => import("./views/MatchExplainView.vue"),
  },
];
