<script setup lang="ts">
/**
 * Search — List–Detail Workspace (UI_RECONSTRUCTION_DESIGN_FREEZE §9).
 *
 * Desktop: rail + 380–420px result pane + remaining detail inspector.
 * Result rows are divider-led (identity → type·address → PRIMARY DECISION →
 * 1 key condition → recent reality); the selected row gets a subtle tint plus
 * a single left indicator; the filter is a light panel (desktop) / bottom
 * sheet (mobile), never a pill wall.
 *
 * VISUAL FIDELITY (Goal §3.1): each row carries a strict information budget —
 * identity / type·distance / primary decision / one key condition / reality
 * freshness. The old engineering noise ("已核验：", effective-rule counts,
 * alias-match mechanics) is gone from the row; rule material presence stays
 * as a single quiet metadata line.
 *
 * Data: the ONLY consumer source is the repository (CoexistenceSnapshot SSOT,
 * bounded concurrency, cache with full query-context keys, epoch guard). The
 * Query Context primitive sits on top and changes session.mode → cache keys →
 * refetches. Lens (?lens=) changes Consumer presentation only (§8.5).
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  client,
  session,
  type BoundaryProfile,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { EMPTY_STATE_COPY, type StatusKey } from "@petaccess/design-tokens";
import DecisionInspector from "../components/domain/DecisionInspector.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import PaBottomSheet from "../components/ui/PaBottomSheet.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../answer";
import {
  evidenceLineFor,
  freshnessLineFor,
  lensOrderScore,
  lensProjection,
  realityLineFor,
  recentLineFor,
  type ConsumerLens,
} from "../consumer/rowView";
import { placeTypeLabel, ruleSummaryLabel } from "../consumer/labels";
import { useBreakpoint } from "../composables/useBreakpoint";
import { useOnline } from "../composables/useOnline";
import { presentDescription } from "../errors";
import {
  createEpoch,
  enrichRows,
  searchPlaces,
  snapshotFor,
  type RowFacts,
} from "../consumer/repository";

const route = useRoute();
const router = useRouter();
const { online } = useOnline();
const q = ref(typeof route.query.q === "string" ? route.query.q : "");
const results = ref<PlaceSummary[]>([]);
const facts = ref<Map<string, RowFacts>>(new Map());
const listStale = ref(false);
const listFetchedAtMs = ref<number | null>(null);

/** v0.9-R1 home entry lens (?lens=presence|indoor|dining|rules) — master §30. */
const LENS_HINTS: Record<string, string> = {
  presence: "正按「现场是否有动物出现」查看 —— 结果将优先展示近期有现场记录的场所",
  indoor: "正按「室内空间情况」查看 —— 结果将优先展示含室内区域的场所",
  dining: "正按「餐饮区域情况」查看 —— 结果将优先展示含餐饮区域的场所",
  rules: "正按「完整规则」查看 —— 结果为已收录规则的场所",
};
const statuses = ref<Record<string, StatusKey>>({});
const boundary = ref<BoundaryProfile | null>(null);
const searched = ref(false);
const loading = ref(false);
const error = ref("");
const epoch = createEpoch();
const speciesLabel = computed(() => {
  const s = session.activePet?.species ?? "dog";
  if (session.activePet?.service_role === "working") return "服务犬";
  return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
});
function lensProjectionFor(p: PlaceSummary) {
  const f = facts.value.get(p.id);
  return lensProjection(lensKey.value, f?.answer, f?.reality);
}
const preview = ref<{ snapshot: CoexistenceSnapshot | null; loading: boolean; error: string }>({
  snapshot: null,
  loading: false,
  error: "",
});
const selectedPlace = computed(() => results.value.find((p) => p.id === selectedId.value) ?? null);
const selectedStatus = computed(() =>
  selectedId.value && statuses.value[selectedId.value] !== undefined
    ? statuses.value[selectedId.value]
    : null,
);

const FILTERS = [
  { key: "MATCH", label: "明确允许" },
  { key: "CONDITIONAL", label: "有条件" },
  { key: "RESTRICTED", label: "明确限制" },
  { key: "UNKNOWN", label: "信息不足" },
  { key: "CONFLICT", label: "来源不一致" },
  { key: "verified", label: "已核验" },
];
const active = ref<string[]>([]);
const filterOpen = ref(false);

const lens = computed(() => (route.query.lens as string | undefined) ?? "");
const lensHint = computed(() => LENS_HINTS[lens.value] ?? "");
const lensKey = computed(() => (lens.value as ConsumerLens) || "");

const visible = computed(() => {
  const filtered = results.value.filter((p) => {
    if (!active.value.length) return true;
    const statusFilters = active.value.filter((k) => k !== "verified");
    const checks: boolean[] = [];
    if (statusFilters.length) {
      checks.push(statusFilters.includes(statuses.value[p.id] ?? "UNKNOWN"));
    }
    if (active.value.includes("verified")) checks.push(Boolean(p.rule_count > 0));
    return checks.every(Boolean);
  });
  // M3.1 lens ordering — presentation-only sort on server facts.
  if (!lensKey.value) return filtered;
  return [...filtered].sort((a, b) => {
    const fa = facts.value.get(a.id);
    const fb = facts.value.get(b.id);
    return (
      lensOrderScore(lensKey.value, fb?.answer, fb?.reality) -
      lensOrderScore(lensKey.value, fa?.answer, fa?.reality)
    );
  });
});

/** The one key condition for a row (or "" when none) — §32 row budget. */
function rowCondition(p: PlaceSummary): string {
  const answer = facts.value.get(p.id)?.answer;
  if (!answer) return "";
  const conditions = answerConditions(answer);
  return conditions[0] ?? "";
}

async function search() {
  if (!online.value) {
    error.value = "当前无网络连接，搜索需要联网。";
    return;
  }
  const query = q.value.trim();
  const n = epoch.begin();
  error.value = "";
  loading.value = true;
  searched.value = true;
  try {
    const list = query ? await searchPlaces(query) : await searchPlaces("");
    if (!epoch.isCurrent(n)) return; // a newer search superseded this one
    results.value = list.items;
    listStale.value = list.stale;
    listFetchedAtMs.value = list.fetchedAtMs;
    const f = await enrichRows(list.items);
    if (!epoch.isCurrent(n)) return; // a newer search superseded this one
    facts.value = f;
    const st: Record<string, StatusKey> = {};
    for (const [id, row] of f) st[id] = answerStatusKey(row.answer);
    statuses.value = st;
    if (query) {
      rememberRecent(query);
      syncRouteQuery(query);
    } else {
      syncRouteQuery("");
    }
    if (isDesktop.value && list.items.length) {
      const first = list.items[0];
      if (!selectedId.value || !list.items.some((p) => p.id === selectedId.value)) {
        void selectPlace(first);
      }
    }
  } catch (e) {
    if (epoch.isCurrent(n)) error.value = presentDescription(e);
  } finally {
    if (epoch.isCurrent(n)) loading.value = false;
  }
}

/** Keep the URL query in sync with what the user searched (B1/B2). */
function syncRouteQuery(query: string) {
  const current = typeof route.query.q === "string" ? route.query.q : "";
  if (current === query) return;
  void router.push({ query: { ...route.query, q: query || undefined } });
}

/** M3 B/D2: fetch the one CoexistenceSnapshot for the previewed place. */
async function selectPlace(p: PlaceSummary) {
  selectedId.value = p.id;
  if (!isDesktop.value) return;
  preview.value = { snapshot: null, loading: true, error: "" };
  try {
    preview.value = {
      snapshot: (await snapshotFor(p.id)).snapshot,
      loading: false,
      error: "",
    };
  } catch (e) {
    preview.value = { snapshot: null, loading: false, error: presentDescription(e) };
  }
}

/** Back/forward or an external deep link changes route.query.q → re-run. */
watch(
  () => route.query.q,
  (v) => {
    const next = typeof v === "string" ? v : "";
    if (next === q.value) return;
    q.value = next;
    void search();
  },
);

/** M2 §11 — recent searches: local-only, capped, clearable, signed-out safe. */
const SEARCH_RECENT_KEY = "pa.searchRecent.v1";
const MAX_SEARCH_RECENT = 5;
const recent = ref<string[]>([]);

function saveRecent() {
  try {
    localStorage.setItem(SEARCH_RECENT_KEY, JSON.stringify(recent.value));
  } catch {
    /* storage unavailable (private mode): history simply does not persist */
  }
}

function rememberRecent(text: string) {
  recent.value = [text, ...recent.value.filter((t) => t !== text)].slice(0, MAX_SEARCH_RECENT);
  saveRecent();
}

function clearRecent() {
  recent.value = [];
  try {
    localStorage.removeItem(SEARCH_RECENT_KEY);
  } catch {
    /* ignore */
  }
}

function loadRecent() {
  try {
    const raw = localStorage.getItem(SEARCH_RECENT_KEY);
    recent.value = raw ? (JSON.parse(raw) as string[]).slice(0, MAX_SEARCH_RECENT) : [];
  } catch {
    recent.value = [];
  }
}

function useRecent(text: string) {
  q.value = text;
  void search();
}

function clearSearch() {
  q.value = "";
  if (searched.value) void search();
}

const emptyDescription = computed(() =>
  results.value.length
    ? "当前筛选下没有结果。清除筛选可查看全部（含信息不足的场所）。"
    : EMPTY_STATE_COPY.SEARCH.description,
);

onMounted(async () => {
  await session.restore();
  loadRecent();
  if (session.signedIn) {
    try {
      boundary.value = (await client.defaultBoundaryProfile()).profile;
    } catch {
      boundary.value = null;
    }
  }
  await search();
});

const { desktop: isDesktop, mobile: isMobile } = useBreakpoint();
const selectedId = ref<string | null>(null);
</script>

<template>
  <div class="search-workspace" data-testid="search-workspace" data-ui="search-shell">
    <QueryContextBar />

    <div class="search-workspace__body" :class="{ 'search-workspace__body--split': isDesktop }">
      <!-- result pane -->
      <section class="search-result-pane" aria-label="搜索结果" data-ui="search-results-pane">
        <header class="search-result-pane__head">
          <h1 class="visually-hidden">搜索场所规则</h1>
          <form class="search-field" @submit.prevent="search">
            <input
              v-model="q"
              aria-label="搜索场所"
              placeholder="搜索场所、商圈或地址"
              data-testid="search-input"
              @keydown.enter="search"
            />
            <button
              v-if="q"
              type="button"
              class="search-clear"
              aria-label="清除"
              data-testid="search-clear"
              @click="clearSearch"
            >
              ×
            </button>
            <button
              type="submit"
              class="primary search-submit"
              :disabled="loading"
              data-testid="search-btn"
            >
              {{ loading ? "搜索中…" : "搜索" }}
            </button>
          </form>
        </header>

        <div v-if="recent.length" class="recent-bar" data-testid="search-recent">
          <div class="recent-bar__row">
            <span class="muted">最近搜索</span>
            <button
              type="button"
              class="recent-bar__clear"
              data-testid="clear-search-recent"
              @click="clearRecent"
            >
              清除
            </button>
          </div>
          <div class="recent-bar__items">
            <button
              v-for="t in recent"
              :key="t"
              type="button"
              class="recent-bar__item"
              :data-testid="'recent-search-' + t"
              @click="useRecent(t)"
            >
              {{ t }}
            </button>
          </div>
        </div>

        <div v-if="lensHint" class="lens-line muted" data-testid="lens-hint">
          {{ lensHint }}
        </div>

        <!-- filter: light panel (desktop) / bottom sheet (mobile) — never pills -->
        <div class="filter-bar">
          <button
            type="button"
            class="filter-toggle"
            data-testid="filter-toggle"
            data-ui="search-filter-toggle"
            :aria-expanded="filterOpen"
            @click="filterOpen = !filterOpen"
          >
            筛选{{ active.length ? ` ${active.length}` : "" }}
          </button>
          <button
            v-if="active.length"
            type="button"
            class="filter-bar__clear"
            data-testid="filter-clear"
            @click="active = []"
          >
            清除筛选
          </button>
        </div>
        <div v-if="isDesktop && filterOpen" class="filter-panel">
          <div class="filter-options">
            <div class="filter-options__row" v-for="f in FILTERS" :key="f.key">
              <label>
                <input
                  type="checkbox"
                  :checked="active.includes(f.key)"
                  @change="
                    active = active.includes(f.key)
                      ? active.filter((k) => k !== f.key)
                      : [...active, f.key]
                  "
                />
                {{ f.label }}
              </label>
            </div>
            <p class="muted filter-panel__hint">筛选只影响显示，不改变任何结论。</p>
          </div>
        </div>

        <PaBottomSheet
          :open="isMobile && filterOpen"
          title="筛选结果"
          ui="search-filter-sheet"
          @close="filterOpen = false"
        >
          <div class="filter-options">
            <div class="filter-options__row" v-for="f in FILTERS" :key="f.key">
              <label>
                <input
                  type="checkbox"
                  :checked="active.includes(f.key)"
                  @change="
                    active = active.includes(f.key)
                      ? active.filter((k) => k !== f.key)
                      : [...active, f.key]
                  "
                />
                {{ f.label }}
              </label>
            </div>
            <p class="muted filter-panel__hint">筛选只影响显示，不改变任何结论。</p>
          </div>
        </PaBottomSheet>

        <SkeletonList v-if="loading" :rows="3" />
        <StateMessage v-else-if="error" kind="ERROR" :description="error">
          <template #action>
            <button type="button" class="primary" @click="search">重试</button>
          </template>
        </StateMessage>
        <StateMessage
          v-else-if="searched && !visible.length"
          kind="PARTIAL"
          data-testid="search-empty"
          :title="EMPTY_STATE_COPY.SEARCH.title"
          :description="emptyDescription"
        >
          <template #action>
            <div class="row" style="justify-content: center">
              <RouterLink
                class="btn primary"
                to="/contribute"
                data-testid="search-empty-contribute"
              >
                提交场所线索
              </RouterLink>
              <button
                v-if="active.length"
                type="button"
                class="filter-bar__clear"
                @click="active = []"
              >
                清除筛选
              </button>
            </div>
          </template>
        </StateMessage>
        <template v-else>
          <p
            v-if="freshnessLineFor(listStale, listFetchedAtMs, !online)"
            class="muted search-freshness"
            data-testid="search-freshness"
          >
            {{ freshnessLineFor(listStale, listFetchedAtMs, !online) }}
          </p>
          <p class="search-count" data-testid="search-count" data-ui="search-count">
            找到 {{ visible.length }} 个结果
          </p>
          <ul class="result-list" role="list">
            <li
              v-for="p in visible"
              :key="p.id"
              class="result-row"
              :class="{ 'result-row--selected': selectedId === p.id }"
              :data-ui="selectedId === p.id ? 'search-selected-row' : 'search-result-row'"
              :aria-current="selectedId === p.id ? 'true' : undefined"
            >
              <RouterLink
                :to="{ name: 'place', params: { id: p.id } }"
                class="result-row__link"
                :data-testid="'result-' + p.canonical_name"
                @mouseenter="selectPlace(p)"
                @focus="selectPlace(p)"
              >
                <!-- head: identity left, recency + status right -->
                <div class="result-row__head">
                  <div class="result-row__identity">
                    <strong class="result-row__name">{{ p.canonical_name }}</strong>
                    <span class="muted result-row__meta">
                      {{ placeTypeLabel(p.place_type) }}
                      <template v-if="p.distance_m"> · {{ Math.round(p.distance_m) }}m</template>
                    </span>
                  </div>
                  <div class="result-row__head-right">
                    <span v-if="recentLineFor(facts.get(p.id)?.reality)" class="result-row__recent">
                      {{ recentLineFor(facts.get(p.id)?.reality) }}
                    </span>
                    <StatusBadge :semantic="statuses[p.id] ?? 'UNKNOWN'" />
                  </div>
                </div>

                <!-- lens projection (presentation-only) -->
                <template v-if="lensKey">
                  <p
                    v-if="lensProjectionFor(p).headline === 'rule' && facts.get(p.id)?.answer"
                    class="result-row__conclusion"
                    data-testid="row-lens-headline"
                  >
                    {{
                      facts.get(p.id)?.answer?.normative_result.summary ||
                      answerVerdictLabel(facts.get(p.id)?.answer)
                    }}
                  </p>
                  <p v-else class="result-row__conclusion" data-testid="row-lens-headline">
                    {{ lensProjectionFor(p).realityLine }}
                  </p>
                  <p
                    v-if="lensProjectionFor(p).zoneFacts.length"
                    class="muted result-row__zonefacts"
                    data-testid="row-lens-zones"
                  >
                    相关区域：{{ lensProjectionFor(p).zoneFacts.join("、") }}
                  </p>
                </template>

                <!-- transport error ≠ domain fact -->
                <p
                  v-if="facts.get(p.id)?.answerError"
                  class="result-row__error"
                  data-testid="row-answer-error"
                >
                  规则结论暂时无法取得 —— 请检查网络后重试。
                </p>
                <!-- primary decision: verdict + 1 key condition on one dense line -->
                <p
                  v-else-if="facts.get(p.id)?.answer"
                  class="result-row__decision"
                  data-testid="row-rule"
                >
                  {{ answerVerdictLabel(facts.get(p.id)?.answer) }}
                  <span v-if="rowCondition(p)" class="result-row__condition">
                    · {{ rowCondition(p) }}
                  </span>
                </p>

                <!-- reality + evidence: one quiet line -->
                <div class="result-row__reality" data-testid="result-reality">
                  <p v-if="facts.get(p.id)?.realityError" class="result-row__error">
                    现场信息暂时无法取得 —— 请检查网络后重试。
                  </p>
                  <p v-else>
                    {{ realityLineFor(facts.get(p.id)?.reality) }}
                    <span v-if="evidenceLineFor(facts.get(p.id)?.reality)" class="muted">
                      · {{ evidenceLineFor(facts.get(p.id)?.reality) }}
                    </span>
                  </p>
                </div>

                <!-- 极轻元数据：规则材料存在性 + 父场所 -->
                <div class="result-row__rules" data-testid="result-rules">
                  {{ ruleSummaryLabel(p) }}
                  <span v-if="p.parent_place_name" class="muted" data-testid="result-branch">
                    · 所属 {{ p.parent_place_name }}
                  </span>
                </div>
              </RouterLink>
            </li>
          </ul>
        </template>
      </section>

      <!-- detail inspector (desktop only) -->
      <aside
        v-if="isDesktop"
        class="search-inspector"
        data-ui="search-detail-pane"
        aria-label="场所详情"
      >
        <DecisionInspector
          data-ui="search-detail-content"
          :place="selectedPlace"
          :status="selectedStatus"
          :answer="selectedPlace ? (facts.get(selectedPlace.id)?.answer ?? null) : null"
          :answer-error="selectedPlace ? Boolean(facts.get(selectedPlace.id)?.answerError) : false"
          :reality="selectedPlace ? (facts.get(selectedPlace.id)?.reality ?? null) : null"
          :reality-error="
            selectedPlace ? Boolean(facts.get(selectedPlace.id)?.realityError) : false
          "
          :snapshot="preview.snapshot"
          :stale="selectedPlace ? Boolean(facts.get(selectedPlace.id)?.stale) : false"
          :fetched-at-ms="selectedPlace ? (facts.get(selectedPlace.id)?.fetchedAtMs ?? null) : null"
          :offline="!online"
          :species-label="speciesLabel"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.search-workspace {
  min-height: 100%;
}

.search-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding: var(--pa-space-4);
  max-width: var(--pa-layout-content-narrow);
  margin: 0 auto;
}

@media (min-width: 768px) {
  .search-workspace__body--split {
    flex-direction: row;
    align-items: stretch;
    max-width: 1180px;
    margin: 0 auto;
  }

  .search-result-pane {
    flex: 0 0 var(--pa-layout-result-pane);
    border-right: var(--pa-border-width) solid var(--pa-color-border);
    padding-right: var(--pa-space-5);
  }

  .search-inspector {
    flex: 1 1 auto;
    min-width: 0;
    max-width: var(--pa-layout-detail-content);
    padding-left: var(--pa-space-40);
    position: sticky;
    top: var(--pa-space-4);
    align-self: stretch;
  }
}

.search-field {
  display: flex;
  gap: var(--pa-space-2);
  align-items: center;
}

.search-field input {
  flex: 1;
  min-width: 0;
}

.search-submit {
  flex-shrink: 0;
}

.search-clear {
  border: none;
  background: transparent;
  color: var(--pa-color-text-muted);
  cursor: pointer;
  font-size: var(--pa-font-size-xl);
  line-height: 1;
  padding: var(--pa-space-1) var(--pa-space-2);
}

.recent-bar {
  margin: var(--pa-space-3) 0 var(--pa-space-2);
}

.recent-bar__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Recent chips are quiet text buttons, not pills (Goal: clear/recent/filter
 * never become visual heroes; contract NO_ROW_PILL_WALL = 0). */
.recent-bar__clear,
.filter-bar__clear {
  border: none;
  background: none;
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-md);
  min-height: var(--pa-size-control-md);
  padding: var(--pa-space-1) var(--pa-space-2);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.recent-bar__clear:hover,
.filter-bar__clear:hover {
  color: var(--pa-color-accent);
  text-decoration-color: var(--pa-color-accent);
}

.recent-bar__items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-1);
}

.recent-bar__item {
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-md);
  min-height: var(--pa-size-control-md);
  padding: var(--pa-space-1) var(--pa-space-3);
  cursor: pointer;
}

.recent-bar__item:hover {
  border-color: var(--pa-color-border-strong);
  color: var(--pa-color-text-primary);
}

.lens-line {
  margin: var(--pa-space-2) 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  margin: var(--pa-space-2) 0;
}

.filter-toggle {
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
  padding: var(--pa-space-1) var(--pa-space-3);
  font-size: var(--pa-font-size-md);
  cursor: pointer;
}

.filter-panel {
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  padding-bottom: var(--pa-space-3);
  margin-bottom: var(--pa-space-2);
}

.filter-options__row {
  min-height: var(--pa-size-control-md);
  display: flex;
  align-items: center;
}

.filter-options__row input {
  width: auto;
  margin-right: var(--pa-space-2);
}

.filter-panel__hint {
  margin: var(--pa-space-2) 0 0;
}

.search-freshness {
  margin: var(--pa-space-2) 0;
}

.search-count {
  margin: var(--pa-space-2) 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}

.result-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

/* Result rows are soft raised rows — never cards, never hard table lines.
 * 生活气息收口（2026-09-30）：12px 圆角 + 轻投影替代 0px 硬边表格感；选中 =
 * 暖 tint + 2px accent 左指示（Goal §32 的「1 clear indicator」保留）。 */
.result-row {
  position: relative;
  border-radius: var(--pa-radius-row);
  background: var(--pa-color-surface);
  box-shadow: var(--pa-elevation-1);
  margin-bottom: var(--pa-space-2);
}

.result-row--selected {
  background: var(--pa-color-surface-warm-strong);
}

.result-row--selected::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--pa-border-width-strong);
  background: var(--pa-color-accent);
  border-radius: var(--pa-radius-row) 0 0 var(--pa-radius-row);
}

.result-row__link {
  display: block;
  padding: var(--pa-space-2) var(--pa-space-1);
  text-decoration: none;
  color: inherit;
}

.result-row__link:hover {
  background: var(--pa-color-surface-interactive);
}

.result-row__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--pa-space-3);
}

.result-row__identity {
  min-width: 0;
}

.result-row__head-right {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  flex-shrink: 0;
}

.result-row__recent {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
  white-space: nowrap;
}

.result-row__name {
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.result-row__meta {
  display: block;
  margin-top: var(--pa-space-1);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-tight);
  overflow-wrap: anywhere;
}

.result-row__conclusion {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.result-row__zonefacts {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
}

.result-row__error {
  margin: var(--pa-space-1) 0 0;
  color: var(--pa-color-text-secondary);
}

/* Primary decision: the scannable line of the row; condition sits inline. */
.result-row__decision {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.result-row__condition {
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-regular);
  color: var(--pa-color-text-secondary);
}

.result-row__reality {
  margin-top: var(--pa-space-1);
  padding-top: var(--pa-space-1);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-14);
  line-height: var(--pa-line-height-tight);
}

.result-row__reality p {
  margin: 0;
}

.result-row__rules {
  margin-top: var(--pa-space-1);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-disabled);
}

.result-row__rules .muted {
  color: var(--pa-color-text-disabled);
}

/* Mobile compression (Goal §33): ≤4 visual groups; rule-count / branch noise
 * does not belong on a phone scan. */
@media (max-width: 767px) {
  .result-row__rules {
    display: none;
  }

  .result-row__link {
    padding: var(--pa-space-3) 0;
  }

  .result-row__name {
    font-size: var(--pa-font-size-xl);
  }

  .result-row__meta {
    font-size: var(--pa-font-size-md);
  }

  .result-row__decision {
    font-size: var(--pa-font-size-xl);
  }
}
</style>
