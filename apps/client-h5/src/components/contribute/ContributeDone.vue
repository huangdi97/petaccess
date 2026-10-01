<script setup lang="ts">
/**
 * ContributeDone — M7 submission result（v0.2.5 §34）。
 * 成功态 =「已提交待核验」，明确说明审核完成前不会改变场所规则结论；
 * 绝不把提交成功误写成规则已变更。
 */
defineOptions({ name: "ContributeDone" });

defineProps<{ msg: string; placeId: string }>();
defineEmits<{ continue: [] }>();
</script>

<template>
  <section class="done" data-testid="contribute-result">
    <h2 class="done__title">已提交待核验</h2>
    <p class="done__body">感谢提供事实记录。审核完成前，它不会直接改变场所规则结论。</p>

    <div class="done__actions">
      <RouterLink class="btn-inline" :to="{ name: 'mine' }" data-testid="done-mine">
        查看我的贡献 →
      </RouterLink>
      <RouterLink
        class="btn-inline"
        :to="{ name: 'place', params: { id: placeId } }"
        data-testid="done-place"
      >
        返回场所 →
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.done {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--pa-space-5) 0;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
}
.done__title {
  margin: 0;
  font-size: var(--pa-font-size-24);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-32);
  color: var(--pa-color-text-primary);
}
.done__body {
  margin: 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-secondary);
}
.done__actions {
  display: flex;
  align-items: center;
  gap: var(--pa-space-4);
  margin-top: var(--pa-space-2);
}
</style>
