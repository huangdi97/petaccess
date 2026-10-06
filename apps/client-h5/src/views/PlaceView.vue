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
  type PlaceExtras,
  type RuleView,
  type SourceView,
  type Zone,
} from "@petaccess/client-core";
import DecisionInspector from "../components/domain/DecisionInspector.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import PlaceSectionNav, { type PlaceViewKey } from "../components/place/PlaceSectionNav.vue";
import PlaceOverviewPane from "../components/place/PlaceOverviewPane.vue";
import PlaceSpacePane from "../components/place/PlaceSpacePane.vue";
import PlaceRulesPane from "../components/place/PlaceRulesPane.vue";
import PlaceRealityPane from "../components/place/PlaceRealityPane.vue";
import PlaceEvidencePane from "../components/place/PlaceEvidencePane.vue";
import { sourceLabel } from "../consumer/labels";
import { answerStatusKey } from "../answer";
import { presentDescription } from "../errors";
import { useBreakpoint } from "../composables/useBreakpoint";
import { snapshotFor } from "../consumer/repository";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

/** §15：?view= overview|space|rules|reality|evidence（deep link / refresh 安全）。 */
const VALID_VIEWS: readonly PlaceViewKey[] = ["overview", "space", "rules", "reality", "evidence"];
const view = computed<PlaceViewKey>(() => {
  const v = route.query.view;
  return typeof v === "string" && (VALID_VIEWS as readonly string[]).includes(v)
    ? (v as PlaceViewKey)
    : "overview";
});

const { desktop: isDesktop } = useBreakpoint();
const speciesLabel = computed(() => {
  const s = session.activePet?.species ?? "dog";
  if (session.activePet?.service_role === "working") return "服务犬";
  return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
});

const place = ref<PlaceDetail | null>(null);
const zones = ref<Zone[]>([]);
const rules = ref<RuleView[]>([]);
const realityEvents = ref<RealityEventView[]>([]);
const sources = ref<SourceView[]>([]);
const extras = ref<PlaceExtras | null>(null);

const answer = ref<AccessAnswer | null>(null);
const error = ref("");
const loading = ref(true);
const partial = ref<string[]>([]);
const watchingRule = ref(false);
const watchingReality = ref(false);
const watchMsg = ref("");
const confirmationMsg = ref("");
const confirmationBusyId = ref<string | null>(null);
const coexistence = ref<CoexistenceSnapshot | null>(null);
const coexistenceLoaded = ref(false);

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
  coexistenceLoaded.value = false;
  try {
    const { snapshot } = await snapshotFor(placeId.value);
    coexistence.value = snapshot;
    answer.value = snapshot.rule_answer;
  } catch (error) {
    coexistence.value = null;
    answer.value = null;
    throw error;
  } finally {
    coexistenceLoaded.value = true;
  }
}

// Mode switch (普通携带 ↔ 服务犬通行) must re-evaluate as the new animal:
// the answer text and verdict change with session.mode / activePet.
watch(
  () => [session.mode, session.activePet],
  () => {
    if (!placeId.value || loading.value) return;
    void evaluate().catch(() => {
      if (!partial.value.includes("当前答案")) partial.value.push("当前答案");
    });
  },
);

async function load() {
  loading.value = true;
  error.value = "";
  partial.value = [];
  const degrade = (label: string) => partial.value.push(label);
  await session.restore();
  try {
    place.value = await client.place(placeId.value);
  } catch (e) {
    error.value = presentDescription(e);
    loading.value = false;
    return;
  }
  if (session.signedIn) {
    try {
      const mine = await client.myWatches();
      watchingRule.value = mine.some(
        (item) =>
          item.watch_domain === "rule" &&
          item.target_type === "place" &&
          item.target_id === placeId.value,
      );
      watchingReality.value = mine.some(
        (item) =>
          item.watch_domain === "reality" &&
          item.target_type === "place" &&
          item.target_id === placeId.value,
      );
    } catch {
      degrade("关注状态");
    }
  } else {
    watchingRule.value = false;
    watchingReality.value = false;
  }
  try {
    zones.value = await client.zones(placeId.value);
  } catch {
    degrade("分区域");
  }
  try {
    rules.value = await client.rules(placeId.value);
  } catch {
    degrade("规则");
  }
  try {
    realityEvents.value = await client.realityEvents(placeId.value);
  } catch {
    degrade("现场记录");
  }
  try {
    const relevantSourceIds = new Set([
      ...rules.value.map((rule) => rule.source_id),
      ...realityEvents.value
        .map((event) => event.source_id)
        .filter((id): id is string => Boolean(id)),
    ]);
    sources.value = (await client.allSources()).filter((source) =>
      relevantSourceIds.has(source.id),
    );
  } catch {
    degrade("来源");
  }
  try {
    extras.value = await client.placeExtras(placeId.value);
  } catch {
    degrade("空间信息");
  }
  try {
    await evaluate();
  } catch {
    degrade("当前答案");
  }
  loading.value = false;
}

watch(
  placeId,
  () => {
    place.value = null;
    zones.value = [];
    rules.value = [];
    realityEvents.value = [];
    sources.value = [];
    extras.value = null;
    answer.value = null;
    error.value = "";
    partial.value = [];
    watchMsg.value = "";
    confirmationMsg.value = "";
    confirmationBusyId.value = null;
    watchingRule.value = false;
    watchingReality.value = false;
    coexistence.value = null;
    coexistenceLoaded.value = false;
    if (placeId.value) void load();
  },
  { immediate: true },
);

async function toggleWatchDomain(domain: "rule" | "reality") {
  watchMsg.value = "";
  try {
    const mine = await client.myWatches();
    const existing = mine.find(
      (watch) =>
        watch.watch_domain === domain &&
        watch.target_type === "place" &&
        watch.target_id === placeId.value,
    );
    if (existing) {
      await client.unwatch(existing.id);
      if (domain === "rule") watchingRule.value = false;
      else watchingReality.value = false;
    } else {
      await client.watch("place", placeId.value, domain);
      if (domain === "rule") watchingRule.value = true;
      else watchingReality.value = true;
    }
  } catch (e) {
    watchMsg.value = `关注状态未能更新：${presentDescription(e)}`;
  }
}

type RealityConfirmationType = "still_present" | "facility_still_present" | "facility_removed";

async function confirmReality(event: RealityEventView, type: RealityConfirmationType) {
  if (!session.signedIn || confirmationBusyId.value) return;
  confirmationMsg.value = "";
  confirmationBusyId.value = event.id;
  const observedAt = new Date().toISOString();
  try {
    await client.createRealityReport(placeId.value, {
      report: {
        origin: "on_site_now",
        place_id: placeId.value,
        subject_place_id: placeId.value,
        place_match_state: "exact_place",
        place_match_evidence_types: ["user_confirmation"],
        time_evidence_state: "live_device_time",
        observed_at: observedAt,
        time_certainty: "exact",
        fact_evidence_state: "first_hand_no_media",
        privacy_state: "private",
      },
      candidates: [],
      effort: null,
      confirmation: {
        confirmation_type: type,
        place_id: placeId.value,
        target_claim_id: event.id,
        observed_at: observedAt,
      },
      external_content: null,
    });
    confirmationMsg.value =
      type === "facility_removed"
        ? "已记录设施撤除线索，等待核验；历史设施记录不会被直接删除。"
        : "已记录本次现场确认，等待核验。";
  } catch (e) {
    confirmationMsg.value = `确认未提交：${presentDescription(e)}`;
  } finally {
    confirmationBusyId.value = null;
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
          <header class="place-dossier__head" data-ui="place-identity">
            <h1 class="place-dossier__name" data-ui="place-name">{{ place.canonical_name }}</h1>
            <p class="muted place-dossier__meta">
              {{ placeTypeLabel(place.place_type) }} ·
              {{ place.canonical_address ?? "地址未收录" }}
            </p>
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
                @click="toggleWatchDomain('rule')"
              >
                {{ watchingRule ? "规则变化已关注 · 取消" : "规则变化" }}
              </button>
              <button
                class="place-dossier__watch"
                type="button"
                data-testid="watch-reality"
                @click="toggleWatchDomain('reality')"
              >
                {{ watchingReality ? "现场更新已关注 · 取消" : "现场更新" }}
              </button>
            </template>
            <RouterLink v-else class="btn-inline" to="/onboarding">登录后关注 →</RouterLink>
          </section>
          <PlaceSpacePane
            v-else-if="view === 'space'"
            :zones="zones"
            :extras="extras"
            :facility-summary="coexistence?.facility_summary ?? []"
            :events="realityEvents"
          />
          <PlaceRulesPane
            v-else-if="view === 'rules'"
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
            :busy-event-id="confirmationBusyId"
            :confirmation-message="confirmationMsg"
            @confirm="confirmReality"
          />
          <PlaceEvidencePane
            v-else-if="view === 'evidence'"
            :place-id="placeId"
            :events="realityEvents"
            :sources="sources"
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
  gap: var(--pa-space-2);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  margin-bottom: var(--pa-space-4);
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

  .place-dossier__head {
    padding-bottom: var(--pa-space-4);
    margin-bottom: var(--pa-space-3);
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
