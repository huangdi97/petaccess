<script setup lang="ts">
/**
 * DesktopRail — 68px icon navigation rail for viewports >= 768px
 * (UI_RECONSTRUCTION_DESIGN_FREEZE §4). Primary: 首页 / 搜索 / 地图 / 贡献;
 * secondary: 我的 / 设置. About has moved INTO Settings (no first-level slot).
 * Labels appear as tooltips so the rail stays an icon rail, not a sidebar.
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
    data-ui="app-rail"
    :style="{ zIndex: `var(${Z_INDEX.sticky})` }"
    aria-label="主导航"
  >
    <RouterLink to="/" class="desktop-rail__brand" aria-label="PetAccess 首页">
      <span class="desktop-rail__brand-mark" aria-hidden="true">PA</span>
    </RouterLink>

    <nav class="desktop-rail__group" aria-label="主要页面">
      <RouterLink
        v-for="item in PRIMARY"
        :key="item.to"
        :to="item.to"
        class="desktop-rail__item"
        :class="{ 'desktop-rail__item--active': isActive(item.to) }"
        :aria-current="isActive(item.to) ? 'page' : undefined"
        :aria-label="item.label"
      >
        <PaIcon class="desktop-rail__icon" :name="item.icon" size="lg" />
        <span class="desktop-rail__tip" aria-hidden="true">{{ item.label }}</span>
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
        :aria-label="item.label"
      >
        <PaIcon class="desktop-rail__icon" :name="item.icon" size="lg" />
        <span class="desktop-rail__tip" aria-hidden="true">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="desktop-rail__version" data-testid="app-version">
      <span class="desktop-rail__version-name">PetAccess v{{ version }}</span>
      <span class="desktop-rail__version-env" aria-hidden="true">{{ envLabel }}</span>
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
  padding: var(--pa-space-4) 0 var(--pa-safe-bottom);
  overflow-y: auto;
}

.desktop-rail__brand {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--pa-space-2) 0;
  margin-bottom: var(--pa-space-4);
  color: var(--pa-color-text-primary);
  text-decoration: none;
}

.desktop-rail__brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-accent);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-bold);
}

.desktop-rail__group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--pa-space-1);
}

.desktop-rail__divider {
  border: none;
  border-top: var(--pa-border-width) solid var(--pa-color-border);
  width: calc(100% - var(--pa-space-6));
  margin: var(--pa-space-4) auto;
}

.desktop-rail__item {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-layout-touch-target);
  height: var(--pa-layout-touch-target);
  border-radius: var(--pa-radius-control);
  color: var(--pa-color-text-secondary);
  text-decoration: none;
}

.desktop-rail__item:hover {
  background: var(--pa-color-surface-interactive);
  color: var(--pa-color-text-primary);
}

.desktop-rail__item--active {
  background: var(--pa-color-surface-interactive);
  color: var(--pa-color-accent);
}

.desktop-rail__item:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}

.desktop-rail__icon {
  color: currentColor;
}

/* Tooltip label — appears on hover/focus, never takes rail space. */
.desktop-rail__tip {
  position: absolute;
  left: calc(100% + var(--pa-space-2));
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  padding: var(--pa-space-1) var(--pa-space-2);
  border-radius: var(--pa-radius-sm);
  background: var(--pa-color-text-primary);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-sm);
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--pa-motion-fast) var(--pa-motion-ease);
  z-index: var(--pa-z-sticky);
}

.desktop-rail__item:hover .desktop-rail__tip,
.desktop-rail__item:focus-visible .desktop-rail__tip {
  opacity: 1;
}

.desktop-rail__version {
  margin-top: auto;
  display: flex;
  justify-content: center;
  padding-top: var(--pa-space-4);
}

.desktop-rail__version-name {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.desktop-rail__version-env {
  font-size: var(--pa-font-size-xs);
  color: var(--pa-color-text-muted);
}
</style>
