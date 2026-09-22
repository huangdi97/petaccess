import type { RouteRecordRaw } from "vue-router";

export const routes: RouteRecordRaw[] = [
  { path: "/login", name: "login", component: () => import("./views/LoginView.vue") },
  { path: "/", redirect: "/dashboard" },
  { path: "/dashboard", name: "dashboard", component: () => import("./views/DashboardView.vue") },
  { path: "/places", name: "places", component: () => import("./views/PlacesView.vue") },
  {
    path: "/places/:id",
    name: "place-detail",
    component: () => import("./views/PlaceDetailView.vue"),
  },
  { path: "/rules", name: "rules", component: () => import("./views/RulesView.vue") },
  { path: "/sources", name: "sources", component: () => import("./views/SourcesView.vue") },
  {
    path: "/regulations",
    name: "regulations",
    component: () => import("./views/RegulationsView.vue"),
  },
  { path: "/claims", name: "claims", component: () => import("./views/ClaimsView.vue") },
  { path: "/disputes", name: "disputes", component: () => import("./views/DisputesView.vue") },
  {
    path: "/observations",
    name: "observations",
    component: () => import("./views/ObservationsView.vue"),
  },
  { path: "/ai-queue", name: "ai-queue", component: () => import("./views/AiQueueView.vue") },
  { path: "/conflicts", name: "conflicts", component: () => import("./views/ConflictsView.vue") },
  { path: "/audit", name: "audit", component: () => import("./views/AuditView.vue") },
  { path: "/users", name: "users", component: () => import("./views/UsersView.vue") },

  // ---- v0.5: real-API domain surfaces ----
  {
    path: "/rule-candidates",
    name: "rule-candidates",
    component: () => import("./views/RuleCandidatesView.vue"),
  },
  { path: "/evidence", name: "evidence", component: () => import("./views/EvidenceView.vue") },
  {
    path: "/observation-candidates",
    name: "observation-candidates",
    component: () => import("./views/ObservationCandidatesView.vue"),
  },
  {
    path: "/monitors",
    name: "monitors",
    component: () => import("./views/SourceMonitorsView.vue"),
  },
  {
    path: "/organizations",
    name: "organizations",
    component: () => import("./views/OrganizationsView.vue"),
  },
  { path: "/spatial", name: "spatial", component: () => import("./views/SpatialExtrasView.vue") },
  {
    path: "/event-rules",
    name: "event-rules",
    component: () => import("./views/EventRulesView.vue"),
  },
  {
    path: "/match-debugger",
    name: "match-debugger",
    component: () => import("./views/MatchDebuggerView.vue"),
  },

  // ---- v0.9-R1: Reality Layer admin surfaces (AC11) ----
  {
    path: "/reality",
    name: "reality-dashboard",
    component: () => import("./views/RealityDashboardView.vue"),
  },
  {
    path: "/reality/candidates",
    name: "reality-candidates",
    component: () => import("./views/RealityCandidateQueueView.vue"),
  },
  {
    path: "/reality/claims",
    name: "reality-claims",
    component: () => import("./views/RealityClaimsView.vue"),
  },
];
