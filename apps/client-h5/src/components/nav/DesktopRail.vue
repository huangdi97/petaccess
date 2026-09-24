<script setup lang="ts">
/**
 * DesktopRail — navigation rail for viewports >= 768px
 * (V020_APP_SHELL_SPEC §16). Primary group: 首页 / 搜索 / 地图 / 贡献; secondary
 * group: 我的 / 设置 / 关于. Version info lives at the rail bottom.
 */
import { useRoute } from "vue-router";
import { Z_INDEX, type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

defineOptions({ name: "DesktopRail" });

interface RailItem {
  to: string;
  icon: IconName;
  label: string;
}

const PRIMARY: RailItem[] = [
  { to: "/", icon: "home", label: "首页" },
  { to: "/search", icon: "search", label: "搜索" },
  { to: "/map", icon: "map", label: "地图" },
  { to: "/contribute", icon: "plus", label: "贡献" },
];

const SECONDARY: RailItem[] = [
  { to: "/mine", icon: "user", label: "我的" },
  { to: "/settings", icon: "settings", label: "设置" },
  { to: "/about", icon: "info", label: "关于" },
];

const route = useRoute();
function isActive(to: string): boolean {
  if (to === "/") return route.path === "/";
  return route.path === to || route.path.startsWith(`${to}/`);
}

const version = import.meta.env.VITE_APP_VERSION ?? "0.2.0-dev";
const envLabel = import.meta.env.DEV ? "development" : "production";
</script>

<template>
  <aside
    class="desktop-rail"
    data-testid="desktop-rail"
    :style="{ zIndex: `var(${Z_INDEX.sticky})` }"
    aria-label="主导航"
  >
    <RouterLink
      to="/"
      class="desktop-rail__brand"
      :class="{ 'desktop-rail__item--active': route.path === '/' }"
    >
      <span class="desktop-rail__brand-mark" aria-hidden="true">PA</span>
      <span class="desktop-rail__brand-name">PetAccess</span>
    </RouterLink>

    <nav class="desktop-rail__group" aria-label="主要页面">
      <RouterLink
        v-for="item in PRIMARY"
        :key="item.to"
        :to="item.to"
        class="desktop-rail__item"
        :class="{ 'desktop-rail__item--active': isActive(item.to) }"
        :aria-current="isActive(item.to) ? 'page' : undefined"
      >
        <PaIcon class="desktop-rail__icon" :name="item.icon" size="md" />
        <span class="desktop-rail__label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <hr class="desktop-rail__divider" />

    <nav class="desktop-rail__group" aria-label="账户与说明">
      <RouterLink
        v-for="item in SECONDARY"
        :key="item.to"
        :to="item.to"
        class="desktop-rail__item"
        :class="{ 'desktop-rail__item--active': isActive(item.to) }"
        :aria-current="isActive(item.to) ? 'page' : undefined"
      >
        <PaIcon class="desktop-rail__icon" :name="item.icon" size="md" />
        <span class="desktop-rail__label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="desktop-rail__version" data-testid="app-version">
      <span class="desktop-rail__version-name">PetAccess v{{ version }}</span>
      <span class="desktop-rail__version-env">{{ envLabel }}</span>
    </div>
  </aside>
</template>

<style scoped>
.desktop-rail {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  width: var(--pa-layout-rail-width);
  background: var(--pa-color-surface-raised);
  border-right: var(--pa-border-width) solid var(--pa-color-border);
  padding: var(--pa-space-4) var(--pa-space-3) var(--pa-safe-bottom);
  overflow-y: auto;
}

.desktop-rail__brand {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  padding: var(--pa-space-2) var(--pa-space-3);
  margin-bottom: var(--pa-space-4);
  border-radius: var(--pa-radius-control);
  color: var(--pa-color-text-primary);
  text-decoration: none;
  font-weight: var(--pa-font-weight-bold);
  font-size: var(--pa-font-size-base);
  min-height: var(--pa-layout-touch-target);
}

.desktop-rail__brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-accent);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-bold);
}

.desktop-rail__group {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-0);
}

.desktop-rail__divider {
  border: none;
  border-top: var(--pa-border-width) solid var(--pa-color-border);
  margin: var(--pa-space-4) var(--pa-space-3);
}

.desktop-rail__item {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: var(--pa-layout-touch-target);
  padding: 0 var(--pa-space-3);
  border-radius: var(--pa-radius-control);
  color: var(--pa-color-text-secondary);
  text-decoration: none;
  font-size: var(--pa-font-size-base);
}

.desktop-rail__item:hover {
  background: var(--pa-color-surface-interactive);
  color: var(--pa-color-text-primary);
}

.desktop-rail__item--active {
  background: var(--pa-color-surface-interactive);
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-medium);
}

.desktop-rail__item:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}

.desktop-rail__icon {
  color: currentColor;
}

.desktop-rail__version {
  margin-top: auto;
  padding: var(--pa-space-4) var(--pa-space-3) 0;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.desktop-rail__version-name {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.desktop-rail__version-env {
  font-size: var(--pa-font-size-xs);
  color: var(--pa-color-text-disabled);
}
</style>
