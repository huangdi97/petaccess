<script setup lang="ts">
defineOptions({ name: "ContributionProgress" });

withDefaults(
  defineProps<{
    step: number;
    total?: number;
  }>(),
  { total: 4 },
);
</script>

<template>
  <div
    class="contribution-progress"
    role="group"
    :aria-label="`贡献进度：第 ${step} 步，共 ${total} 步`"
    data-ui="contribution-progress"
  >
    <div
      v-for="index in total"
      :key="index"
      class="contribution-progress__segment"
      :class="{ 'contribution-progress__segment--active': index <= step }"
      aria-hidden="true"
    />
    <span class="muted contribution-progress__label" data-testid="contribute-step">
      步骤 {{ step }} / {{ total }}
    </span>
  </div>
</template>

<style scoped>
.contribution-progress {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
}

.contribution-progress__segment {
  flex: 1 1 0;
  height: 4px;
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-border);
}

.contribution-progress__segment--active {
  background: var(--pa-color-accent);
}

.contribution-progress__label {
  margin-left: var(--pa-space-2);
  white-space: nowrap;
  font-size: var(--pa-font-size-sm);
  letter-spacing: var(--pa-letter-spacing-wide);
}
</style>
