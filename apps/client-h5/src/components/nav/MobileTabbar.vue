<script setup lang="ts">
/**
 * MobileTabbar — bottom navigation for viewports < 768px
 * (V020_APP_SHELL_SPEC §15). Four first-class tabs: 首页 / 地图 / 贡献 / 我的.
 * Search is a Home-level feature, not a separate tab (spec §15).
 */
import { useRoute } from "vue-router";
import { Z_INDEX, type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

interface TabItem {
  to: string;
  icon: IconName;
  label: string;
}

const TABS: TabItem[] = [
  { to: "/", icon: "home", label: "首页" },
  { to: "/map", icon: "map", label: "地图" },
  { to: "/contribute", icon: "plus", label: "贡献" },
  { to: "/mine", icon: "user", label: "我的" },
];

const route = useRoute();

/** Active if the route is exactly the tab target. */
function isActive(to: string): boolean {
  if (to === "/") return route.path === "/";
  return route.path === to || route.path.startsWith(`${to}/`);
}
</script>

<template>
  <nav
    class="mobile-tabbar"
    data-testid="mobile-tabbar"
    :style="{ zIndex: `var(${Z_INDEX.tabbar})` }"
    aria-label="主导航"
  >
    <RouterLink
      v-for="tab in TABS"
      :key="tab.to"
      :to="tab.to"
      class="mobile-tabbar__item"
      :class="{ 'mobile-tabbar__item--active': isActive(tab.to) }"
      :aria-current="isActive(tab.to) ? 'page' : undefined"
    >
      <PaIcon class="mobile-tabbar__icon" :name="tab.icon" size="md" :label="tab.label" />
      <span class="mobile-tabbar__label">{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.mobile-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  background: var(--pa-color-surface-raised);
  border-top: var(--pa-border-width) solid var(--pa-color-border);
  padding-bottom: var(--pa-safe-bottom);
}

.mobile-tabbar__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--pa-space-1);
  min-height: var(--pa-layout-tabbar-height);
  color: var(--pa-color-text-muted);
  text-decoration: none;
  font-size: var(--pa-font-size-xs);
}

.mobile-tabbar__item--active {
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-medium);
}

.mobile-tabbar__item:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}
</style>
