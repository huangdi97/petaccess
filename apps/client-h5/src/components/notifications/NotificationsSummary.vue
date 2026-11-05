<script setup lang="ts">
defineProps<{
  ruleCount: number;
  realityCount: number;
  totalCount: number;
}>();
</script>

<template>
  <div class="notifications-summary" aria-label="关注摘要">
    <div>
      <span>规则变化</span>
      <strong>{{ ruleCount }}</strong>
    </div>
    <div>
      <span>现场更新</span>
      <strong>{{ realityCount }}</strong>
    </div>
    <div>
      <span>总关注</span>
      <strong>{{ totalCount }}</strong>
    </div>
  </div>
</template>

<style scoped>
.notifications-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-5);
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.notifications-summary > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.notifications-summary span {
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-sm);
}

.notifications-summary strong {
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-xl);
  line-height: var(--pa-line-height-26);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 767px) {
  .notifications-summary {
    margin-top: var(--pa-space-4);
  }
}
</style>
