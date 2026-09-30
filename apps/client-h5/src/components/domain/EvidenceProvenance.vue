<script setup lang="ts">
/**
 * EvidenceProvenance — the five-step provenance chain of a place's evidence
 * record (§39): 原始证据 → 地点匹配 → 时间确认 → 来源确认 → 人工核验.
 *
 * Blueprint geometry: marker column = 24px, content column = remaining,
 * marker x identical across steps, continuous vertical rail, step gap
 * 28–36px (marker 24px col / rail / gap are part of the O2 contract).
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
      label: "原始证据",
      filled: observed,
      note: observed ? "现场记录已收录" : "暂无原始证据",
    },
    {
      key: "place",
      label: "地点匹配",
      filled: observed,
      note: observed ? "记录绑定到该场所" : "尚无绑定记录",
    },
    {
      key: "observed",
      label: "时间确认",
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
  <section
    class="evidence-section"
    data-testid="evidence-provenance"
    data-ui="evidence-provenance"
    aria-label="证据来源链"
  >
    <h2 class="evidence-section__title">证据来源链</h2>
    <ol class="provenance-rail" data-ui="evidence-prov-rail">
      <span class="provenance-rail__line" data-ui="evidence-prov-rail-line" aria-hidden="true"></span>
      <li
        v-for="p in provenance"
        :key="p.key"
        class="provenance-step"
        :class="{ 'provenance-step--filled': p.filled }"
        data-ui="evidence-prov-step"
      >
        <span class="provenance-step__mark" aria-hidden="true" data-ui="evidence-prov-marker"></span>
        <div class="provenance-step__body">
          <span class="provenance-step__label">{{ p.label }}</span>
          <span class="muted provenance-step__note">{{ p.note }}</span>
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

/* §39: marker col 24px + content column, continuous rail, gap 28–36. */
.provenance-rail {
  position: relative;
  margin: 0;
  padding: 0;
  list-style: none;
}

.provenance-rail__line {
  content: "";
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
  margin-bottom: 32px;
  /* Events are ledger rows, not cards. */
  background: transparent;
  border-radius: 0;
  box-shadow: none;
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

.provenance-step__label {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-medium);
}

.provenance-step__note {
  font-size: var(--pa-font-size-sm);
}
</style>