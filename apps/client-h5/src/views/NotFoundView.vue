<script setup lang="ts">
// @ui-static NotFoundView — static route fallback, no external data request.
import AppShell from "../components/AppShell.vue";
</script>

<template>
  <AppShell>
    <main class="not-found" data-testid="not-found">
      <p class="not-found__code">404</p>
      <h1>这个页面不存在</h1>
      <p class="muted">
        链接可能已经失效，也可能是地址输入有误。你可以回到查询入口，或直接继续搜索场所。
      </p>
      <div class="not-found__actions">
        <RouterLink class="btn primary" to="/">返回首页</RouterLink>
        <RouterLink class="btn-inline" to="/search">搜索场所 →</RouterLink>
      </div>
    </main>
  </AppShell>
</template>

<style scoped>
.not-found {
  max-width: 560px;
  padding-top: var(--pa-space-7);
}

.not-found__code {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-650);
  letter-spacing: var(--pa-letter-spacing-wide);
  color: var(--pa-color-text-muted);
}

.not-found h1 {
  margin-bottom: var(--pa-space-2);
}

.not-found > p:last-of-type {
  max-width: 520px;
  line-height: var(--pa-line-height-23);
}

.not-found__actions {
  display: flex;
  align-items: center;
  gap: var(--pa-space-4);
  margin-top: var(--pa-space-5);
}

@media (max-width: 767px) {
  .not-found {
    padding-top: var(--pa-space-5);
  }

  .not-found__actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
