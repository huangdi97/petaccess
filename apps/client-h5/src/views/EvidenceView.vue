<script setup lang="ts">
/**
 * EvidenceView — Evidence Record + Provenance (v0.2.4 §37–40).
 *
 * Record identity is resolved, never "场所信息暂不可用": the header names the
 * place, zone and observed time from the actual API responses. The provenance
 * rail (5 steps) stays as the successful v0.2.3 surface and gains explicit
 * active/complete/pending shapes with one-line explanation per step. Evidence
 * dimensions are never conflated: the record header says 现场记录 count while
 * a separate line states 正式规则依据 when the rule-evidence dimension is truly
 * zero (§40).
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  client,
  placeTypeLabel,
  type ObservationView,
  type PlaceDetail,
  type SourceView,
  type Zone,
} from "@petaccess/client-core";
import {
  animalScopeLabel,
  ruleActionLabel,
  staffActionLabel,
  zoneConsumerLine,
} from "../consumer/labels";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
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
const place = ref<PlaceDetail | null>(null);
const zones = ref<Zone[]>([]);
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

/** §38 record identity — zone of the most recent observation, resolved by name. */
const recordZone = computed(() => {
  const latest = [...observations.value].sort((a, b) =>
    b.occurred_at.localeCompare(a.occurred_at),
  )[0];
  if (!latest?.zone_id) return null;
  return zones.value.find((z) => z.id === latest.zone_id) ?? null;
});

const recordIdentity = computed(() => {
  if (!observations.value.length) return null;
  const latest = [...observations.value].sort((a, b) =>
    b.occurred_at.localeCompare(a.occurred_at),
  )[0];
  const zone = recordZone.value ? zoneConsumerLine(recordZone.value) : null;
  return {
    placeName: place.value?.canonical_name ?? null,
    zoneName: zone,
    observedTime: displayTime(latest.occurred_at),
  };
});

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

/** §40：记录存在时标题显示「N 条现场记录」；正式规则依据单独计数，不混维。 */
const factCountLabel = computed(() => {
  const n = observations.value.length;
  return n === 0 ? "暂无现场记录" : `${n} 条现场记录`;
});
const ruleEvidenceCount = computed(() => trace.value?.evidence_count ?? 0);
const pendingSources = computed(
  () => sources.value.filter((s) => s.issuer_verification === "unverified").length,
);
const sourceSummary = computed(() => {
  const parts: string[] = [];
  if (sources.value.length === 0) parts.push("来源待补充");
  else parts.push(`${sources.value.length} 个来源`);
  if (pendingSources.value > 0) parts.push(`${pendingSources.value} 个待核验`);
  return parts.join(" · ");
});

async function load() {
  if (!placeId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const [t, obs, srcs, plc, zs] = await Promise.all([
      client.realityTrace(placeId.value),
      client.observations(placeId.value),
      client.allSources(),
      client.place(placeId.value).catch(() => null),
      client.zones(placeId.value).catch(() => [] as Zone[]),
    ]);
    trace.value = t;
    observations.value = obs;
    sources.value = srcs;
    place.value = plc;
    zones.value = zs;
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
        <!-- §38 header：record identity 必须可读（ready fixture 有 place/zone/time）。 -->
        <header class="evidence-head" data-testid="evidence-head">
          <template v-if="recordIdentity">
            <h2 class="evidence-head__record" data-testid="evidence-record-place">
              {{ recordIdentity.placeName ?? "场所名称待补充" }}
            </h2>
            <p class="muted evidence-head__meta" data-testid="evidence-record-zone">
              {{ recordIdentity.zoneName ?? placeTypeLabel(place?.place_type ?? "") }} ·
              {{ recordIdentity.observedTime }}
            </p>
            <p class="muted evidence-head__count" data-testid="evidence-record-count">
              {{ factCountLabel }} · {{ sourceSummary }}
            </p>
          </template>
          <template v-else>
            <h2 class="evidence-head__record">暂无现场记录</h2>
            <p class="muted evidence-head__meta">该场所尚未收录现场事实。未收录不代表没有动物。</p>
          </template>
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
          :rule-evidence-count="ruleEvidenceCount"
          :reviewed-count="trace.review_sections.length"
        />

        <section class="evidence-section" aria-label="时间记录" data-ui="evidence-times">
          <h2 class="evidence-section__title">时间记录</h2>
          <div class="evidence-time-grid">
            <div class="evidence-timefact">
              <span class="evidence-timefact__label">观察时间</span>
              <strong class="evidence-timefact__value" data-ui="observed-time">{{
                observedTime || "未记录"
              }}</strong>
            </div>
            <div class="evidence-timefact">
              <span class="evidence-timefact__label">提交时间</span>
              <strong class="evidence-timefact__value" data-ui="submitted-time">{{
                submittedTime || "未记录"
              }}</strong>
            </div>
            <div class="evidence-timefact">
              <span class="evidence-timefact__label">核验时间</span>
              <strong class="evidence-timefact__value" data-ui="reviewed-time">{{
                reviewedTime || "未记录"
              }}</strong>
            </div>
          </div>
          <div v-for="(line, i) in reviewLines" :key="i" class="evidence-review-row">
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
          <div
            v-if="!observations.length"
            class="evidence-empty-inline"
            data-testid="evidence-empty"
          >
            <p>暂无现场记录</p>
            <p class="muted">这并不代表现场没有动物。</p>
          </div>
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
          <!-- §40：正式规则依据维度单独说明，不与现场记录数量混淆。 -->
          <p class="muted evidence-rule-dimension" data-testid="evidence-rule-count">
            正式规则依据：{{ ruleEvidenceCount }}
          </p>
        </section>
      </template>
      <div v-else class="evidence-empty-inline" data-testid="evidence-none">
        <p>暂无现场记录</p>
        <p class="muted">这并不代表现场没有动物。</p>
      </div>
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
  padding: var(--pa-space-5) var(--pa-space-6) var(--pa-space-7);
  max-width: var(--pa-layout-content-820);
  margin: 0 auto;
}
.evidence-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.evidence-head__record {
  margin: 0;
  /* v0.2.7 §25/§28：record identity 是页面首要事实 —— 22/650，强化可读层级。 */
  font-size: var(--pa-font-size-24);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-32);
  color: var(--pa-color-text-primary);
}
.evidence-head__meta {
  margin: var(--pa-space-1) 0 0;
  line-height: var(--pa-line-height-23);
}
.evidence-head__count {
  margin: var(--pa-space-2) 0 0;
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-secondary);
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
  margin: var(--pa-space-4) 0 var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
  color: var(--pa-color-text-primary);
}

.evidence-time-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--pa-space-5);
  padding: var(--pa-space-3) 0 var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.evidence-timefact {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  min-width: 0;
}

.evidence-timefact__label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.evidence-timefact__value {
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
  overflow-wrap: anywhere;
}

.evidence-review-row {
  display: flex;
  justify-content: space-between;
  gap: var(--pa-space-4);
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-sm);
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
.evidence-rule-dimension {
  margin: var(--pa-space-2) 0 0;
  font-size: var(--pa-font-size-sm);
}
.evidence-empty-inline {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin: var(--pa-space-2) 0;
}

@media (max-width: 767px) {
  .evidence-workspace__body {
    padding: var(--pa-space-4);
  }

  .evidence-head__record {
    font-size: var(--pa-font-size-22);
    line-height: var(--pa-line-height-26);
  }

  .evidence-time-grid {
    grid-template-columns: 1fr;
    gap: var(--pa-space-3);
  }

  .evidence-review-row,
  .surface-row {
    align-items: flex-start;
  }

  .evidence-source__meta {
    max-width: 60%;
  }
}
</style>
