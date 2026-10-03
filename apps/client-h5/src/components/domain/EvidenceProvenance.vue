<script setup lang="ts">
/**
 * EvidenceProvenance — the five-step provenance chain of a place's evidence
 * record (§39): 原始证据 → 地点匹配 → 时间确认 → 来源确认 → 人工核验.
 *
 * v0.2.4 §39：保留当前成功的 5 步 rail，并增强为每步「形状 + 状态文字 + 一句解释」。
 * 步骤只从可用数据推导；缺失渲染「待补充」，不猜测（空态仍保留 5 步结构）。
 *
 * Blueprint geometry (O2): marker column = 24px, content column = remaining,
 * marker x identical across steps, continuous vertical rail, step gap 28–36px.
 */
import { computed } from "vue";

interface Props {
  observedCount: number;
  ruleEvidenceCount: number;
  reviewedCount: number;
}

const props = defineProps<Props>();

interface ProvenanceStep {
  key: string;
  label: string;
  /** complete / pending（当前无历史记录则 pending）。 */
  filled: boolean;
  /** 每步一句解释（§39）。 */
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
      filled: props.ruleEvidenceCount > 0,
      note:
        props.ruleEvidenceCount > 0
          ? `${props.ruleEvidenceCount} 条规则依据`
          : "正式规则依据：0（来源待补充）",
    },
    {
      key: "review",
      label: "人工核验",
      filled: reviewed,
      note: reviewed ? "已有人工核验记录" : "尚未完成人工核验",
    },
  ];
});

/** §39：每步状态文字 —— complete / pending。 */
function stepStatus(p: ProvenanceStep): string {
  return p.filled ? "已完成" : "待补充";
}
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
      <span
        class="provenance-rail__line"
        data-ui="evidence-prov-rail-line"
        aria-hidden="true"
      ></span>
      <li
        v-for="p in provenance"
        :key="p.key"
        class="provenance-step"
        :class="p.filled ? 'provenance-step--filled' : 'provenance-step--pending'"
        :data-step-state="p.filled ? 'complete' : 'pending'"
        data-ui="evidence-prov-step"
      >
        <span
          class="provenance-step__mark"
          aria-hidden="true"
          data-ui="evidence-prov-marker"
        ></span>
        <div class="provenance-step__body">
          <span class="provenance-step__title-row">
            <span class="provenance-step__label">{{ p.label }}</span>
            <span
              class="provenance-step__status"
              :data-step-state="p.filled ? 'complete' : 'pending'"
              >{{ stepStatus(p) }}</span
            >
          </span>
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
  margin-bottom: var(--pa-space-5);
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.provenance-step:last-child {
  margin-bottom: 0;
}

/* §39 形状：pending = 空心圆 + 中性边框；complete = 实心 accent。 */
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

.provenance-step__status {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.provenance-step__status[data-step-state="complete"] {
  color: var(--pa-color-text-secondary);
}

.provenance-step__note {
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}
</style>
