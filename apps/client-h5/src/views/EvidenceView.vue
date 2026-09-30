<script setup lang="ts">
/**
 * EvidenceView — Evidence Record + Provenance (freeze §9).
 * Provenance (photo → place → observed → source → human review) derives ONLY
 * from available data; absent fields render 未记录, never invented. The
 * observations API exposes no media URLs, so a muted note replaces imagery.
 *
 * Composition: the provenance chain lives in EvidenceProvenance; this view
 * keeps data loading and the time-record / items / sources sections.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, type ObservationView, type SourceView } from "@petaccess/client-core";
import { animalScopeLabel, ruleActionLabel, staffActionLabel } from "../consumer/labels";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import EvidenceMeta from "../components/domain/EvidenceMeta.vue";
import EvidenceStatus from "../components/domain/EvidenceStatus.vue";
import EvidenceProvenance from "../components/domain/EvidenceProvenance.vue";
import { presentDescription } from "../errors";

interface TraceSection {
  label: string;
  value: string | null;
  note?: string | null;
}
interface Trace {
  summary: string;
  fact_sections: TraceSection[];
  review_sections: TraceSection[];
  evidence_count: number;
}

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const trace = ref<Trace | null>(null);
const observations = ref<ObservationView[]>([]);
const sources = ref<SourceView[]>([]);
const loading = ref(true);
const error = ref("");

function evidenceStateFor(o: ObservationView): "verified" | "pending" | "disputed" | "historical" {
  if (o.dispute_status === "DISPUTED") return "disputed";
  if (o.dispute_status && o.dispute_status !== "NONE") return "pending";
  return "verified";
}

/** Render "2026-09-20 10:30" for a timestamp, "2026-09-20" for a bare date. */
function displayTime(iso: string): string {
  return iso.length >= 16 ? `${iso.slice(0, 10)} ${iso.slice(11, 16)}` : iso;
}

/** Observed = most recent observation's occurred_at. */
const observedTime = computed(() => {
  if (!observations.value.length) return "";
  const latest = [...observations.value].sort((a, b) =>
    b.occurred_at.localeCompare(a.occurred_at),
  )[0];
  return displayTime(latest.occurred_at);
});

/** Submitted = created_at when the API provides it; ObservationView has none today. */
const submittedTime = computed(() => {
  const created = observations.value
    .map((o) => ("created_at" in o ? String(o.created_at) : ""))
    .find((v) => v);
  return created ? displayTime(created) : "";
});

/** Reviewed = first date-looking review value; fall back to 未记录 rather than guess. */
const reviewedTime = computed(() => {
  const values = (trace.value?.review_sections ?? []).map((s) => s.value ?? "");
  const dated = values.find((v) => /^\d{4}-\d{2}-\d{2}/.test(v));
  return dated ? displayTime(dated) : "";
});

/** Every review section as a metadata line (label：value). */
const reviewLines = computed(() =>
  (trace.value?.review_sections ?? []).map((s) => `${s.label}：${s.value ?? "未记录"}`),
);

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

async function load() {
  if (!placeId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const [t, obs, srcs] = await Promise.all([
      client.realityTrace(placeId.value),
      client.observations(placeId.value),
      client.allSources(),
    ]);
    trace.value = t;
    observations.value = obs;
    sources.value = srcs;
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

watch(placeId, () => void load(), { immediate: true });

/** O6 capture-state integrity: ready = records exist, else empty/loading/error. */
const uiState = computed<string>(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  if (!trace.value) return "unavailable";
  return observations.value.length > 0 ? "ready" : "empty";
});
const uiFixture = computed<string>(() =>
  uiState.value === "ready"
    ? "evidence-records-v1"
    : uiState.value === "empty"
      ? "evidence-empty-v1"
      : "evidence-other",
);
</script>

<template>
  <div
    class="evidence-workspace"
    data-testid="evidence-workspace"
    data-ui-page="evidence"
    :data-ui-state="uiState"
    :data-ui-fixture="uiFixture"
  >
    <QueryContextBar />
    <div class="evidence-workspace__body">
      <h1 class="visually-hidden">证据与来源</h1>
      <SkeletonList v-if="loading" :rows="4" />
      <StateMessage v-else-if="error" kind="ERROR" title="未能取得证据记录" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>
      <template v-else-if="trace">
        <header class="evidence-head">
          <!-- Place display name: never the raw UUID (contract EVIDENCE_NO_UUID_TEXT). -->
          <p class="muted evidence-head__place">场所信息暂不可用</p>
          <h2>证据与来源</h2>
          <EvidenceMeta
            v-if="trace.evidence_count != null"
            :evidence-count="trace.evidence_count"
          />
          <p
            class="evidence-disclaimer"
            data-testid="evidence-disclaimer"
            data-ui="evidence-disclaimer"
          >
            现场事实不代表正式准入规则。
          </p>
        </header>

        <EvidenceProvenance
          :observed-count="observations.length"
          :evidence-count="trace.evidence_count ?? 0"
          :reviewed-count="trace.review_sections.length"
        />

        <section class="evidence-section" aria-label="时间记录" data-ui="evidence-times">
          <h2 class="evidence-section__title">时间记录</h2>
          <div class="surface-row">
            <span>观察时间</span
            ><span class="muted" data-ui="observed-time">{{ observedTime || "未记录" }}</span>
          </div>
          <div class="surface-row">
            <span>提交时间</span
            ><span class="muted" data-ui="submitted-time">{{ submittedTime || "未记录" }}</span>
          </div>
          <div class="surface-row">
            <span>核验时间</span
            ><span class="muted" data-ui="reviewed-time">{{ reviewedTime || "未记录" }}</span>
          </div>
          <div v-for="(line, i) in reviewLines" :key="i" class="surface-row">
            <span>核验记录</span><span class="muted">{{ line }}</span>
          </div>
        </section>

        <section class="evidence-section" data-testid="evidence-items" aria-label="证据条目">
          <h2 class="evidence-section__title">现场证据条目</h2>
          <div v-for="o in observations" :key="o.id" class="surface-row evidence-item">
            <div class="evidence-item__main">
              <EvidenceStatus :state="evidenceStateFor(o)" />
              <time class="muted">{{ displayTime(o.occurred_at) }}</time>
            </div>
            <p class="evidence-item__text">
              {{ animalScopeLabel(o.animal_scope) }} · {{ ruleActionLabel(o.observed_action) }}
              <span v-if="o.staff_action" class="muted"
                >（工作人员：{{ staffActionLabel(o.staff_action) }}）</span
              >
            </p>
            <p v-if="o.note" class="muted evidence-item__note">{{ o.note }}</p>
          </div>
          <StateMessage
            v-if="!observations.length"
            kind="EMPTY"
            :title="EMPTY_STATE_COPY.EVIDENCE.title"
            :description="EMPTY_STATE_COPY.EVIDENCE.description"
            data-testid="evidence-empty"
          >
            <template #action>
              <button class="primary" @click="load">刷新</button>
            </template>
          </StateMessage>
          <p class="muted evidence-item__images" data-testid="evidence-images-note">
            暂无原始证据图片（证据仍可来自文字记录）
          </p>
        </section>

        <section class="evidence-section" data-testid="evidence-sources" aria-label="来源列表">
          <h2 class="evidence-section__title">来源</h2>
          <div v-for="s in sources" :key="s.id" class="surface-row">
            <span class="evidence-source__issuer">{{ s.issuer }}</span>
            <span class="muted evidence-source__meta"
              >{{ LABELS[s.source_type] ?? "其他来源" }} ·
              {{ LABELS[s.issuer_verification] ?? "核验状态未知" }} · 收集于
              {{ s.collected_at.slice(0, 10) }}</span
            >
          </div>
          <p v-if="!sources.length" class="muted">暂无来源记录。</p>
        </section>
      </template>
      <StateMessage
        v-else
        kind="EMPTY"
        :title="EMPTY_STATE_COPY.EVIDENCE.title"
        :description="EMPTY_STATE_COPY.EVIDENCE.description"
      />
    </div>
  </div>
</template>

<style scoped>
.evidence-workspace {
  min-height: 100%;
}
.evidence-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding: var(--pa-space-4);
  max-width: var(--pa-layout-content-820);
  margin: 0 auto;
}
.evidence-head {
  padding-bottom: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}
.evidence-head__place {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-sm);
}
.evidence-head h2 {
  margin: 0 0 var(--pa-space-2);
}
.evidence-disclaimer {
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}
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
.evidence-item__text,
.evidence-item__note {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}
.evidence-item__note,
.evidence-item__images {
  font-size: var(--pa-font-size-sm);
}
.evidence-item__images {
  margin: var(--pa-space-2) 0 0;
}
.evidence-source__issuer {
  color: var(--pa-color-text-primary);
}
.evidence-source__meta {
  text-align: right;
}
</style>
