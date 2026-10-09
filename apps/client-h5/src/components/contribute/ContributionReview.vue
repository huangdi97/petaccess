<script setup lang="ts">
/**
 * Step 3 — submission review.
 *
 * This is deliberately read-only: it mirrors the structured fields already
 * captured by the form and gives the user one chance to spot scope/time/type
 * mistakes before the API write. It never invents or interprets facts.
 */
defineOptions({ name: "ContributionReview" });

defineProps<{
  items: { label: string; value: string }[];
  guard?: string;
}>();
</script>

<template>
  <section class="contribution-review" data-testid="contribution-review">
    <h3>提交前核对</h3>
    <p class="muted contribution-review__lead">
      请确认场所、范围、时间和事实类型。返回修改不会提交任何数据。
    </p>
    <dl class="contribution-review__facts">
      <div v-for="item in items" :key="item.label" class="contribution-review__row">
        <dt>{{ item.label }}</dt>
        <dd>{{ item.value }}</dd>
      </div>
    </dl>
    <p class="contribution-review__guard">
      {{ guard || "确认提交后内容进入人工核验；审核通过前不会改变公开规则或现场事实。" }}
    </p>
  </section>
</template>

<style scoped>
.contribution-review {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
  padding: var(--pa-space-4) 0;
}

.contribution-review h3,
.contribution-review__lead,
.contribution-review__guard {
  margin: 0;
}

.contribution-review h3 {
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
}

.contribution-review__facts {
  margin: 0;
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.contribution-review__row {
  display: grid;
  grid-template-columns: minmax(96px, 0.35fr) minmax(0, 1fr);
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.contribution-review__row dt {
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
}

.contribution-review__row dd {
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  overflow-wrap: anywhere;
}

.contribution-review__guard {
  padding-left: var(--pa-space-3);
  border-left: var(--pa-border-width-strong) solid var(--pa-color-evidence-pending);
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

@media (max-width: 767px) {
  .contribution-review__row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }
}
</style>
