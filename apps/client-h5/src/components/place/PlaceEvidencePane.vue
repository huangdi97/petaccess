<script setup lang="ts">
import { computed } from "vue";
/**
 * PlaceEvidencePane — compact evidence view inside the Place dossier.
 *
 * Reality evidence is derived from the published v0.9 event stream, so the
 * evidence pane and Reality timeline cannot disagree by reading two different
 * generations of the data model.
 */
import type { AccessAnswerEvidence, RealityEventView, SourceView } from "@petaccess/client-core";
import {
  displayRealityEventTime,
  realityEventDetail,
  realityEventEvidenceState,
  realityEventHeadline,
  realityEventProvenance,
  realityProvenanceCounts,
  realityEventTimeBasis,
} from "../../consumer/realityEvent";
import EvidenceProvenance from "../domain/EvidenceProvenance.vue";
import EvidenceStatus from "../domain/EvidenceStatus.vue";
import { publicSourceIssuer } from "../../consumer/sourcePrivacy";

const props = defineProps<{
  placeId: string;
  events: RealityEventView[];
  sources: SourceView[];
  ruleEvidence: AccessAnswerEvidence[];
}>();

const provenanceCounts = computed(() => realityProvenanceCounts(props.events));

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
      :raw-material-count="provenanceCounts.rawMaterialCount"
      :place-matched-count="provenanceCounts.placeMatchedCount"
      :time-confirmed-count="provenanceCounts.timeConfirmedCount"
      :source-count="provenanceCounts.sourceCount"
      :reviewed-count="provenanceCounts.reviewedCount"
    />

    <section class="place-section" data-testid="evidence-items" aria-label="现场证据事实">
      <h2 class="place-section__title">现场证据事实</h2>
      <div v-for="event in events" :key="event.id" class="surface-row evidence-item">
        <div class="evidence-item__main">
          <EvidenceStatus :state="realityEventEvidenceState(event)" />
          <time class="muted">{{ displayRealityEventTime(event) }}</time>
        </div>
        <p class="evidence-item__text">{{ realityEventHeadline(event) }}</p>
        <p v-if="realityEventDetail(event)" class="muted evidence-item__detail">
          {{ realityEventDetail(event) }}
        </p>
        <p v-if="realityEventProvenance(event)" class="muted evidence-item__provenance">
          {{ realityEventProvenance(event) }}
        </p>
        <p v-if="event.event_type === 'staff_response'" class="muted evidence-item__privacy">
          工作人员原话如有提交，仅用于核验；公开页面不展示可能包含个人身份的信息。
        </p>
        <p class="muted evidence-item__time-basis">{{ realityEventTimeBasis(event) }}</p>
      </div>
      <p v-if="!events.length" class="muted">暂无经核验现场事实（未收录不代表没有动物）。</p>
      <RouterLink class="btn-inline" :to="`/place/${props.placeId}/evidence`">
        查看完整证据记录 →
      </RouterLink>
    </section>

    <section class="place-section" data-testid="place-rule-evidence" aria-label="规则依据">
      <h2 class="place-section__title">规则依据</h2>
      <div
        v-for="(item, index) in ruleEvidence"
        :key="item.rule_id + '-' + index"
        class="surface-row"
      >
        <span class="evidence-source__issuer">{{
          publicSourceIssuer(item.source_type, item.issuer)
        }}</span>
        <span class="muted evidence-source__meta">
          {{ item.provenance_statement || LABELS[item.source_type ?? ""] || "规则来源待核验" }}
        </span>
      </div>
      <p v-if="!ruleEvidence.length" class="muted">
        暂无可靠规则依据。规则依据不足不影响下方已核验现场事实的独立展示。
      </p>
    </section>

    <section class="place-section" data-testid="evidence-sources" aria-label="来源列表">
      <h2 class="place-section__title">来源</h2>
      <div v-for="source in sources" :key="source.id" class="surface-row">
        <span class="evidence-source__issuer">{{
          publicSourceIssuer(source.source_type, source.issuer)
        }}</span>
        <span class="muted evidence-source__meta">
          {{ LABELS[source.source_type] ?? "其他来源" }} · 收集于
          {{ source.collected_at.slice(0, 10) }}
        </span>
      </div>
      <p v-if="!sources.length" class="muted">
        原始材料可能受隐私或许可限制；现场事实行已显示可公开的来源类型与核验信息。
      </p>
    </section>
  </div>
</template>

<style scoped src="./PlaceEvidencePane.css"></style>
