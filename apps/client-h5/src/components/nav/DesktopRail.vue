<script setup lang="ts">
/**
 * DesktopRail — 68px icon navigation rail for viewports >= 768px
 * (UI_RECONSTRUCTION_DESIGN_FREEZE §4). Primary: 首页 / 搜索 / 地图 / 贡献;
 * secondary: 我的 / 设置. About has moved INTO Settings (no first-level slot).
 * Labels are exposed via native title + aria-label so the rail stays an icon
 * rail, not a sidebar, and no custom tooltip can be clipped by the rail's
 * overflow clamp.
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
// v0.2.7-R1.1 P0-3: the 68px rail only ever shows the compact major.minor
// version. Full "PetAccess v{version} · {env}" stays in title + data
// attributes (accessible metadata), never as persistent rail text.
const compactVersion = version.split("-")[0]!.split(".").slice(0, 2).join(".");
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
      <span class="desktop-rail__brand-mark" aria-hidden="true">
        <PaIcon name="location" size="md" />
      </span>
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
        :title="item.label"
      >
        <PaIcon class="desktop-rail__icon" :name="item.icon" size="lg" />
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
        :title="item.label"
      >
        <PaIcon class="desktop-rail__icon" :name="item.icon" size="lg" />
      </RouterLink>
    </nav>

    <div
      class="desktop-rail__version"
      data-testid="app-version"
      :title="`PetAccess v${version} · ${envLabel}`"
      :data-version="version"
      :data-env="envLabel"
    >
      <span class="desktop-rail__version-compact">v{{ compactVersion }}</span>
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
  /* v0.2.7-R1 P0-1: the rail is a 68px icon rail — it must never grow a
     horizontal scrollbar. overflow-x hidden is the visual clamp; the footer
     text is also width-bounded below so content cannot enlarge the rail. */
  overflow-x: hidden;
}

.desktop-rail__brand {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--pa-space-2) 0;
  margin-bottom: var(--pa-space-4);
  color: var(--pa-color-text-primary);
  text-decoration: none;
  transition:
    background-color var(--pa-motion-fast) var(--pa-motion-ease),
    color var(--pa-motion-fast) var(--pa-motion-ease);
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
  box-shadow: inset 0 0 0 var(--pa-border-width) color-mix(in srgb, var(--pa-color-text-inverse) 24%, transparent);
}

.desktop-rail__group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--pa-space-1);
}

.desktop-rail__divider {
  border: none;
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
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
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
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
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding-top: var(--pa-space-4);
  color: var(--pa-color-text-muted);
}

.desktop-rail__version-compact {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--pa-font-size-xs);
  line-height: 1;
}
</style>
