<script setup lang="ts">
/**
 * PlaceSectionNav — Place Dossier local section navigation (§15).
 *
 * 概览 / 空间 / 规则 / 现场 / 证据。Desktop = text tab + underline；
 * Mobile = horizontal scroll text tab。不是 pill。切换写回 ?view= query so
 * deep link / back-forward / refresh 全部可用。
 */
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

export type PlaceViewKey = "overview" | "space" | "rules" | "reality" | "evidence";

const ROUTE_BY_VIEW: Record<PlaceViewKey, string> = {
  overview: "overview",
  space: "space",
  rules: "rules",
  reality: "reality",
  evidence: "evidence",
};

const TABS: { key: PlaceViewKey; label: string }[] = [
  { key: "overview", label: "概览" },
  { key: "space", label: "空间" },
  { key: "rules", label: "规则" },
  { key: "reality", label: "现场" },
  { key: "evidence", label: "证据" },
];

const route = useRoute();
const router = useRouter();

const props = defineProps<{
  /** 当前视图（一般为 ?view= 解析结果）。 */
  active: PlaceViewKey;
  placeId: string;
}>();

const activeView = computed(() =>
  TABS.some((t) => t.key === props.active) ? props.active : "overview",
);

function select(v: PlaceViewKey) {
  if (v === activeView.value) return;
  void router.replace({
    query: { ...route.query, view: ROUTE_BY_VIEW[v] },
  });
}
</script>

<template>
  <nav class="place-nav" data-ui="place-nav" aria-label="场所档案分节">
    <button
      v-for="t in TABS"
      :key="t.key"
      type="button"
      class="place-nav__tab"
      :class="{ 'place-nav__tab--active': t.key === activeView }"
      :aria-current="t.key === activeView ? 'page' : undefined"
      :data-testid="`place-tab-${t.key}`"
      @click="select(t.key)"
    >
      {{ t.label }}
    </button>
  </nav>
</template>

<style scoped>
/* Desktop：text tab + underline；Mobile：横向滚动 text tab。 */
.place-nav {
  display: flex;
  gap: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.place-nav::-webkit-scrollbar {
  display: none;
}
.place-nav__tab {
  flex-shrink: 0;
  border: none;
  border-bottom: var(--pa-border-width-strong) solid transparent;
  background: transparent;
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  padding: var(--pa-space-2) var(--pa-space-1);
  margin-bottom: calc(-1 * var(--pa-border-width));
  cursor: pointer;
  min-height: var(--pa-size-control-md);
}
.place-nav__tab--active {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-600);
  border-bottom-color: var(--pa-color-accent);
}
.place-nav__tab:hover {
  color: var(--pa-color-accent);
}
</style>
