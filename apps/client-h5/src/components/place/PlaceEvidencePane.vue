<script setup lang="ts">
/**
 * PlaceEvidencePane — Place Dossier 证据 view（v0.2.4 §25）。
 * 复用 EvidenceRecord / Provenance component（EvidenceProvenance），不复制来源表。
 */
import type { ObservationView, SourceView } from "@petaccess/client-core";
import { animalScopeLabel, ruleActionLabel, staffActionLabel } from "../../consumer/labels";
import EvidenceProvenance from "../domain/EvidenceProvenance.vue";
import EvidenceStatus from "../domain/EvidenceStatus.vue";

const props = defineProps<{
  placeId: string;
  observations: ObservationView[];
  sources: SourceView[];
  ruleEvidenceCount: number;
  reviewedCount: number;
}>();

function evidenceStateFor(o: ObservationView): "verified" | "pending" | "disputed" | "historical" {
  if (o.dispute_status === "DISPUTED") return "disputed";
  if (o.dispute_status && o.dispute_status !== "NONE") return "pending";
  return "verified";
}

const LABELS: Record<string, string> = {
  statute_or_regulation: "法规",
  government_service: "政府服务",
  official_operator_policy: "管理方发布",
  onsite_signage: "现场标识",
  certified_verifier: "认证核验方",
  ordinary_user: "普通用户",
  external_web_reference: "外部网页",
  imported_dataset: "导入数据",
  verified: "已核验来源",
  self_declared: "自行声明",
  unverified: "未核验",
};
</script>

<template>
  <div data-ui="place-evidence-view" data-testid="place-evidence-view">
    <EvidenceProvenance
      :observed-count="observations.length"
      :rule-evidence-count="ruleEvidenceCount"
      :reviewed-count="reviewedCount"
    />

    <section class="place-section" data-testid="evidence-items" aria-label="证据条目">
      <h2 class="place-section__title">现场证据条目</h2>
      <div v-for="o in observations" :key="o.id" class="surface-row evidence-item">
        <div class="evidence-item__main">
          <EvidenceStatus :state="evidenceStateFor(o)" />
          <time class="muted"
            >{{ o.occurred_at.slice(0, 10) }} {{ o.occurred_at.slice(11, 16) }}</time
          >
        </div>
        <p class="evidence-item__text">
          {{ animalScopeLabel(o.animal_scope) }} · {{ ruleActionLabel(o.observed_action) }}
          <span v-if="o.staff_action" class="muted"
            >（工作人员：{{ staffActionLabel(o.staff_action) }}）</span
          >
        </p>
      </div>
      <p v-if="!observations.length" class="muted">暂无现场记录（未收录不代表没有动物）。</p>
      <RouterLink class="btn-inline" :to="`/place/${props.placeId}/evidence`">
        查看全部证据 →
      </RouterLink>
    </section>

    <section class="place-section" data-testid="evidence-sources" aria-label="来源列表">
      <h2 class="place-section__title">来源</h2>
      <div v-for="s in sources" :key="s.id" class="surface-row">
        <span class="evidence-source__issuer">{{ s.issuer }}</span>
        <span class="muted evidence-source__meta"
          >{{ LABELS[s.source_type] ?? "其他来源" }} · 收集于
          {{ s.collected_at.slice(0, 10) }}</span
        >
      </div>
      <p v-if="!sources.length" class="muted">暂无来源记录。</p>
    </section>
  </div>
</template>

<style scoped>
.place-section {
  margin-bottom: var(--pa-space-5);
}
.place-section__title {
  margin: var(--pa-space-4) 0 var(--pa-space-1);
  font-size: var(--pa-font-size-lg);
  color: var(--pa-color-text-primary);
}
.surface-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.surface-row:last-child {
  border-bottom: none;
}
.evidence-item {
  flex-direction: column;
  align-items: stretch;
  gap: var(--pa-space-1);
}
.evidence-item__main {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
}
.evidence-item__text {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}
.evidence-source__issuer {
  color: var(--pa-color-text-primary);
}
.evidence-source__meta {
  text-align: right;
  font-size: var(--pa-font-size-sm);
}
</style>
