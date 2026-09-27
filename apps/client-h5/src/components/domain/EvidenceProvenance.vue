<script setup lang="ts">
/**
 * EvidenceProvenance — the five-step provenance chain of a place's evidence
 * record (freeze §9): photo exists → place matched → observed time → source
 * confirmed → human reviewed.
 *
 * Steps derive ONLY from available data; absent fields render 未记录, never
 * invented. The view supplies the three counts; this component turns them
 * into the chain. Pure presentation, no data fetching.
 */
import { computed } from "vue";

interface Props {
  observedCount: number;
  evidenceCount: number;
  reviewedCount: number;
}

const props = defineProps<Props>();

interface ProvenanceStep {
  key: string;
  label: string;
  filled: boolean;
  note: string;
}

const provenance = computed<ProvenanceStep[]>(() => {
  const observed = props.observedCount > 0;
  const reviewed = props.reviewedCount > 0;
  return [
    {
      key: "photo",
      label: "原始图片存在",
      filled: observed,
      note: observed ? "现场记录已收录" : "暂无原始图片",
    },
    {
      key: "place",
      label: "场所匹配",
      filled: observed,
      note: observed ? "记录绑定到该场所" : "尚无绑定记录",
    },
    {
      key: "observed",
      label: "观察时间",
      filled: observed,
      note: observed ? "已记录观察时间" : "暂无观察时间",
    },
    {
      key: "source",
      label: "来源确认",
      filled: props.evidenceCount > 0,
      note: props.evidenceCount > 0 ? `${props.evidenceCount} 条依据` : "暂无依据来源",
    },
    {
      key: "review",
      label: "人工核验",
      filled: reviewed,
      note: reviewed ? "已有人工核验记录" : "尚未完成人工核验",
    },
  ];
});
</script>

<template>
  <section class="evidence-section" data-testid="evidence-provenance" aria-label="证据来源链">
    <h2 class="evidence-section__title">证据来源链</h2>
    <div
      v-for="p in provenance"
      :key="p.key"
      class="surface-row"
      :class="{ 'evidence-provenance__row--filled': p.filled }"
    >
      <span class="evidence-provenance__mark" aria-hidden="true">{{ p.filled ? "●" : "○" }}</span>
      <span class="evidence-provenance__label">{{ p.label }}</span>
      <span class="muted evidence-provenance__note">{{ p.note }}</span>
    </div>
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

.evidence-provenance__mark {
  flex: none;
  width: 1.25rem;
  color: var(--pa-color-text-secondary);
}

.evidence-provenance__row--filled .evidence-provenance__mark {
  color: var(--pa-color-accent);
}

.evidence-provenance__label {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-medium);
}

.evidence-provenance__note {
  text-align: right;
}
</style>
