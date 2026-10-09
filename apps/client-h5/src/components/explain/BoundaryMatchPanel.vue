<script setup lang="ts">
import type { BoundaryMatchResult } from "@petaccess/client-core";
import { BOUNDARY_ATTRIBUTE_LABELS, BOUNDARY_STANCE_LABELS } from "../../consumer/boundaryOptions";

defineProps<{ boundary: BoundaryMatchResult | null; note: string }>();

const VERDICT_TEXT: Record<string, string> = {
  MATCH: "符合",
  CONFLICT: "不符合",
  UNKNOWN: "信息不足",
};
</script>

<template>
  <section class="boundary-panel" data-testid="boundary-section">
    <div class="boundary-panel__head">
      <div>
        <h2>与我的共处边界比对</h2>
        <p class="muted">这是个人偏好的逐项比对，无总分，也不是场所评分。</p>
      </div>
      <RouterLink class="btn-inline" to="/boundary">设置边界 →</RouterLink>
    </div>

    <p v-if="note" class="muted" data-testid="boundary-note">{{ note }}</p>

    <template v-if="boundary">
      <p class="boundary-panel__summary muted">
        共 {{ boundary.results.length }} 项 · 符合 {{ boundary.summary.match }} · 不符合
        {{ boundary.summary.conflict }} · 信息不足 {{ boundary.summary.unknown }}
      </p>

      <div
        v-for="result in boundary.results"
        :key="result.attribute"
        class="boundary-panel__row"
        data-testid="boundary-item"
      >
        <div>
          <strong>{{ BOUNDARY_ATTRIBUTE_LABELS[result.attribute] ?? "共处条件" }}</strong>
          <span class="muted"> · {{ BOUNDARY_STANCE_LABELS[result.stance] ?? "个人偏好" }} </span>
        </div>
        <span class="boundary-panel__verdict">
          {{ VERDICT_TEXT[result.verdict] ?? "信息不足" }}
        </span>
      </div>
    </template>
  </section>
</template>

<style scoped>
.boundary-panel {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
  margin-bottom: var(--pa-space-3);
}

.boundary-panel__head h2 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.boundary-panel__head p {
  margin: var(--pa-space-1) 0 0;
}

.boundary-panel__summary {
  margin-bottom: var(--pa-space-2);
}

.boundary-panel__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pa-space-4);
  min-height: 48px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-panel__verdict {
  flex: 0 0 auto;
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .boundary-panel__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .boundary-panel__row {
    align-items: flex-start;
  }
}
</style>
