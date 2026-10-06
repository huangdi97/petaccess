<script setup lang="ts">
/**
 * EvidenceProvenance — factual five-step provenance rail.
 *
 * Every step is driven by the published RealityEvent metadata. A later stage
 * never implies an earlier one: source confirmation, place matching, time
 * evidence and human review are independent provenance dimensions.
 */
import { computed } from "vue";

const props = defineProps<{
  rawMaterialCount: number;
  placeMatchedCount: number;
  timeConfirmedCount: number;
  sourceCount: number;
  reviewedCount: number;
}>();

interface ProvenanceStep {
  key: string;
  label: string;
  count: number;
  note: string;
}

const provenance = computed<ProvenanceStep[]>(() => [
  {
    key: "material",
    label: "原始材料",
    count: props.rawMaterialCount,
    note: props.rawMaterialCount
      ? `${props.rawMaterialCount} 条事实带有可追溯材料或来源锚点`
      : "暂无可公开确认的原始材料锚点",
  },
  {
    key: "place",
    label: "地点匹配",
    count: props.placeMatchedCount,
    note: props.placeMatchedCount
      ? `${props.placeMatchedCount} 条事实已绑定到当前场所或明确子区域`
      : "地点匹配依据待补充",
  },
  {
    key: "time",
    label: "时间确认",
    count: props.timeConfirmedCount,
    note: props.timeConfirmedCount
      ? `${props.timeConfirmedCount} 条事实具有事件时间依据`
      : "仅有发布时间或未确认事件时间",
  },
  {
    key: "source",
    label: "来源确认",
    count: props.sourceCount,
    note: props.sourceCount ? `${props.sourceCount} 个可追溯来源 / 证据锚点` : "来源待补充",
  },
  {
    key: "review",
    label: "人工核验",
    count: props.reviewedCount,
    note: props.reviewedCount
      ? `${props.reviewedCount} 条事实已完成人工核验`
      : "尚未完成人工核验",
  },
]);

function stepStatus(step: ProvenanceStep): string {
  return step.count > 0 ? "已记录" : "待补充";
}
</script>

<template>
  <section
    class="evidence-section"
    data-testid="evidence-provenance"
    data-ui="evidence-provenance"
    aria-label="现场证据来源链"
  >
    <h2 class="evidence-section__title">现场证据来源链</h2>
    <p class="muted evidence-section__intro">
      五个环节分别记录，不会因为“已人工核验”就自动推断地点、时间或来源也已经充分确认。
    </p>
    <ol class="provenance-rail" data-ui="evidence-prov-rail">
      <span
        class="provenance-rail__line"
        data-ui="evidence-prov-rail-line"
        aria-hidden="true"
      ></span>
      <li
        v-for="step in provenance"
        :key="step.key"
        class="provenance-step"
        :class="step.count > 0 ? 'provenance-step--filled' : 'provenance-step--pending'"
        :data-step-state="step.count > 0 ? 'complete' : 'pending'"
        data-ui="evidence-prov-step"
      >
        <span class="provenance-step__mark" aria-hidden="true" data-ui="evidence-prov-marker"></span>
        <div class="provenance-step__body">
          <span class="provenance-step__title-row">
            <span class="provenance-step__label">{{ step.label }}</span>
            <span
              class="provenance-step__status"
              :data-step-state="step.count > 0 ? 'complete' : 'pending'"
            >
              {{ stepStatus(step) }}
            </span>
          </span>
          <span class="muted provenance-step__note">{{ step.note }}</span>
        </div>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.evidence-section {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.evidence-section__title {
  margin: var(--pa-space-4) 0 var(--pa-space-1);
  font-size: var(--pa-font-size-lg);
  color: var(--pa-color-text-primary);
}

.evidence-section__intro {
  margin: 0 0 var(--pa-space-3);
  max-width: 680px;
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

.provenance-rail {
  position: relative;
  margin: 0;
  padding: 0;
  list-style: none;
}

.provenance-rail__line {
  position: absolute;
  left: 11px;
  top: 6px;
  bottom: 6px;
  width: 2px;
  background: var(--pa-color-border-subtle);
  pointer-events: none;
}

.provenance-step {
  position: relative;
  display: grid;
  grid-template-columns: 24px 1fr;
  gap: 0 var(--pa-space-3);
  margin-bottom: var(--pa-space-6);
}

.provenance-step:last-child {
  margin-bottom: 0;
}

.provenance-step__mark {
  width: 12px;
  height: 12px;
  margin: 4px auto 0;
  border-radius: 50%;
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-text-secondary);
}

.provenance-step--filled .provenance-step__mark {
  border-color: var(--pa-color-accent);
  background: var(--pa-color-accent);
}

.provenance-step__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: 2px;
}

.provenance-step__title-row {
  display: flex;
  align-items: baseline;
  gap: var(--pa-space-2);
}

.provenance-step__label {
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
}

.provenance-step__status,
.provenance-step__note {
  font-size: var(--pa-font-size-sm);
}

.provenance-step__status {
  color: var(--pa-color-text-muted);
}

.provenance-step__status[data-step-state="complete"] {
  color: var(--pa-color-text-secondary);
}

.provenance-step__note {
  line-height: var(--pa-line-height-20);
}
</style>
