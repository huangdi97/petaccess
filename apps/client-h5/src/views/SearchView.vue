<script setup lang="ts">
/**
 * Search — List–Detail Workspace (UI_RECONSTRUCTION_DESIGN_FREEZE §9).
 *
 * Desktop: rail + 360–420px result pane + remaining detail inspector.
 * Result rows are divider-led (identity/distance → conclusion/conditions →
 * recent reality + sources); the selected row gets a subtle tint; the filter
 * is a light panel ("筛选 N"), never a pill wall. Mobile: results → tap →
 * place, no squeezed two-pane.
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
  placeTypeLabel,
  ruleSummaryLabel,
  session,
  type BoundaryProfile,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { EMPTY_STATE_COPY, type StatusKey } from "@petaccess/design-tokens";
import DecisionInspector from "../components/domain/DecisionInspector.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { answerScopeLabel, answerStatusKey } from "../answer";
import { lensOrderScore, lensProjection, type ConsumerLens } from "../consumer/rowView";
import { evidenceLineFor, freshnessLineFor, realityLineFor } from "../consumer/rowView";
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

const { desktop: isDesktop } = useBreakpoint();
const selectedId = ref<string | null>(null);
</script>

<template>
  <div class="search-workspace" data-testid="search-workspace">
    <QueryContextBar />

    <div class="search-workspace__body" :class="{ 'search-workspace__body--split': isDesktop }">
      <!-- result pane -->
      <section class="search-result-pane" aria-label="搜索结果">
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
              class="pill"
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
              class="pill"
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

        <!-- filter: a light panel, never a pill wall -->
        <div class="filter-bar">
          <button
            type="button"
            class="filter-toggle"
            data-testid="filter-toggle"
            :aria-expanded="filterOpen"
            @click="filterOpen = !filterOpen"
          >
            筛选{{ active.length ? ` ${active.length}` : "" }}
          </button>
          <button
            v-if="active.length"
            type="button"
            class="pill"
            data-testid="filter-clear"
            @click="active = []"
          >
            清除筛选
          </button>
        </div>
        <div v-if="filterOpen" class="filter-panel">
          <div class="filter-panel__option" v-for="f in FILTERS" :key="f.key">
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
              <button v-if="active.length" type="button" class="pill" @click="active = []">
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
          <ul class="result-list" role="list">
            <li
              v-for="p in visible"
              :key="p.id"
              class="result-row"
              :class="{ 'result-row--selected': selectedId === p.id }"
              :aria-current="selectedId === p.id ? 'true' : undefined"
            >
              <RouterLink
                :to="{ name: 'place', params: { id: p.id } }"
                class="result-row__link"
                :data-testid="'result-' + p.canonical_name"
                @mouseenter="selectPlace(p)"
                @focus="selectPlace(p)"
              >
                <div class="result-row__head">
                  <div class="result-row__identity">
                    <strong class="result-row__name">{{ p.canonical_name }}</strong>
                    <span class="muted result-row__meta">
                      {{ placeTypeLabel(p.place_type) }} ·
                      {{ p.canonical_address ?? "地址待补充" }}
                      <span v-if="p.distance_m"> · {{ Math.round(p.distance_m) }}m</span>
                    </span>
                  </div>
                  <StatusBadge :semantic="statuses[p.id] ?? 'UNKNOWN'" />
                </div>

                <!-- M3.1 lens projection：真实改变 Consumer 呈现（rule-first / reality-first），
                     不改变任何 domain 事实；indoor/dining 仅上浮服务端返回的 observed_zones。 -->
                <template v-if="lensKey">
                  <p
                    v-if="lensProjectionFor(p).headline === 'rule' && facts.get(p.id)?.answer"
                    class="result-row__conclusion"
                    data-testid="row-lens-headline"
                  >
                    {{
                      facts.get(p.id)?.answer?.normative_result.summary ||
                      "已核验：" + answerScopeLabel(facts.get(p.id)?.answer, speciesLabel)
                    }}
                  </p>
                  <p v-else class="result-row__conclusion" data-testid="row-lens-headline">
                    {{ lensProjectionFor(p).realityLine }}
                  </p>
                  <p
                    v-if="lensProjectionFor(p).zoneFacts.length"
                    class="muted"
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
                <template v-else-if="facts.get(p.id)?.answer">
                  <p class="result-row__conclusion" data-testid="row-rule">
                    已核验：{{ answerScopeLabel(facts.get(p.id)?.answer, speciesLabel) }}
                  </p>
                  <p
                    v-if="facts.get(p.id)?.answer?.condition_evaluation?.conditions?.length"
                    class="muted"
                  >
                    条件：{{ answerScopeLabel(facts.get(p.id)?.answer, speciesLabel) }}
                  </p>
                </template>

                <div v-if="p.parent_place_name" class="muted" data-testid="result-branch">
                  所属 {{ p.parent_place_name }}
                </div>
                <div v-if="p.matched_alias" class="muted" data-testid="result-alias">
                  以「{{ p.matched_alias }}」匹配（曾用名／别称）
                </div>
                <div class="muted" data-testid="result-rules">{{ ruleSummaryLabel(p) }}</div>

                <!-- Reality 摘要 + Evidence/Freshness 元数据 -->
                <div class="result-row__reality" data-testid="result-reality">
                  <p v-if="facts.get(p.id)?.realityError" class="result-row__error">
                    现场信息暂时无法取得 —— 请检查网络后重试。
                  </p>
                  <template v-else>
                    <p>{{ realityLineFor(facts.get(p.id)?.reality) }}</p>
                    <p v-if="evidenceLineFor(facts.get(p.id)?.reality)" class="muted">
                      {{ evidenceLineFor(facts.get(p.id)?.reality) }}
                    </p>
                  </template>
                </div>
              </RouterLink>
            </li>
          </ul>
        </template>
      </section>

      <!-- detail inspector (desktop only) -->
      <aside v-if="isDesktop" class="search-inspector" aria-label="场所详情">
        <DecisionInspector
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
    align-items: flex-start;
    max-width: none;
  }

  .search-result-pane {
    flex: 0 0 var(--pa-layout-result-pane);
    border-right: var(--pa-border-width) solid var(--pa-color-border);
    padding-right: var(--pa-space-5);
  }

  .search-inspector {
    flex: 1 1 auto;
    min-width: 0;
    position: sticky;
    top: var(--pa-space-4);
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
  margin: var(--pa-space-4) 0 var(--pa-space-2);
}

.recent-bar__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-bar__items {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-2);
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

.filter-panel__option {
  min-height: var(--pa-size-control-md);
  display: flex;
  align-items: center;
}

.filter-panel__option input {
  width: auto;
  margin-right: var(--pa-space-2);
}

.filter-panel__hint {
  margin: var(--pa-space-2) 0 0;
}

.search-freshness {
  margin: var(--pa-space-2) 0;
}

.result-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.result-row {
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.result-row--selected {
  background: var(--pa-color-accent-weak);
}

.result-row__link {
  display: block;
  padding: var(--pa-space-3) var(--pa-space-2);
  text-decoration: none;
  color: inherit;
}

.result-row__link:hover {
  background: var(--pa-color-surface-interactive);
}

.result-row__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--pa-space-3);
}

.result-row__name {
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.result-row__meta {
  display: block;
  margin-top: var(--pa-space-1);
}

.result-row__conclusion {
  margin: var(--pa-space-2) 0 0;
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.result-row__error {
  margin: var(--pa-space-2) 0 0;
  color: var(--pa-color-text-secondary);
}

.result-row__reality {
  margin-top: var(--pa-space-2);
  padding-top: var(--pa-space-2);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-md);
}

.result-row__reality p {
  margin: 0 0 var(--pa-space-1);
}
</style>
