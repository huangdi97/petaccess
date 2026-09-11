<script setup lang="ts">
import { useRouter } from "vue-router";
import { logout } from "./api";

const router = useRouter();

const nav = [
  { to: "/dashboard", label: "数据质量" },
  { to: "/places", label: "场所" },
  { to: "/rules", label: "规则" },
  { to: "/sources", label: "来源" },
  { to: "/regulations", label: "法规" },
  { to: "/claims", label: "管理方认领" },
  { to: "/disputes", label: "异议" },
  { to: "/observations", label: "观察记录" },
  { to: "/ai-queue", label: "AI 队列" },
  { to: "/conflicts", label: "冲突复核" },
  { to: "/audit", label: "审计日志" },
  { to: "/users", label: "用户" },
];

function onLogout() {
  logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">宠物准入平台 · Admin</div>
      <RouterLink v-for="n in nav" :key="n.to" :to="n.to">{{ n.label }}</RouterLink>
      <div class="spacer"></div>
      <button style="margin: 0 16px; width: calc(100% - 32px)" @click="onLogout">退出登录</button>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>
