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
  type ObservationView,
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
const observations = ref<ObservationView[]>([]);
const sources = ref<SourceView[]>([]);
const extras = ref<PlaceExtras | null>(null);

const answer = ref<AccessAnswer | null>(null);
const error = ref("");
const loading = ref(true);
const partial = ref<string[]>([]);
const watching = ref(false);
const quickMsg = ref("");
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

function queryServiceRole(): string {
  if (session.mode === "service_dog") return "working";
  return session.activePet?.service_role ?? "none";
}

async function evaluate() {
  const animal = session.activePet?.species ?? "dog";
  answer.value = await client.accessAnswer(placeId.value, {
    animal,
    service_role: queryServiceRole(),
    declared_role: session.activePet?.declared_role ?? null,
    action: "enter",
  });
}

async function load() {
  loading.value = true;
  error.value = "";
  partial.value = [];
  const degrade = (label: string) => partial.value.push(label);
  try {
    place.value = await client.place(placeId.value);
  } catch (e) {
    error.value = presentDescription(e);
    loading.value = false;
    return;
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
    observations.value = await client.observations(placeId.value);
  } catch {
    degrade("现场记录");
  }
  try {
    sources.value = (await client.allSources()).filter((s) =>
      rules.value.some((r) => r.source_id === s.id),
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
  try {
    coexistence.value = (await snapshotFor(placeId.value)).snapshot;
  } catch {
    coexistence.value = null;
  }
  coexistenceLoaded.value = true;
  loading.value = false;
}

watch(
  placeId,
  () => {
    place.value = null;
    zones.value = [];
    rules.value = [];
    observations.value = [];
    sources.value = [];
    extras.value = null;
    answer.value = null;
    error.value = "";
    partial.value = [];
    quickMsg.value = "";
    coexistence.value = null;
    coexistenceLoaded.value = false;
    if (placeId.value) void load();
  },
  { immediate: true },
);

async function toggleWatch() {
  try {
    const mine = await client.myWatches();
    const existing = mine.find((w) => w.target_type === "place" && w.target_id === placeId.value);
    if (existing) {
      await client.unwatch(existing.id);
      watching.value = false;
    } else {
      await client.watch("place", placeId.value);
      watching.value = true;
    }
  } catch (e) {
    quickMsg.value = `关注失败（需登录）：${presentDescription(e)}`;
  }
}

async function quickConfirm(ruleId: string, result: "still_valid" | "changed" | "uncertain") {
  quickMsg.value = "";
  try {
    await client.verify({
      place_id: placeId.value,
      rule_id: ruleId,
      result,
      note: "Quick Confirm（现场快捷确认）",
      proximity_verified: true,
      distance_bucket: "<100m",
      accuracy_bucket: "10-50m",
    });
    quickMsg.value =
      result === "still_valid"
        ? "已记录：规则仍有效 ✓"
        : result === "changed"
          ? "已记录：规则已变化，进入复核"
          : "已记录：不确定";
  } catch (e) {
    quickMsg.value = `需要登录后才能核验：${presentDescription(e)}`;
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
            <div class="row place-dossier__actions">
              <button @click="toggleWatch">
                {{ watching ? "已关注规则变化 ✓（点击取消）" : "关注此场所规则变化" }}
              </button>
              <RouterLink :to="`/place/${placeId}/why`" class="btn-inline">
                为什么是这个结果 →
              </RouterLink>
            </div>
          </header>

          <!-- 2. 本地 section 导航（§15） -->
          <PlaceSectionNav :active="view" :place-id="placeId" />

          <!-- 3. 按 view 渲染对应 pane -->
          <PlaceOverviewPane
            v-if="view === 'overview' && overviewFiveBlocks"
            :answer="answer"
            :coexistence="coexistence"
            :zone-summary="zones"
            :primary-source-label="primarySourceLabel"
            :latest-verified-at="latestVerifiedAt"
            :observation-count="observations.length"
          />
          <PlaceSpacePane v-else-if="view === 'space'" :zones="zones" :extras="extras" />
          <PlaceRulesPane
            v-else-if="view === 'rules'"
            :current-rules="currentRules"
            :history-rules="historyRules"
            :source-map="sourceMap"
            :conditions="conditions"
            :answer="answer"
            :latest-verified-at="latestVerifiedAt"
          />
          <PlaceRealityPane
            v-else-if="view === 'reality'"
            :observations="observations"
            :zones="zones"
            :place-id="placeId"
          />
          <PlaceEvidencePane
            v-else-if="view === 'evidence'"
            :observations="observations"
            :sources="sources"
            :rule-evidence-count="currentRules.length"
            :reviewed-count="observations.length"
          />

          <!-- 未知态（§27）：不渲染空 section 全家福 -->
          <section
            v-if="placeState === 'unknown'"
            class="place-section place-unknown"
            data-testid="place-unknown"
          >
            <h2 class="place-section__title">当前查询</h2>
            <p class="place-unknown__headline">信息不足</p>
            <p class="muted">当前没有足够可靠规则，无法确认是否允许进入。</p>
            <h3 class="place-section__subtitle">已有信息</h3>
            <ul class="muted place-unknown__list">
              <li v-if="!currentRules.length">暂无正式规则</li>
              <li v-if="!observations.length">暂无足够现场记录</li>
            </ul>
            <div class="row">
              <RouterLink class="btn" :to="`/contribute/${placeId}`">提交规则线索</RouterLink>
              <RouterLink class="btn" :to="`/place/${placeId}/reality`">记录现场情况</RouterLink>
            </div>
          </section>

          <!-- 现场快捷确认（保留在概览底部之外的次级位置） -->
          <section
            v-if="view === 'overview' && currentRules.length"
            class="place-section"
            data-testid="quick-confirm"
          >
            <h2 class="place-section__title">快速确认</h2>
            <div class="muted">页面显示当前规则，目前仍然如此吗？</div>
            <div class="row" style="margin-top: 8px">
              <button @click="quickConfirm(currentRules[0]?.id ?? '', 'still_valid')">
                仍然如此
              </button>
              <button @click="quickConfirm(currentRules[0]?.id ?? '', 'changed')">已变化</button>
              <button @click="quickConfirm(currentRules[0]?.id ?? '', 'uncertain')">不确定</button>
            </div>
            <div v-if="quickMsg" class="notice" data-testid="quick-msg">{{ quickMsg }}</div>
          </section>
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
    max-width: none;
    padding: var(--pa-space-4) var(--pa-space-6);
  }

  .place-dossier {
    flex: 1 1 auto;
    min-width: 0;
    max-width: 860px;
  }

  .place-inspector {
    flex: 0 0 var(--pa-layout-inspector);
    min-width: 0;
    position: sticky;
    top: var(--pa-space-4);
  }
}

.place-dossier__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  padding-bottom: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  margin-bottom: var(--pa-space-5);
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
  margin-top: var(--pa-space-2);
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
  .place-dossier__name {
    font-size: var(--pa-font-size-23);
    font-weight: var(--pa-font-weight-650);
    line-height: var(--pa-line-height-31);
  }
}
</style>
