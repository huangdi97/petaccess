<script setup lang="ts">
// @ui-static NotFoundView — 404 状态视图，无数据加载（M3 E1 静态声明）。
import { useRouter } from "vue-router";
import AppShell from "../components/AppShell.vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import PaEmptyState from "../components/ui/PaEmptyState.vue";

defineOptions({ name: "NotFoundView" });

const router = useRouter();
</script>

<template>
  <AppShell>
    <DesktopContentContainer mode="single-column">
      <h1 class="visually-hidden">页面不存在</h1>
      <PaEmptyState
        data-testid="not-found"
        icon="search"
        title="页面不存在"
        description="你访问的页面不存在或已被移动。返回首页继续查找场所。"
        primary-label="返回首页"
        @primary="router.push('/')"
      />
    </DesktopContentContainer>
  </AppShell>
</template>

<style scoped>
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  margin: -1px;
  padding: 0;
  border: 0;
  white-space: nowrap;
}
</style>
