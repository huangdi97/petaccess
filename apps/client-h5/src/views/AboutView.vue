<script setup lang="ts">
/**
 * AboutView — 关于: what PetAccess is, what it is not, and version info.
 * Desktop rail 关于 destination (V020_APP_SHELL_SPEC §16).
 */
import AppShell from "../components/AppShell.vue";
import PaIcon from "../components/ui/PaIcon.vue";

const version = import.meta.env.VITE_APP_VERSION ?? "0.2.0-dev";

const PRINCIPLES = [
  { icon: "document" as const, text: "规则来自已核验来源；UNKNOWN 不等于允许或禁止。" },
  { icon: "eye" as const, text: "现场记录是独立的「事实」维度，不等于场所政策。" },
  { icon: "shield" as const, text: "证据链可追溯；AI/OCR 只生成待审候选，不是最终判定。" },
];
</script>

<template>
  <AppShell>
    <h1 class="title" data-testid="about-title">关于 PetAccess</h1>
    <p class="muted">
      PetAccess 是城市公共空间动物共处信息工具：你去之前，先查这里的规则与经核验的现场记录。
    </p>

    <section class="panel" aria-label="产品原则">
      <div v-for="(p, i) in PRINCIPLES" :key="i" class="principle-row">
        <PaIcon :name="p.icon" size="md" class="principle-icon" />
        <span>{{ p.text }}</span>
      </div>
    </section>

    <section class="panel" aria-label="版本">
      <div class="principle-row">
        <PaIcon name="info" size="md" class="principle-icon" />
        <span>当前版本 v{{ version }}</span>
      </div>
      <p class="muted">试点区域：上海 · 试点。产品处于开发预览阶段。</p>
    </section>

    <footer class="muted">现场记录与官方规则分开保存；本产品不做场所评分与排名。</footer>
  </AppShell>
</template>

<style scoped>
.title {
  font-size: var(--pa-font-size-2xl);
  margin: 0 0 var(--pa-space-2);
}

.principle-row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-base);
}

.principle-row + .principle-row {
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.principle-icon {
  flex: none;
  color: var(--pa-color-text-secondary);
}
</style>
