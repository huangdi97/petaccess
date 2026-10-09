<script setup lang="ts">
/**
 * Place Detail — Dossier with Views（v0.2.4 §15–28）.
 *
 * Place 不再是一张无限长页面：Dossier 顶部是本地 section 导航
 * （概览 / 空间 / 规则 / 现场 / 证据，text tab + underline；mobile 横滑），
 * 每个 section 只渲染自己的内容，支持 ?view= deep link / back-forward / refresh。
 * Overview 最多五块（Identity / Current Decision / Recent Reality / Space
 * Summary / Evidence·Source Summary），其余进各自 view；规则/证据 view 使用
 * progressive disclosure（历史版本折叠）。Unknown 态只渲染有数据的部分。
 *
 * Data：public place endpoints + CoexistenceSnapshot SSOT（consumer repository）。
 * 状态按 O6 从真实加载数据导出，从不冒充 ready。
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import {
  client,
  conditionLabel,
  placeTypeLabel,
  session,
  type AccessAnswer,
  type CoexistenceSnapshot,
  type RealityEventView,
  type PlaceDetail,
  type PlaceSummary,
  type PlaceExtras,
  type PublicEvidenceMediaView,
  type RuleView,
  type SourceView,
  type Zone,
} from "@petaccess/client-core";
import DecisionInspector from "../components/domain/DecisionInspector.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import PlaceTypeGlyph from "../components/domain/PlaceTypeGlyph.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import PlaceSectionNav, { type PlaceViewKey } from "../components/place/PlaceSectionNav.vue";
import PlaceOverviewPane from "../components/place/PlaceOverviewPane.vue";
import PlaceSpacePane from "../components/place/PlaceSpacePane.vue";
import PlaceRulesPane from "../components/place/PlaceRulesPane.vue";
import PlaceRealityPane from "../components/place/PlaceRealityPane.vue";
import PlaceEvidencePane from "../components/place/PlaceEvidencePane.vue";
import { sourceLabel } from "../consumer/labels";
import { queryAnimalLabel } from "../consumer/queryContext";
import { answerStatusKey } from "../answer";
import { presentDescription } from "../errors";
import { useBreakpoint } from "../composables/useBreakpoint";
import { useRealityConfirmation } from "../composables/useRealityConfirmation";
import { createEpoch, currentQueryContext, snapshotFor } from "../consumer/repository";
import { firstApprovedSceneMedia } from "../consumer/publicSceneMedia";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const realityConfirmation = useRealityConfirmation(() => placeId.value);

/** §15：?view= overview|space|rules|reality|evidence（deep link / refresh 安全）。 */
const VALID_VIEWS: readonly PlaceViewKey[] = ["overview", "space", "rules", "reality", "evidence"];
const view = computed<PlaceViewKey>(() => {
  const v = route.query.view;
  return typeof v === "string" && (VALID_VIEWS as readonly string[]).includes(v)
    ? (v as PlaceViewKey)
    : "overview";
});

const { desktop: isDesktop } = useBreakpoint();
const speciesLabel = computed(() => queryAnimalLabel());

const place = ref<PlaceDetail | null>(null);
const placeSummary = ref<PlaceSummary | null>(null);
const zones = ref<Zone[]>([]);
const rules = ref<RuleView[]>([]);
const realityEvents = ref<RealityEventView[]>([]);
const placeSceneMedia = ref<PublicEvidenceMediaView | null>(null);
const sources = ref<SourceView[]>([]);
const extras = ref<PlaceExtras | null>(null);

const answer = ref<AccessAnswer | null>(null);
const error = ref("");
const loading = ref(true);
const partial = ref<string[]>([]);
const watchingRule = ref(false);
const watchingReality = ref(false);
const watchMsg = ref("");
const watchBusy = ref<"rule" | "reality" | null>(null);
const coexistence = ref<CoexistenceSnapshot | null>(null);
const coexistenceLoaded = ref(false);
const evaluationEpoch = createEpoch();

const currentRules = computed(() => rules.value.filter((r) => r.status === "current"));
const historyRules = computed(() => rules.value.filter((r) => r.status !== "current"));
const conditions = computed(() => {
  const seen = new Set<string>();
  for (const r of currentRules.value) {
    for (const c of (r as unknown as { conditions?: { condition_type?: string }[] }).conditions ??
      []) {
      seen.add(conditionLabel(c.condition_type ?? ""));
    }
  }
  return [...seen];
});
const sourceMap = computed(() => {
  const m = new Map<string, SourceView>();
  for (const s of sources.value) m.set(s.id, s);
  return m;
});
const latestVerifiedAt = computed(() => {
  const latest = currentRules.value
    .map((r) => r.last_verified_at)
    .filter((v): v is string => Boolean(v))
    .sort()
    .at(-1);
  return latest ? latest.slice(0, 10) : null;
});
const primarySourceLabel = computed(() => {
  const first = currentRules.value[0];
  return first ? sourceLabel(sourceMap.value.get(first.source_id)?.issuer ?? null, true) : null;
});

const presenceEventCount = computed(
  () => realityEvents.value.filter((event) => event.event_type === "observed_presence").length,
);

async function evaluate() {
  const epoch = evaluationEpoch.begin();
  coexistenceLoaded.value = false;
  try {
    const { snapshot } = await snapshotFor(placeId.value);
    if (!evaluationEpoch.isCurrent(epoch)) return;
    coexistence.value = snapshot;
    answer.value = snapshot.rule_answer;
  } catch (error) {
    if (!evaluationEpoch.isCurrent(epoch)) return;
    coexistence.value = null;
    answer.value = null;
    throw error;
  } finally {
    if (evaluationEpoch.isCurrent(epoch)) coexistenceLoaded.value = true;
  }
}

// Every field that actually changes CoexistenceSnapshot must re-evaluate:
// mode, active pet/species/service role and ephemeral declared service-dog role.
watch(currentQueryContext, () => {
  if (!placeId.value || loading.value) return;
  void evaluate().catch(() => {
    if (!partial.value.includes("当前答案")) partial.value.push("当前答案");
  });
});

const loadEpoch = createEpoch();

async function loadPlaceSceneMedia(
  eventRows: RealityEventView[],
  epoch: number,
  expectedPlaceId: string,
) {
  const media = await firstApprovedSceneMedia(eventRows);
  if (!loadEpoch.isCurrent(epoch) || placeId.value !== expectedPlaceId) return;
  placeSceneMedia.value = media;
}

async function load() {
  const epoch = loadEpoch.begin();
  const id = placeId.value;
  const isCurrent = () => loadEpoch.isCurrent(epoch) && placeId.value === id;
  loading.value = true;
  error.value = "";
  partial.value = [];
  placeSceneMedia.value = null;
  const degrade = (label: string) => {
    if (isCurrent() && !partial.value.includes(label)) partial.value.push(label);
  };
  await session.restore();
  if (!isCurrent()) return;

  try {
    const result = await client.place(id);
    if (!isCurrent()) return;
    place.value = result;
  } catch (e) {
    if (!isCurrent()) return;
    error.value = presentDescription(e);
    loading.value = false;
    return;
  }

  try {
    const summary = await client.placeSummary(id);
    if (!isCurrent()) return;
    placeSummary.value = summary;
  } catch {
    if (!isCurrent()) return;
    placeSummary.value = null;
    degrade("地图位置");
  }

  if (session.signedIn) {
    try {
      const mine = await client.myWatches();
      if (!isCurrent()) return;
      watchingRule.value = mine.some(
        (item) =>
          item.watch_domain === "rule" && item.target_type === "place" && item.target_id === id,
      );
      watchingReality.value = mine.some(
        (item) =>
          item.watch_domain === "reality" && item.target_type === "place" && item.target_id === id,
      );
    } catch {
      if (!isCurrent()) return;
      degrade("关注状态");
    }
  } else {
    watchingRule.value = false;
    watchingReality.value = false;
  }
  try {
    const rows = await client.zones(id);
    if (!isCurrent()) return;
    zones.value = rows;
  } catch {
    if (!isCurrent()) return;
    degrade("分区域");
  }
  try {
    const rows = await client.rules(id);
    if (!isCurrent()) return;
    rules.value = rows;
  } catch {
    if (!isCurrent()) return;
    degrade("规则");
  }
  try {
    const rows = await client.realityEvents(id);
    if (!isCurrent()) return;
    realityEvents.value = rows;
    void loadPlaceSceneMedia(rows, epoch, id);
  } catch {
    if (!isCurrent()) return;
    degrade("现场记录");
  }
  try {
    const relevantSourceIds = new Set([
      ...rules.value.map((rule) => rule.source_id),
      ...realityEvents.value
        .map((event) => event.source_id)
        .filter((sourceId): sourceId is string => Boolean(sourceId)),
    ]);
    const rows = await client.allSources();
    if (!isCurrent()) return;
    sources.value = rows.filter((source) => relevantSourceIds.has(source.id));
  } catch {
    if (!isCurrent()) return;
    degrade("来源");
  }
  try {
    const result = await client.placeExtras(id);
    if (!isCurrent()) return;
    extras.value = result;
  } catch {
    if (!isCurrent()) return;
    degrade("空间信息");
  }
  try {
    await evaluate();
    if (!isCurrent()) return;
  } catch {
    if (!isCurrent()) return;
    degrade("当前答案");
  }
  if (isCurrent()) loading.value = false;
}

watch(
  placeId,
  () => {
    // Invalidate in-flight Place and Coexistence requests before clearing the
    // previous dossier. A slow response must never write into a new place.
    loadEpoch.begin();
    evaluationEpoch.begin();
    place.value = null;
    placeSummary.value = null;
    zones.value = [];
    rules.value = [];
    realityEvents.value = [];
    sources.value = [];
    extras.value = null;
    answer.value = null;
    error.value = "";
    partial.value = [];
    watchMsg.value = "";
    watchBusy.value = null;
    realityConfirmation.message.value = "";
    realityConfirmation.busyEventId.value = null;
    watchingRule.value = false;
    watchingReality.value = false;
    coexistence.value = null;
    coexistenceLoaded.value = false;
    if (placeId.value) void load();
  },
  { immediate: true },
);

async function toggleWatchDomain(domain: "rule" | "reality") {
  if (watchBusy.value) return;
  const targetPlaceId = placeId.value;
  if (!targetPlaceId) return;
  const current = () => placeId.value === targetPlaceId;
  watchMsg.value = "";
  watchBusy.value = domain;
  try {
    const mine = await client.myWatches();
    // The route may switch places while the watch list is loading.
    // Never submit the pending action for a different destination.
    if (!current()) return;
    const existing = mine.find(
      (watch) =>
        watch.watch_domain === domain &&
        watch.target_type === "place" &&
        watch.target_id === targetPlaceId,
    );
    if (existing) {
      await client.unwatch(existing.id);
      if (!current()) return;
      if (domain === "rule") watchingRule.value = false;
      else watchingReality.value = false;
    } else {
      await client.watch("place", targetPlaceId, domain);
      if (!current()) return;
      if (domain === "rule") watchingRule.value = true;
      else watchingReality.value = true;
    }
  } catch (e) {
    if (current()) watchMsg.value = `关注状态未能更新：${presentDescription(e)}`;
  } finally {
    if (current()) watchBusy.value = null;
  }
}

/** §16：Overview 全页长度门由 oracle 测量；这里只渲染 5 块 + CTA links。 */
const overviewFiveBlocks = computed(() => Boolean(place.value));

const placeState = computed<string>(() => {
  if (error.value || !place.value) return "unavailable";
  if (loading.value) return "loading";
  if (!answer.value) return "unknown";
  return answerStatusKey(answer.value) === "UNKNOWN" ? "unknown" : "ready";
});
const placeFixture = computed<string>(() => {
  if (placeState.value === "ready") return "place-ready-v1";
  if (placeState.value === "unknown") return "place-unknown-v1";
  return "place-state-v1";
});
</script>

<template>
  <div
    class="place-workspace"
    data-testid="place-workspace"
    data-ui="place-shell"
    data-ui-page="place"
    :data-ui-state="placeState"
    :data-ui-fixture="placeFixture"
    :data-ui-entity-id="placeId"
  >
    <QueryContextBar />
    <div class="place-workspace__body" :class="{ 'place-workspace__body--split': isDesktop }">
      <!-- main dossier -->
      <main class="place-dossier" data-ui="place-dossier" aria-label="场所档案">
        <SkeletonList v-if="loading" :rows="4" />
        <StateMessage v-else-if="error" kind="ERROR" title="未能取得场所信息" :description="error">
          <template #action>
            <button class="primary" @click="load">重试</button>
          </template>
        </StateMessage>
        <StateMessage
          v-else-if="!place"
          kind="EMPTY"
          description="该场所尚未收录，或已被移除。未收录不代表该场所没有规则。"
        />
        <template v-else>
          <StateMessage
            v-if="partial.length"
            kind="PARTIAL"
            :description="`部分板块未能加载：${partial.join('、')}。已加载内容仍可查看。`"
          />

          <!-- 1. Identity（§16 Overview 第一块） -->
          <header
            class="place-dossier__head"
            :class="{ 'place-dossier__head--with-scene': Boolean(placeSceneMedia) }"
            data-ui="place-identity"
          >
            <div class="place-dossier__identity-row">
              <figure
                v-if="placeSceneMedia"
                class="place-dossier__scene"
                data-testid="place-scene-media"
              >
                <img
                  :src="placeSceneMedia.url"
                  alt="经审核允许公开展示的场所场景照片"
                  loading="lazy"
                  decoding="async"
                  referrerpolicy="no-referrer"
                />
              </figure>
              <PlaceTypeGlyph v-else :place-type="place.place_type" size="lg" />
              <div class="place-dossier__identity-copy">
                <h1 class="place-dossier__name" data-ui="place-name">{{ place.canonical_name }}</h1>
                <p class="muted place-dossier__meta">
                  {{ placeTypeLabel(place.place_type) }} ·
                  {{ place.canonical_address ?? "地址未收录" }}
                  <RouterLink
                    class="place-dossier__map-link"
                    data-testid="place-map-link"
                    :to="{ path: '/map', query: { place: placeId } }"
                  >
                    {{
                      placeSummary?.latitude != null && placeSummary?.longitude != null
                        ? "地图定位 →"
                        : "地图列表查看 →"
                    }}
                  </RouterLink>
                </p>
              </div>
            </div>
            <div class="place-dossier__actions" aria-label="场所操作">
              <RouterLink :to="`/place/${placeId}/evidence`" class="btn-inline">
                查看证据 →
              </RouterLink>
              <RouterLink :to="`/place/${placeId}/why`" class="btn-inline"> 为什么？ → </RouterLink>
              <RouterLink :to="`/contribute/${placeId}`" class="btn-inline">
                纠错 / 补充 →
              </RouterLink>
            </div>
            <p v-if="watchMsg" class="muted place-dossier__watch-msg" role="status">
              {{ watchMsg }}
            </p>
          </header>

          <!-- 2. 本地 section 导航（§15） -->
          <PlaceSectionNav :active="view" :place-id="placeId" />

          <!-- Rule UNKNOWN must never hide Reality / Staff / Facility / Evidence.
               A valid place always renders the Coexistence overview; unknown is
               expressed inside the Rule block as one fact dimension. -->
          <PlaceOverviewPane
            v-if="view === 'overview' && overviewFiveBlocks"
            :answer="answer"
            :coexistence="coexistence"
            :zone-summary="zones"
            :primary-source-label="primarySourceLabel"
            :latest-verified-at="latestVerifiedAt"
            :observation-count="presenceEventCount"
            :desktop="isDesktop"
          />
          <section
            v-if="view === 'overview'"
            class="place-follow-strip"
            aria-label="关注变化"
            data-ui="place-follow-strip"
          >
            <span class="place-follow-strip__label">关注变化</span>
            <template v-if="session.signedIn">
              <button
                class="place-dossier__watch"
                type="button"
                data-testid="watch-rule"
                :disabled="Boolean(watchBusy)"
                @click="toggleWatchDomain('rule')"
              >
                {{ watchingRule ? "规则变化已关注 · 取消" : "关注规则变化" }}
              </button>
              <button
                class="place-dossier__watch"
                type="button"
                data-testid="watch-reality"
                :disabled="Boolean(watchBusy)"
                @click="toggleWatchDomain('reality')"
              >
                {{ watchingReality ? "现场更新已关注 · 取消" : "关注现场更新" }}
              </button>
            </template>
            <RouterLink v-else class="btn-inline" to="/onboarding">登录后关注 →</RouterLink>
          </section>
          <div v-if="view === 'overview'" class="place-governance-row" data-ui="place-governance">
            <span class="muted">你是场所管理方？</span>
            <RouterLink :to="`/place/${placeId}/operator-claim`" class="btn-inline">
              认领场所并提交管理方规则 →
            </RouterLink>
          </div>
          <PlaceSpacePane
            v-else-if="view === 'space'"
            :zones="zones"
            :extras="extras"
            :facility-summary="coexistence?.facility_summary ?? []"
            :events="realityEvents"
          />
          <PlaceRulesPane
            v-else-if="view === 'rules'"
            :place-id="placeId"
            :current-rules="currentRules"
            :history-rules="historyRules"
            :source-map="sourceMap"
            :conditions="conditions"
            :answer="answer"
            :latest-verified-at="latestVerifiedAt"
            :zone-list="zones"
          />
          <PlaceRealityPane
            v-else-if="view === 'reality'"
            :events="realityEvents"
            :staff-responses="coexistence?.staff_response_summary ?? []"
            :zones="zones"
            :place-id="placeId"
            :signed-in="session.signedIn"
            :busy-event-id="realityConfirmation.busyEventId.value"
            :confirmation-message="realityConfirmation.message.value"
            @confirm="realityConfirmation.confirm"
          />
          <PlaceEvidencePane
            v-else-if="view === 'evidence'"
            :place-id="placeId"
            :events="realityEvents"
            :sources="sources"
            :rule-evidence="coexistence?.evidence_summary.rule_evidence ?? []"
          />
        </template>
      </main>

      <!-- sticky decision inspector（desktop only；§26 固定内容） -->
      <aside
        v-if="isDesktop && place"
        class="place-inspector"
        data-ui="place-inspector"
        aria-label="当前决策"
      >
        <DecisionInspector
          variant="place"
          :place="{ ...place, canonical_address: place.canonical_address ?? null }"
          :answer="answer"
          :answer-error="!coexistenceLoaded && !answer"
          :reality="coexistence?.reality_answer ?? null"
          :reality-error="coexistenceLoaded && !coexistence?.reality_answer"
          :snapshot="coexistence"
          :species-label="speciesLabel"
          :latest-verified-at="latestVerifiedAt"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.place-workspace {
  min-height: 100%;
}

.place-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-6);
  padding: var(--pa-space-4);
  max-width: var(--pa-layout-content-narrow);
  margin: 0 auto;
}

@media (min-width: 768px) {
  .place-workspace__body--split {
    flex-direction: row;
    align-items: flex-start;
    gap: var(--pa-space-7);
    max-width: none;
    padding: var(--pa-space-5) var(--pa-space-6);
  }

  .place-dossier {
    flex: 1 1 auto;
    min-width: 0;
    /* v0.2.5 §10：main column max width 820。 */
    max-width: 820px;
  }

  .place-inspector {
    flex: 0 0 var(--pa-layout-inspector);
    min-width: 0;
    position: sticky;
    top: var(--pa-space-5);
    padding-left: var(--pa-space-6);
    border-left: var(--pa-border-width) solid var(--pa-color-border-subtle);
  }
}

.place-dossier__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
  padding: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: var(--pa-color-surface-muted);
  margin-bottom: var(--pa-space-4);
}

.place-dossier__head--with-scene {
  padding: var(--pa-space-5);
}

.place-dossier__identity-row {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-3);
  min-width: 0;
}

.place-dossier__identity-copy {
  flex: 1 1 auto;
  min-width: 0;
}

.place-dossier__scene {
  flex: 0 0 152px;
  width: 152px;
  height: 96px;
  margin: 0;
  overflow: hidden;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface-muted);
}

.place-dossier__scene img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

/* Identity anchor is a neutral place-type glyph, not an invented venue photo.
   Distinguish the Place dossier header from the evidence sections below. */
.place-dossier__identity-row :deep(.place-type-glyph) {
  width: 52px;
  height: 52px;
  border-color: var(--pa-color-border);
  background: var(--pa-color-surface);
}

.place-dossier__map-link {
  margin-left: var(--pa-space-2);
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-sm);
  white-space: nowrap;
}

.place-dossier__map-link:hover,
.place-dossier__map-link:focus-visible {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.place-dossier__name {
  margin: 0;
  font-size: var(--pa-font-size-28);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-36);
  color: var(--pa-color-text-primary);
}
.place-dossier__meta {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-muted);
}

.place-dossier__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-4);
  margin-top: var(--pa-space-2);
}

.place-dossier__watch {
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-text-secondary);
  padding: 0;
  cursor: pointer;
}

.place-dossier__watch:hover,
.place-dossier__watch:focus-visible {
  color: var(--pa-color-accent);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.place-follow-strip {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-3);
  margin: var(--pa-space-6) 0 0;
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.place-follow-strip__label {
  margin-right: var(--pa-space-1);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.place-governance-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-5);
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-sm);
}

/* Sections: divider-led rhythm, not a flat wall of equal-weight panels. */
.place-section {
  margin-bottom: var(--pa-space-5);
}

.place-section__title {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.place-section__subtitle {
  margin: var(--pa-space-4) 0 var(--pa-space-2);
  font-size: var(--pa-font-size-17);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-secondary);
}

/* Unknown state (§27) minimal */
.place-unknown__headline {
  margin: 0;
  font-size: var(--pa-font-size-decision);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-decision);
  color: var(--pa-color-text-primary);
}

.place-unknown__list {
  margin: var(--pa-space-1) 0 var(--pa-space-4);
  padding-left: var(--pa-space-5);
}

@media (max-width: 767px) {
  .place-workspace__body {
    gap: var(--pa-space-5);
    padding: var(--pa-space-4);
  }

  .place-dossier__head,
  .place-dossier__head--with-scene {
    padding: var(--pa-space-4);
    margin-bottom: var(--pa-space-3);
  }

  .place-dossier__scene {
    flex-basis: 96px;
    width: 96px;
    height: 64px;
  }

  .place-dossier__actions {
    gap: var(--pa-space-3);
  }

  .place-dossier__watch {
    text-align: left;
  }

  .place-dossier__name {
    font-size: var(--pa-font-size-23);
    font-weight: var(--pa-font-weight-650);
    line-height: var(--pa-line-height-31);
  }
}
</style>
