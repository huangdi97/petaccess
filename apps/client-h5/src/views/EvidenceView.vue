<script setup lang="ts">
/**
 * EvidenceView — Evidence Record + Provenance.
 *
 * The page now reads the same v0.9 published Reality events and
 * CoexistenceSnapshot as Home/Search/Map/Place. Legacy ObservationClaim rows
 * are not used as a second consumer truth source.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  client,
  placeTypeLabel,
  session,
  type CoexistenceSnapshot,
  type PlaceDetail,
  type PublicEvidenceMediaView,
  type RealityEventView,
  type Zone,
} from "@petaccess/client-core";
import { zoneConsumerLine } from "../consumer/labels";
import {
  displayRealityEventTime,
  displayRealityTime,
  evidenceMaterialLabel,
  realityEventDetail,
  realityEventEvidenceState,
  realityEventHeadline,
  realityEventProvenance,
  realityProvenanceCounts,
  realityEventTimeBasis,
} from "../consumer/realityEvent";
import { createEpoch, currentQueryContext, snapshotFor } from "../consumer/repository";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import EvidenceStatus from "../components/domain/EvidenceStatus.vue";
import EvidenceProvenance from "../components/domain/EvidenceProvenance.vue";
import EvidenceGovernanceSummary from "../components/domain/EvidenceGovernanceSummary.vue";
import EvidenceDisputeAction from "../components/domain/EvidenceDisputeAction.vue";
import PaIcon from "../components/ui/PaIcon.vue";
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
const snapshot = ref<CoexistenceSnapshot | null>(null);
const place = ref<PlaceDetail | null>(null);
const zones = ref<Zone[]>([]);
const events = ref<RealityEventView[]>([]);
const publicMediaByBundle = ref<Map<string, PublicEvidenceMediaView>>(new Map());
const loading = ref(true);
const error = ref("");
const loadEpoch = createEpoch();

function sourceTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    statute_or_regulation: "法规",
    government_service: "政府服务",
    official_operator_policy: "管理方发布",
    onsite_signage: "现场标识",
    certified_verifier: "认证核验方",
    ordinary_user: "普通用户",
    external_web_reference: "外部网页",
    imported_dataset: "导入数据",
  };
  return labels[value] ?? "其他来源";
}

const latestEvent = computed(
  () => [...events.value].sort((a, b) => b.event_at.localeCompare(a.event_at))[0] ?? null,
);

const recordIdentity = computed(() => {
  const latest = latestEvent.value;
  if (!latest) return null;
  const zone = latest.zone_id ? zones.value.find((item) => item.id === latest.zone_id) : null;
  return {
    placeName: place.value?.canonical_name ?? null,
    zoneName: zone ? zoneConsumerLine(zone) : "场所范围",
    eventTime: displayRealityEventTime(latest),
    timeBasis: realityEventTimeBasis(latest),
  };
});

const observedTime = computed(() => {
  const latestObserved = events.value
    .filter(
      (event) =>
        event.time_basis === "observed" && event.time_evidence_state !== "publication_time_only",
    )
    .sort((a, b) => b.event_at.localeCompare(a.event_at))[0];
  return latestObserved ? displayRealityEventTime(latestObserved) : "";
});

const submittedTime = computed(() => {
  const latest = events.value
    .map((event) => event.submitted_at)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1);
  return latest ? displayRealityTime(latest) : "";
});

const reviewedTime = computed(() => {
  const latest = events.value
    .map((event) => event.last_verified_at)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1);
  return latest ? displayRealityTime(latest) : "";
});

const reviewLines = computed(() =>
  (trace.value?.review_sections ?? []).map(
    (section) => `${section.label}：${section.value ?? "未记录"}`,
  ),
);

const ruleEvidence = computed(() => snapshot.value?.evidence_summary.rule_evidence ?? []);
const ruleEvidenceCount = computed(() => ruleEvidence.value.length);
const realityEvidenceCount = computed(
  () => snapshot.value?.evidence_summary.reality_evidence_count ?? events.value.length,
);
const provenanceCounts = computed(() => realityProvenanceCounts(events.value));

const realitySourceRows = computed(() => {
  // RealityEventOut already carries the public provenance projection needed
  // by the consumer. Never enumerate the global /sources collection and then
  // infer that its first page is complete for this place.
  const seen = new Set<string>();
  return events.value.flatMap((event) => {
    const key = event.source_id ?? event.evidence_bundle_id;
    if (!key || seen.has(key)) return [];
    seen.add(key);
    return [
      {
        key,
        material: evidenceMaterialLabel(event),
        provenance: realityEventProvenance(event) || "已有来源记录",
        reviewedAt: event.last_verified_at ? displayRealityTime(event.last_verified_at) : "",
      },
    ];
  });
});

const sourceSummary = computed(() => {
  const sourceCount = provenanceCounts.value.sourceCount;
  if (sourceCount) return `${sourceCount} 个可追溯来源`;
  const bundles = new Set(
    events.value.map((event) => event.evidence_bundle_id).filter((id): id is string => Boolean(id)),
  );
  return bundles.size ? `${bundles.size} 组可追溯现场材料` : "来源待补充";
});

function publicMediaFor(event: RealityEventView): PublicEvidenceMediaView | null {
  if (!event.evidence_bundle_id) return null;
  return publicMediaByBundle.value.get(event.evidence_bundle_id) ?? null;
}

async function loadPublicMedia(eventRows: RealityEventView[], epoch: number) {
  const bundleIds = [
    ...new Set(
      eventRows.map((event) => event.evidence_bundle_id).filter((id): id is string => Boolean(id)),
    ),
  ].slice(0, 8);
  const rows = await Promise.all(
    bundleIds.map(async (bundleId) => {
      try {
        return [bundleId, await client.publicEvidenceMedia(bundleId)] as const;
      } catch {
        // Public-media qualification is intentionally fail-closed. A 404 means
        // "do not display" rather than a page-level Evidence failure.
        return null;
      }
    }),
  );
  if (!loadEpoch.isCurrent(epoch)) return;
  publicMediaByBundle.value = new Map(rows.filter((row) => row !== null));
}

async function load() {
  const id = placeId.value;
  if (!id) return;
  const epoch = loadEpoch.begin();
  loading.value = true;
  error.value = "";
  try {
    // A direct Evidence deep link must restore the persisted query subject
    // before taking the rule snapshot; otherwise the same place can briefly
    // resolve as the default ordinary dog instead of the user's active pet.
    await session.restore();
    if (!loadEpoch.isCurrent(epoch) || placeId.value !== id) return;
    const [traceRow, eventRows, placeRow, zoneRows, snapshotRow] = await Promise.all([
      client.realityTrace(id),
      client.realityEvents(id),
      client.place(id),
      client.zones(id),
      snapshotFor(id).then((result) => result.snapshot),
    ]);
    if (!loadEpoch.isCurrent(epoch) || placeId.value !== id) return;
    trace.value = traceRow;
    events.value = eventRows;
    publicMediaByBundle.value = new Map();
    place.value = placeRow;
    zones.value = zoneRows;
    snapshot.value = snapshotRow;
    void loadPublicMedia(eventRows, epoch);
  } catch (e) {
    if (loadEpoch.isCurrent(epoch)) error.value = presentDescription(e);
  } finally {
    if (loadEpoch.isCurrent(epoch)) loading.value = false;
  }
}

watch(placeId, () => void load(), { immediate: true });

watch(currentQueryContext, () => {
  if (!placeId.value || loading.value) return;
  void load();
});

const uiState = computed<string>(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  if (!snapshot.value) return "unavailable";
  return events.value.length || ruleEvidenceCount.value ? "ready" : "empty";
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

      <template v-else-if="snapshot">
        <header class="evidence-head" data-testid="evidence-head">
          <div class="evidence-head__identity">
            <span class="evidence-head__icon" aria-hidden="true">
              <PaIcon name="shield-check" size="md" />
            </span>
            <div class="evidence-head__identity-copy">
              <h2 class="evidence-head__record" data-testid="evidence-record-place">
                {{ place?.canonical_name ?? "场所名称待补充" }}
              </h2>
              <p class="muted evidence-head__meta" data-testid="evidence-record-zone">
                <template v-if="recordIdentity">
                  {{ recordIdentity.zoneName }} · {{ recordIdentity.eventTime }} ·
                  {{ recordIdentity.timeBasis }}
                </template>
                <template v-else>
                  {{ placeTypeLabel(place?.place_type ?? "") }} · 暂无经核验现场事实
                </template>
              </p>
            </div>
          </div>
          <p class="muted evidence-head__count" data-testid="evidence-record-count">
            {{ realityEvidenceCount }} 条现场依据 · {{ ruleEvidenceCount }} 条规则依据 ·
            {{ sourceSummary }}
          </p>
          <p
            class="evidence-disclaimer"
            data-testid="evidence-disclaimer"
            data-ui="evidence-disclaimer"
          >
            现场事实不代表正式准入规则；工作人员处理不等于运营方政策；设施存在不等于允许进入。
          </p>
        </header>

        <EvidenceProvenance
          :raw-material-count="provenanceCounts.rawMaterialCount"
          :place-matched-count="provenanceCounts.placeMatchedCount"
          :time-confirmed-count="provenanceCounts.timeConfirmedCount"
          :source-count="provenanceCounts.sourceCount"
          :reviewed-count="provenanceCounts.reviewedCount"
        />

        <EvidenceGovernanceSummary
          :events="events"
          :rule-first-party-pending="snapshot.evidence_summary.rule_first_party_pending"
        />

        <section class="evidence-section" aria-label="时间记录" data-ui="evidence-times">
          <h2 class="evidence-section__title">时间记录</h2>
          <div class="evidence-time-grid">
            <div class="evidence-timefact">
              <span class="evidence-timefact__label">观察时间</span>
              <strong class="evidence-timefact__value" data-ui="observed-time">
                {{ observedTime || "未记录" }}
              </strong>
            </div>
            <div class="evidence-timefact">
              <span class="evidence-timefact__label">提交时间</span>
              <strong class="evidence-timefact__value" data-ui="submitted-time">
                {{ submittedTime || "未记录" }}
              </strong>
            </div>
            <div class="evidence-timefact">
              <span class="evidence-timefact__label">核验时间</span>
              <strong class="evidence-timefact__value" data-ui="reviewed-time">
                {{ reviewedTime || "未记录" }}
              </strong>
            </div>
          </div>
          <div v-for="(line, index) in reviewLines" :key="index" class="evidence-review-row">
            <span>核验记录</span><span class="muted">{{ line }}</span>
          </div>
        </section>

        <section class="evidence-section" data-testid="evidence-items" aria-label="现场证据事实">
          <h2 class="evidence-section__title">现场证据事实</h2>
          <div v-for="event in events" :key="event.id" class="surface-row evidence-item">
            <div class="evidence-item__main">
              <EvidenceStatus :state="realityEventEvidenceState(event)" />
              <time class="muted">{{ displayRealityEventTime(event) }}</time>
            </div>
            <p class="evidence-item__text">{{ realityEventHeadline(event) }}</p>
            <p v-if="realityEventDetail(event)" class="muted evidence-item__note">
              {{ realityEventDetail(event) }}
            </p>
            <figure
              v-if="publicMediaFor(event)"
              class="evidence-item__media"
              data-testid="public-evidence-media"
            >
              <img
                :src="publicMediaFor(event)!.url"
                alt="经审核允许公开展示的现场证据图片"
                loading="lazy"
                decoding="async"
                referrerpolicy="no-referrer"
              />
              <figcaption>经审核允许公开展示的现场证据图片 · 临时访问链接</figcaption>
            </figure>
            <p v-if="realityEventProvenance(event)" class="muted evidence-item__provenance">
              {{ realityEventProvenance(event) }}
            </p>
            <p
              v-if="event.event_type === 'staff_response' && event.staff_policy_statement_verbatim"
              class="evidence-item__quote"
            >
              <span class="evidence-item__quote-label">本次事件中记录的原话</span>
              “{{ event.staff_policy_statement_verbatim }}”
              <span class="muted">· 不代表运营方正式政策</span>
            </p>
            <p class="muted evidence-item__basis">{{ realityEventTimeBasis(event) }}</p>
            <EvidenceDisputeAction :event="event" :signed-in="session.signedIn" />
          </div>
          <div v-if="!events.length" class="evidence-empty-inline" data-testid="evidence-empty">
            <p>暂无经核验现场事实</p>
            <p class="muted">这并不代表现场没有动物。</p>
          </div>
        </section>

        <section class="evidence-section" data-testid="rule-evidence-items" aria-label="规则依据">
          <h2 class="evidence-section__title">规则依据</h2>
          <div
            v-for="(item, index) in ruleEvidence"
            :key="item.source_id + '-' + index"
            class="surface-row"
          >
            <span>{{ item.issuer || "来源待补充" }}</span>
            <span class="muted evidence-source__meta">
              {{ sourceTypeLabel(item.source_type || "") }}
            </span>
          </div>
          <p v-if="!ruleEvidence.length" class="muted">暂无可靠规则依据。</p>
        </section>

        <section class="evidence-section" data-testid="evidence-sources" aria-label="现场来源">
          <h2 class="evidence-section__title">现场来源</h2>
          <div v-for="source in realitySourceRows" :key="source.key" class="surface-row">
            <span class="evidence-source__issuer">{{ source.material }}</span>
            <span class="muted evidence-source__meta">
              {{ source.provenance }}
              <template v-if="source.reviewedAt"> · 最近核验 {{ source.reviewedAt }}</template>
            </span>
          </div>
          <p v-if="!realitySourceRows.length" class="muted">
            原始材料可能受隐私或许可限制；上方现场事实仍显示可公开的来源类型、时间依据与核验状态。
          </p>
        </section>
      </template>

      <div v-else class="evidence-empty-inline" data-testid="evidence-none">
        <p>暂无证据记录</p>
        <p class="muted">未收录不代表允许或禁止，也不代表现场没有动物。</p>
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

.evidence-head__identity {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-3);
}

.evidence-head__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-evidence-verified-bg);
  color: var(--pa-color-evidence-verified);
}

.evidence-head__identity-copy {
  min-width: 0;
}

.evidence-head__record {
  margin: 0;
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
  line-height: var(--pa-line-height-20);
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

.evidence-review-row,
.surface-row {
  display: flex;
  justify-content: space-between;
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.evidence-review-row {
  padding: var(--pa-space-2) 0;
  font-size: var(--pa-font-size-sm);
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

.evidence-item__text,
.evidence-item__note,
.evidence-item__provenance,
.evidence-item__basis {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}

.evidence-item__provenance,
.evidence-item__basis {
  font-size: var(--pa-font-size-sm);
}

.evidence-item__media {
  margin: var(--pa-space-3) 0 var(--pa-space-1);
  max-width: 560px;
}

.evidence-item__media img {
  display: block;
  width: 100%;
  max-height: 360px;
  object-fit: contain;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface-muted);
}

.evidence-item__media figcaption {
  margin-top: var(--pa-space-1);
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-xs);
  line-height: var(--pa-line-height-20);
}

.evidence-item__quote {
  margin: var(--pa-space-1) 0 0;
  padding-left: var(--pa-space-3);
  border-left: 2px solid var(--pa-color-border);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-primary);
}

.evidence-item__quote-label {
  display: block;
  margin-bottom: 2px;
  color: var(--pa-color-text-muted);
}

.evidence-source__issuer {
  color: var(--pa-color-text-primary);
}

.evidence-source__meta {
  text-align: right;
  font-size: var(--pa-font-size-sm);
}

.evidence-empty-inline {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin: var(--pa-space-2) 0;
}

.evidence-empty-inline p {
  margin: 0;
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
    max-width: 62%;
  }
}
</style>
