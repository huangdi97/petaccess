<script setup lang="ts">
import { computed } from "vue";

defineOptions({ name: "ContributionProgress" });

const props = withDefaults(
  defineProps<{
    step: number;
    total?: number;
  }>(),
  { total: 4 },
);

const stageLabel = computed(
  () => ["选择类型", "填写信息", "核对", "提交"][Math.max(0, Math.min(3, props.step - 1))],
);
</script>

<template>
  <div
    class="contribution-progress"
    role="group"
    :aria-label="`贡献进度：第 ${step} 步，共 ${total} 步`"
    data-ui="contribution-progress"
  >
    <span class="contribution-progress__count" data-testid="contribute-step">
      {{ step }} / {{ total }}
    </span>
    <span class="contribution-progress__stage">{{ stageLabel }}</span>
  </div>
</template>

<style scoped>
.contribution-progress {
  display: flex;
  align-items: center;
  gap: var(--pa-space-4);
  min-height: var(--pa-size-control-sm);
}

.contribution-progress__count {
  font-family: var(--pa-font-family-numeric);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-650);
  letter-spacing: var(--pa-letter-spacing-wide);
  color: var(--pa-color-text-primary);
}

.contribution-progress__stage {
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-secondary);
}
</style>
