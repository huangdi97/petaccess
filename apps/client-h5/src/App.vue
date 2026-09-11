<script setup lang="ts">
import { RouterView } from "vue-router";
</script>

<template>
  <RouterView />
  <nav class="tabbar">
    <RouterLink to="/">地图</RouterLink>
    <RouterLink to="/search">搜索</RouterLink>
    <RouterLink to="/pet/new">贡献</RouterLink>
    <RouterLink to="/mine">我的</RouterLink>
  </nav>
</template>
