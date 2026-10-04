<script setup lang="ts">
// @ui-static AboutView — legacy deep link; canonical product explanation lives in Settings.
import AppShell from "../components/AppShell.vue";
import PaIcon from "../components/ui/PaIcon.vue";

const version = import.meta.env.VITE_APP_VERSION ?? "0.2.0-dev";

const PRINCIPLES = [
  { icon: "document" as const, title: "规则", text: "说明当前查询适用的允许、限制与条件。" },
  { icon: "eye" as const, title: "现场", text: "记录实际观察到的事实，与正式规则分开。" },
  { icon: "shield" as const, title: "证据", text: "保留来源、时间和核验状态，让结论可追溯。" },
];
</script>

<template>
  <AppShell>
    <header class="about-head">
      <h1 data-testid="about-title">关于 PetAccess</h1>
      <p class="muted">
        城市公共空间动物通行规则与现场事实查询工具。我们不替你评价一个场所，只把规则、现场和依据讲清楚。
      </p>
    </header>

    <section class="about-principles" aria-label="产品原则">
      <div v-for="p in PRINCIPLES" :key="p.title" class="principle-row">
        <PaIcon :name="p.icon" size="md" class="principle-icon" />
        <div>
          <strong>{{ p.title }}</strong>
          <p class="muted">{{ p.text }}</p>
        </div>
      </div>
    </section>

    <section class="about-meta" aria-label="版本">
      <p>当前版本 v{{ version }}</p>
      <p class="muted">上海试点 · 开发预览阶段</p>
      <RouterLink class="btn-inline" to="/settings">查看设置与完整方法说明 →</RouterLink>
    </section>

    <footer class="muted">现场记录与正式规则分开保存；PetAccess 不做场所评分与排名。</footer>
  </AppShell>
</template>

<style scoped>
.about-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.about-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.about-principles {
  padding: var(--pa-space-4) 0;
}

.principle-row {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: var(--pa-space-3);
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.principle-row p {
  margin: var(--pa-space-1) 0 0;
}

.principle-icon {
  color: var(--pa-color-text-secondary);
}

.about-meta {
  padding: var(--pa-space-5) 0;
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.about-meta p {
  margin: 0 0 var(--pa-space-1);
}

footer {
  padding-top: var(--pa-space-5);
  font-size: var(--pa-font-size-sm);
}
</style>
