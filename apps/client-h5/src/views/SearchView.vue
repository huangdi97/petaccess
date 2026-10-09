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
  platformStorage,
  session,
  type BoundaryProfile,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { type StatusKey } from "@petaccess/design-tokens";
import DecisionInspector from "../components/domain/DecisionInspector.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import PaBottomSheet from "../components/ui/PaBottomSheet.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import PlaceTypeGlyph from "../components/domain/PlaceTypeGlyph.vue";
import { answerConditions, answerPrimarySummary, answerStatusKey } from "../answer";
import {
  coexistenceEvidenceLine,
  freshnessLineFor,
  lensOrderScore,
  lensProjection,
  type ConsumerLens,
} from "../consumer/rowView";
import { placeTypeLabel } from "../consumer/labels";
import { queryAnimalLabel } from "../consumer/queryContext";
import { useBreakpoint } from "../composables/useBreakpoint";
import { useOnline } from "../composables/useOnline";
import { usePlaceSceneMedia } from "../composables/usePlaceSceneMedia";
import { publicSourceIssuer } from "../consumer/sourcePrivacy";
import { presentDescription } from "../errors";
import {
  createEpoch,
  currentQueryContext,
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
const previewEpoch = createEpoch();

/**
 * O6 capture-state integrity: page/state/fixture narrated by this component.
 * The oracle compares these against the real DOM before a screenshot counts
 * as evidence — state reflects what is actually on screen (ready / selected /
 * empty / filter), never what a test wanted to see.
 */
const uiState = computed<string>(() => {
  if (filterOpen.value) return "filter";
  if (searched.value && !loading.value && !error.value && visible.value.length === 0)
    return "empty";
  if (searched.value && !loading.value && !error.value && selectedId.value) return "ready-selected";
  return "ready";
});
const uiFixture = computed<string>(() => {
  if (uiState.value === "filter") return "search-filter-v1";
  if (uiState.value === "empty") return "search-empty-v1";
  return "search-ready-v1";
});
const speciesLabel = computed(() => queryAnimalLabel());
function lensProjectionFor(p: PlaceSummary) {
  const f = facts.value.get(p.id);
  // The un-lensed Search page answers the access question first. Explicit
  // presence/indoor/dining lenses may promote Reality without changing facts.
  return lensProjection(lensKey.value, f?.answer, f?.reality, f?.snapshot);
}
const preview = ref<{ snapshot: CoexistenceSnapshot | null; loading: boolean; error: string }>({
  snapshot: null,
  loading: false,
  error: "",
});
const selectedPlace = computed(() => results.value.find((p) => p.id === selectedId.value) ?? null);
const FILTERS = [
  { key: "ALLOWED", label: "明确允许" },
  { key: "CONDITIONAL", label: "有条件" },
  { key: "RESTRICTED", label: "明确限制" },
  { key: "UNKNOWN", label: "信息不足" },
  { key: "CONFLICT", label: "来源不一致" },
  { key: "verified", label: "规则已核验" },
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
    if (active.value.includes("verified")) checks.push(Boolean(p.last_verified_at));
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

function rowEvidenceMeta(p: PlaceSummary): string {
  const row = facts.value.get(p.id);
  const safety = statuses.value[p.id] === "UNKNOWN" ? "信息不足不等于允许或禁止" : "";
  const realityMeta = coexistenceEvidenceLine(row?.snapshot, row?.reality);
  if (realityMeta) return [safety, realityMeta].filter(Boolean).join(" · ");

  const rules = row?.snapshot?.evidence_summary.rule_evidence ?? [];
  if (!rules.length) return [safety, "依据待补充"].filter(Boolean).join(" · ");
  const primary = rules[0];
  const issuer = primary ? publicSourceIssuer(primary.source_type, primary.issuer) : "";
  const evidence = issuer ? `${rules.length} 条规则依据 · ${issuer}` : `${rules.length} 条规则依据`;
  return [safety, evidence].filter(Boolean).join(" · ");
}

async function search() {
  // The repository can serve an explicitly stale cached result offline.
  // Blocking all searches before consulting it discards useful last-known facts.
  const query = q.value.trim();
  const n = epoch.begin();
  error.value = "";
  loading.value = true;
  searched.value = true;
  try {
    const list = query ? await searchPlaces(query) : await searchPlaces("");
    if (!epoch.isCurrent(n)) return; // a newer search superseded this one
    const f = await enrichRows(list.items);
    if (!epoch.isCurrent(n)) return; // a newer search superseded this one
    // Publish rows and their Rule/Reality facts together, never a new list
    // alongside the previous query context's stale decision statuses.
    results.value = list.items;
    facts.value = f;
    listStale.value = list.stale;
    listFetchedAtMs.value = list.fetchedAtMs;
    const st: Record<string, StatusKey> = {};
    for (const [id, row] of f) st[id] = answerStatusKey(row.answer);
    statuses.value = st;
    if (query) {
      rememberRecent(query);
      syncRouteQuery(query);
    } else {
      syncRouteQuery("");
    }
    if (isDesktop.value) {
      const firstVisible = visible.value[0] ?? null;
      const selectedStillVisible = visible.value.some((place) => place.id === selectedId.value);
      if (!selectedStillVisible) {
        if (firstVisible) void selectPlace(firstVisible);
        else {
          previewEpoch.begin();
          selectedId.value = null;
          preview.value = { snapshot: null, loading: false, error: "" };
        }
      }
    }
  } catch (e) {
    if (epoch.isCurrent(n)) {
      error.value = online.value
        ? presentDescription(e)
        : "当前离线且没有可用的已缓存搜索结果，请恢复网络后重试。";
    }
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

  const n = previewEpoch.begin();
  preview.value = { snapshot: null, loading: true, error: "" };
  try {
    const { snapshot } = await snapshotFor(p.id);
    if (!previewEpoch.isCurrent(n) || selectedId.value !== p.id) return;
    preview.value = { snapshot, loading: false, error: "" };
  } catch (e) {
    if (!previewEpoch.isCurrent(n) || selectedId.value !== p.id) return;
    preview.value = { snapshot: null, loading: false, error: presentDescription(e) };
  }
}

/** Desktop is a true List–Detail workspace: clicking a result selects it.
 * Mobile keeps normal navigation into the Place dossier. */
function handleResultClick(event: MouseEvent, place: PlaceSummary) {
  if (!isDesktop.value) return;
  event.preventDefault();
  void selectPlace(place);
}

/** Back/forward or an external deep link changes route.query.q → re-run. */
watch(
  () => route.query.q,
  (v) => {
    const next = typeof v === "string" ? v : "";
    if (next === q.value) return;
    // Filter is transient presentation state. A new/deep-linked query starts
    // from its own result state instead of inheriting an open panel from the
    // previous search.
    filterOpen.value = false;
    q.value = next;
    void search();
  },
);

/** M2 §11 — recent searches: local-only, capped, clearable, signed-out safe. */
const SEARCH_RECENT_KEY = "pa.searchRecent.v1";
const MAX_SEARCH_RECENT = 5;
const recent = ref<string[]>([]);

function saveRecent() {
  platformStorage.set(SEARCH_RECENT_KEY, JSON.stringify(recent.value));
}

function rememberRecent(text: string) {
  recent.value = [text, ...recent.value.filter((t) => t !== text)].slice(0, MAX_SEARCH_RECENT);
  saveRecent();
}

function clearRecent() {
  recent.value = [];
  platformStorage.remove(SEARCH_RECENT_KEY);
}

function loadRecent() {
  const raw = platformStorage.get(SEARCH_RECENT_KEY);
  try {
    recent.value = raw ? (JSON.parse(raw) as string[]).slice(0, MAX_SEARCH_RECENT) : [];
  } catch {
    recent.value = [];
    platformStorage.remove(SEARCH_RECENT_KEY);
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

let queryContextReady = false;

onMounted(async () => {
  try {
    await session.restore();
  } catch {
    // Search is public; a broken/stale local session may remove private
    // boundary context but cannot block Rule/Reality lookup.
  }
  loadRecent();
  if (session.signedIn) {
    try {
      boundary.value = (await client.defaultBoundaryProfile()).profile;
    } catch {
      boundary.value = null;
    }
  }
  await search();
  queryContextReady = true;
});

const { desktop: isDesktop, mobile: isMobile } = useBreakpoint();
const selectedId = ref<string | null>(null);
const selectedSceneMedia = usePlaceSceneMedia(computed(() => selectedId.value));

// Desktop List–Detail must never show detail for a row hidden by the active
// filter/lens. Keep selection inside the visible result set.
watch(visible, (list) => {
  if (!isDesktop.value) return;
  if (selectedId.value && list.some((place) => place.id === selectedId.value)) return;

  const next = list[0] ?? null;
  if (next) {
    void selectPlace(next);
    return;
  }

  previewEpoch.begin();
  selectedId.value = null;
  preview.value = { snapshot: null, loading: false, error: "" };
});

watch(currentQueryContext, () => {
  if (!queryContextReady) return;
  void (async () => {
    await search();
    const place = selectedPlace.value;
    if (place && isDesktop.value) await selectPlace(place);
  })();
});
</script>

<template>
  <div
    class="search-workspace"
    data-testid="search-workspace"
    data-ui="search-shell"
    data-ui-page="search"
    :data-ui-state="uiState"
    :data-ui-fixture="uiFixture"
  >
    <QueryContextBar />

    <div class="search-workspace__body" :class="{ 'search-workspace__body--split': isDesktop }">
      <!-- result pane（v0.2.3 §21：ResultsPane x=68 w=400 全出血；§22 内容列不铺满） -->
      <section class="search-result-pane" aria-label="搜索结果" data-ui="search-results-pane">
        <header class="search-result-pane__head">
          <h1 class="visually-hidden">搜索场所的规则与现场</h1>
          <form class="search-field" @submit.prevent="search">
            <input
              v-model="q"
              aria-label="搜索场所"
              placeholder="搜索场所、商圈或地址"
              data-testid="search-input"
              data-ui="search-input"
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
              data-ui="search-submit"
            >
              {{ loading ? "搜索中…" : "搜索" }}
            </button>
          </form>
          <!-- v0.2.4 §11：toolbar 单行「结果数 | 筛选」；不再把搜索/最近搜索/
               lens/筛选/结果数散成 5 层。 -->
          <div class="search-toolbar">
            <span class="search-count" data-testid="search-count" data-ui="search-count">
              <span data-ui-count="result-rows" class="visually-hidden">{{ visible.length }}</span>
              结果 {{ visible.length }}
            </span>
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
        </header>

        <!-- 最近搜索：仅在真实存在时显示（v0.2.4 §11 ≤56px vertical）。 -->
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

        <!-- 筛选面板：desktop inline panel / mobile bottom sheet；单入口不铺 pill。 -->
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
        <!-- empty: v0.2.4 §14 inline，不用 StateMessage 卡片视觉（无 card/shadow）。 -->
        <div
          v-else-if="searched && !visible.length"
          class="search-empty"
          data-ui="search-empty-block"
          data-testid="search-empty"
        >
          <template v-if="active.length">
            <p class="search-empty__title">当前筛选下没有结果</p>
            <p class="muted search-empty__body">清除筛选可查看全部（含信息不足的场所）。</p>
            <button type="button" class="filter-bar__clear" @click="active = []">清除筛选</button>
          </template>
          <template v-else>
            <p class="search-empty__title">没有找到已收录场所</p>
            <p class="muted search-empty__body">
              试试其他关键词，或者到地图查看附近已收录场所。当前贡献流程只接受已收录场所的规则、现场与纠错线索。
            </p>
            <RouterLink class="btn primary" to="/map" data-testid="search-empty-map">
              在地图查找
            </RouterLink>
          </template>
        </div>
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
              :data-ui="selectedId === p.id ? 'search-selected-row' : 'search-result-row'"
              :aria-current="selectedId === p.id ? 'true' : undefined"
            >
              <RouterLink
                :to="{ name: 'place', params: { id: p.id } }"
                class="result-row__link"
                :data-testid="'result-' + p.id"
                @focus="selectPlace(p)"
                @click="handleResultClick($event, p)"
              >
                <!-- Canonical v0.10-R1 search row:
                     identity + rule status / type·distance / primary Reality fact /
                     Rule conclusion + key condition / Evidence·freshness metadata.
                     Keep it divider-led, never a card wall. -->
                <div class="result-row__head">
                  <div class="result-row__identity-wrap">
                    <img
                      v-if="selectedId === p.id && selectedSceneMedia"
                      class="result-row__scene"
                      :src="selectedSceneMedia.url"
                      :alt="`场所场景：${p.canonical_name}`"
                      loading="lazy"
                      decoding="async"
                      referrerpolicy="no-referrer"
                    />
                    <PlaceTypeGlyph v-else :place-type="p.place_type" size="lg" />
                    <div class="result-row__identity">
                      <strong class="result-row__name">{{ p.canonical_name }}</strong>
                      <span class="muted result-row__meta">
                        {{ placeTypeLabel(p.place_type) }}
                        <template v-if="p.distance_m"> · {{ Math.round(p.distance_m) }}m</template>
                      </span>
                    </div>
                  </div>
                  <div class="result-row__head-right">
                    <StatusBadge :semantic="statuses[p.id] ?? 'UNKNOWN'" />
                  </div>
                </div>

                <!-- Default and presence/indoor/dining are Reality-first; only the
                     explicit rules lens promotes Rule. Both layers remain visible. -->
                <p
                  v-if="lensProjectionFor(p).headline === 'rule'"
                  class="result-row__decision result-row__decision--lead"
                  data-testid="row-lens-headline"
                >
                  <template v-if="facts.get(p.id)?.answerError">规则结论暂时无法取得</template>
                  <template v-else-if="facts.get(p.id)?.answer">
                    {{ answerPrimarySummary(facts.get(p.id)?.answer) }}
                    <span v-if="rowCondition(p)" class="result-row__condition">
                      · {{ rowCondition(p) }}
                    </span>
                  </template>
                  <template v-else>信息不足</template>
                </p>
                <p
                  v-else
                  class="result-row__reality-line result-row__reality-line--lead"
                  data-testid="row-lens-headline"
                >
                  {{
                    facts.get(p.id)?.realityError
                      ? "现场信息暂时无法取得"
                      : lensProjectionFor(p).realityLine
                  }}
                </p>

                <!-- Rule stays visible beneath a Reality-first headline. -->
                <p
                  v-if="facts.get(p.id)?.answerError && lensProjectionFor(p).headline !== 'rule'"
                  class="result-row__error"
                  data-testid="row-answer-error"
                >
                  规则结论暂时无法取得 —— 请检查网络后重试。
                </p>
                <p
                  v-else-if="
                    facts.get(p.id)?.answer &&
                    lensProjectionFor(p).headline !== 'rule' &&
                    rowCondition(p)
                  "
                  class="result-row__condition-line"
                  data-testid="row-rule-condition"
                >
                  进入前需满足：{{ rowCondition(p) }}
                </p>

                <!-- Rules lens still keeps Reality visible as the secondary fact. -->
                <p
                  v-if="lensProjectionFor(p).headline === 'rule' && !facts.get(p.id)?.realityError"
                  class="result-row__reality-line"
                  data-testid="result-reality"
                >
                  {{ lensProjectionFor(p).realityLine }}
                </p>
                <p
                  v-if="rowEvidenceMeta(p)"
                  class="result-row__evidence-meta"
                  data-testid="result-evidence-meta"
                >
                  {{ rowEvidenceMeta(p) }}
                </p>
              </RouterLink>
            </li>
          </ul>
        </template>
      </section>

      <!-- detail inspector (desktop only; v0.2.3 §22 content 列 ≤704px) -->
      <aside
        v-if="isDesktop"
        class="search-inspector"
        data-ui="search-detail-pane"
        aria-label="场所详情"
      >
        <DecisionInspector
          data-ui="search-detail-content"
          variant="search"
          :place="selectedPlace"
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
          :latest-verified-at="selectedPlace?.last_verified_at?.slice(0, 10) ?? null"
          :scene-media-url="selectedSceneMedia?.url ?? null"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.search-workspace {
  min-height: 100%;
  min-width: 0;
  max-width: 100%;
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
  /* v0.2.3 §21.1：Rail 68 / Topbar 60 / Results 400（x=68, 全出血）/
   * Detail 余下（x=468 w=972）。禁用居中 max-width：结果窗格必须贴住
   * rail（Content Shell 已 margin-left 68），detail 自适应到右侧边缘。 */
  .search-workspace__body--split {
    flex-direction: row;
    align-items: stretch;
    width: 100%;
    min-width: 0;
    max-width: none;
    margin: 0;
    padding: 0;
    gap: 0;
  }

  .search-result-pane {
    flex: 0 0 var(--pa-layout-result-pane);
    min-width: 0;
    border-right: var(--pa-border-width) solid var(--pa-color-border);
    background: var(--pa-color-surface-raised);
    /* Results remain a pane, not a card: the surface tint only separates
       task selection from the decision workspace. */
    padding: var(--pa-space-5) var(--pa-space-20) 0;
  }

  .search-inspector {
    flex: 1 1 auto;
    min-width: 0;
    /* §22：detail content x = 468 + 40 = 508；宽度由 DecisionInspector
     * 自身 max-width（--pa-layout-detail-content = 704）约束。 */
    padding: var(--pa-space-6) var(--pa-space-6) 0 var(--pa-space-40);
    position: sticky;
    top: 0;
    align-self: stretch;
  }
}

@media (min-width: 768px) and (max-width: 1099px) {
  /* Responsive contract: tablet is compact list-detail, not a squeezed
     desktop canvas. Grid minmax(0, 1fr) removes intrinsic-width overflow. */
  .search-workspace__body--split {
    display: grid;
    grid-template-columns: minmax(280px, 42%) minmax(0, 1fr);
  }

  .search-result-pane {
    width: auto;
    padding-left: var(--pa-space-4);
    padding-right: var(--pa-space-4);
  }

  .search-inspector {
    width: auto;
    min-width: 0;
    max-width: 100%;
    padding: var(--pa-space-5) var(--pa-space-4) 0 var(--pa-space-4);
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
  min-height: 46px;
  margin: 0;
  border-color: var(--pa-color-border-strong);
  background: var(--pa-color-surface);
}

.search-submit {
  flex-shrink: 0;
  min-height: 46px;
  padding-inline: var(--pa-space-4);
  font-weight: var(--pa-font-weight-600);
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

.search-empty {
  /* v0.2.4 §14：inline empty，不放大卡/大圆角/阴影。 */
  margin-top: var(--pa-space-4);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--pa-space-2);
}

.search-empty__title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}

.search-empty__body {
  margin: 0;
  line-height: var(--pa-line-height-base);
}

.search-freshness {
  margin: var(--pa-space-2) 0;
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

/* v0.2.4 §11：toolbar 单行 —— 结果数（muted）| 筛选（text button）。 */
.search-toolbar {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-2);
  padding-bottom: var(--pa-space-2);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.search-toolbar .search-count {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}

.search-toolbar .filter-toggle {
  margin-left: auto;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  margin: var(--pa-space-2) 0;
}

.filter-toggle {
  border: none;
  border-radius: var(--pa-radius-control);
  background: transparent;
  color: var(--pa-color-accent);
  padding: var(--pa-space-1) var(--pa-space-2);
  font-size: var(--pa-font-size-md);
  cursor: pointer;
}

.filter-toggle:hover,
.filter-toggle:focus-visible {
  background: var(--pa-color-accent-weak);
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

.search-freshness {
  margin: var(--pa-space-2) 0;
}

/* v0.2.4 §11：result rows = divider rows, NOT cards — radius 0, no shadow,
 * bottom divider, height 92–108（§11 target），paddings ≤14px。 */
.result-row {
  position: relative;
  border-radius: var(--pa-radius-row-zero);
  background: transparent;
  box-shadow: none;
  min-height: 112px;
  max-height: 132px;
  /* §11 divider=yes：每行自带底部 divider，保证任意第一行也满足
   * borderBottomWidth ≥1（oracle 对第一行测量，不能只有第二行有线）。 */
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}

.result-row--selected {
  /* v0.2.5 §17：selected tint 更轻、不发米黄；用 subtle blue。 */
  background: var(--pa-color-accent-weak);
}

.result-row--selected::before {
  content: "";
  position: absolute;
  left: 0;
  top: var(--pa-space-3);
  bottom: var(--pa-space-3);
  width: var(--pa-border-width-strong);
  background: var(--pa-color-accent);
  border-radius: 0;
}

.result-row__link {
  display: block;
  /* v0.2.4 §11 row internal = 12px。 */
  padding: var(--pa-space-3) var(--pa-space-1);
  text-decoration: none;
  color: inherit;
  min-height: 112px;
  box-sizing: border-box;
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

.result-row__identity-wrap {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-3);
  min-width: 0;
}

.result-row__identity {
  min-width: 0;
}

.result-row__scene {
  width: 56px;
  height: 44px;
  flex: 0 0 auto;
  object-fit: cover;
  border-radius: var(--pa-radius-control);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: var(--pa-color-surface-muted);
}

.result-row__head-right {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  flex-shrink: 0;
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

/* Primary decision: the scannable line of the row; condition sits inline.
 * --lead = lens 标题行（v0.2.4 §11：只改强调，不新增行）。 */
.result-row__decision {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-row__decision--lead {
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.result-row__condition {
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-regular);
  color: var(--pa-color-text-secondary);
}

.result-row__condition-line {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-row__reality-line {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-14);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-row__reality-line--lead {
  font-size: var(--pa-font-size-lg);
  line-height: var(--pa-line-height-tight);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.result-row__evidence-meta {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-row__error {
  margin: var(--pa-space-1) 0 0;
  color: var(--pa-color-text-secondary);
}

/* Mobile compression (v0.2.4 §13): row height 88–104，单列，≤4 semantic lines。 */
@media (max-width: 767px) {
  .result-row,
  .result-row__link {
    min-height: 112px;
    max-height: 132px;
  }

  .result-row__link {
    padding: var(--pa-space-2) 0;
  }

  .result-row__name {
    font-size: var(--pa-font-size-xl);
  }

  .result-row__meta {
    font-size: var(--pa-font-size-md);
  }

  .result-row__decision,
  .result-row__reality-line--lead {
    font-size: var(--pa-font-size-xl);
  }
}
</style>
