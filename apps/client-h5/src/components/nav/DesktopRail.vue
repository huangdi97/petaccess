<script setup lang="ts">
/**
 * DesktopRail — 68px icon navigation rail for viewports >= 768px
 * (UI_RECONSTRUCTION_DESIGN_FREEZE §4). Primary: 首页 / 搜索 / 地图 / 贡献;
 * secondary: 我的 / 设置. About has moved INTO Settings (no first-level slot).
 * Short visible labels supplement native title + aria-label so first-time
 * users can recognize destinations without guessing icons. The rail remains
 * a compact 68px navigation surface, never a full sidebar.
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
        <span class="desktop-rail__caption" aria-hidden="true">{{ item.label }}</span>
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
        <span class="desktop-rail__caption" aria-hidden="true">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<style scoped src="./DesktopRail.css"></style>
