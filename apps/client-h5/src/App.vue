<script setup lang="ts">
import { RouterView } from "vue-router";
</script>

<template>
  <RouterView />
  <!--
    Consumer UX Baseline v1 / §22–23: 首页 · 地图 · 贡献 · 我的
    首页 is the Decision Home (search-first); 地图 is its own tab.
  -->
  <nav class="tabbar">
    <RouterLink to="/">首页</RouterLink>
    <RouterLink to="/map">地图</RouterLink>
    <RouterLink to="/contribute">贡献</RouterLink>
    <RouterLink to="/mine">我的</RouterLink>
  </nav>
</template>
