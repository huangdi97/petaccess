<script setup lang="ts">
/**
 * Search — M3 深化收口 (V020_M3_CONSUMER_CORE, DESIGN.md).
 *
 * 变更（相对 M3 基线）：
 *   • 数据统一走 Consumer repository：search/nearby 列表缓存 + 行级
 *     Rule 结论（accessAnswer）+ Reality 摘要（placeReality）经 bounded
 *     concurrency 获取（不再 N×无界 Promise.all）。
 *   • 请求 epoch 保护：慢旧请求不覆盖快新请求（快速输入/深链/back-forward）。
 *   • 结果行：identity → Rule → Reality 摘要 → Freshness/Evidence 元数据 →
 *     仅相关 divergence；关键标签减负（conflict 显式，其余并入 meta）。
 *   • 桌面 split preview（PlacePreview + CoexistenceSnapshot）保留。
 *
 * 既有行为（保留）：?q=/?lens= 深链与回填、back/forward 同步、最近搜索
 * （localStorage, 上限 5, 可清空）、筛选不改变任何结论。
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
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import FilterChips from "../components/FilterChips.vue";
import PlacePreview from "../components/domain/PlacePreview.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import PaIcon from "../components/ui/PaIcon.vue";
import { answerStatusKey } from "../answer";
import { useBreakpoint } from "../composables/useBreakpoint";
import { useOnline } from "../composables/useOnline";
import { presentDescription } from "../errors";
import { evidenceLineFor, realityLineFor } from "../consumer/rowView";
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

/** v0.9-R1 home entry lens (?lens=presence|indoor|dining|rules) — master §30. */
const LENS_HINTS: Record<string, string> = {
  presence: "正按「现场是否有动物出现」查看 —— 结果将优先展示近期有现场记录的场所",
  indoor: "正按「室内空间情况」查看 —— 结果将优先展示含室内区域的场所",
  dining: "正按「餐饮区域情况」查看 —— 结果将优先展示含餐饮区域的场所",
  rules: "正按「完整规则」查看 —— 结果为已收录规则的场所",
};
const lens = computed(() => (route.query.lens as string | undefined) ?? "");
const lensHint = computed(() => LENS_HINTS[lens.value] ?? "");
const statuses = ref<Record<string, string>>({});
const boundary = ref<BoundaryProfile | null>(null);
const searched = ref(false);
const loading = ref(false);
const error = ref("");
const epoch = createEpoch();

/** M3 D2 — desktop split preview. */
const { desktop: isDesktop } = useBreakpoint();
const selectedId = ref<string | null>(null);
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

const visible = computed(() =>
  results.value.filter((p) => {
    if (!active.value.length) return true;
    const statusFilters = active.value.filter((k) => k !== "verified");
    const checks: boolean[] = [];
    if (statusFilters.length) {
      checks.push(statusFilters.includes(statuses.value[p.id] ?? "UNKNOWN"));
    }
    if (active.value.includes("verified")) checks.push(Boolean(p.rule_count > 0));
    return checks.every(Boolean);
  }),
);

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
    results.value = list;
    const f = await enrichRows(list);
    if (!epoch.isCurrent(n)) return; // a newer search superseded this one
    facts.value = f;
    const st: Record<string, string> = {};
    for (const [id, row] of f) st[id] = answerStatusKey(row.answer);
    statuses.value = st;
    if (query) {
      rememberRecent(query);
      syncRouteQuery(query);
    } else {
      syncRouteQuery("");
    }
    if (isDesktop.value && list.length) {
      const first = list[0];
      if (!selectedId.value || !list.some((p) => p.id === selectedId.value)) {
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
    preview.value = { snapshot: await snapshotFor(p.id), loading: false, error: "" };
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
</script>

<template>
  <DesktopContentContainer :mode="isDesktop ? 'split' : 'single-column'">
    <div class="search-pane page">
      <h1 class="visually-hidden">搜索场所规则</h1>

      <div class="panel">
        <div class="search-field">
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
            <PaIcon name="close" size="sm" />
          </button>
        </div>
        <button
          type="button"
          class="primary block"
          style="margin-top: var(--pa-space-2)"
          :disabled="loading"
          @click="search"
          data-testid="search-btn"
        >
          {{ loading ? "搜索中…" : "搜索" }}
        </button>
      </div>

      <div v-if="recent.length" class="recent-bar" data-testid="search-recent">
        <div class="row" style="justify-content: space-between">
          <span class="muted">最近搜索</span>
          <button type="button" class="pill" data-testid="clear-search-recent" @click="clearRecent">
            清除
          </button>
        </div>
        <div class="row">
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

      <div
        v-if="lensHint"
        class="panel muted"
        data-testid="lens-hint"
        style="margin-top: var(--pa-space-2)"
      >
        {{ lensHint }}
      </div>

      <div class="panel">
        <div class="muted">
          {{ session.activePet ? `本次：${session.activePet.display_name}` : "未设置宠物档案" }}
          · {{ boundary ? `共处边界「${boundary.name}」` : "未设置共处边界" }}
        </div>
      </div>

      <FilterChips
        v-model="active"
        :options="FILTERS"
        hint="默认不过滤“信息不足”。筛选只影响显示，不改变任何结论。"
      />

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
            <RouterLink class="btn primary" to="/contribute" data-testid="search-empty-contribute">
              提交场所线索
            </RouterLink>
            <button v-if="active.length" type="button" class="pill" @click="active = []">
              清除筛选
            </button>
          </div>
        </template>
      </StateMessage>
      <template v-else>
        <RouterLink
          v-for="p in visible"
          :key="p.id"
          class="panel result-card"
          :to="{ name: 'place', params: { id: p.id } }"
          :aria-current="selectedId === p.id ? 'true' : undefined"
          :data-testid="'result-' + p.canonical_name"
          @mouseenter="selectPlace(p)"
          @focus="selectPlace(p)"
        >
          <div class="row" style="justify-content: space-between">
            <strong>{{ p.canonical_name }}</strong>
            <StatusBadge :status="statuses[p.id] ?? 'UNKNOWN'" />
          </div>
          <p
            v-if="facts.get(p.id)?.answerError"
            class="result-answer-error"
            data-testid="row-answer-error"
          >
            规则结论暂时无法取得 —— 请检查网络后重试。
          </p>
          <div v-if="p.parent_place_name" class="muted" data-testid="result-branch">
            所属 {{ p.parent_place_name }}
          </div>
          <div class="muted" data-testid="result-meta">
            {{ placeTypeLabel(p.place_type) }} · {{ p.canonical_address ?? "地址待补充" }}
          </div>
          <div v-if="p.matched_alias" class="muted" data-testid="result-alias">
            以「{{ p.matched_alias }}」匹配（曾用名／别称）
          </div>
          <div class="muted" data-testid="result-rules">{{ ruleSummaryLabel(p) }}</div>

          <!-- M3：移动端也可见 Reality 摘要 + Evidence/Freshness 元数据 -->
          <div class="result-reality" data-testid="result-reality">
            <p v-if="facts.get(p.id)?.realityError" class="result-reality__error">
              现场信息暂时无法取得 —— 请检查网络后重试。
            </p>
            <template v-else>
              <p>{{ realityLineFor(facts.get(p.id)?.reality) }}</p>
              <p v-if="evidenceLineFor(facts.get(p.id)?.reality)" class="muted">
                {{ evidenceLineFor(facts.get(p.id)?.reality) }}
              </p>
            </template>
          </div>

          <div v-if="p.rule_count === 0" class="muted result-notes">尚未收录规则</div>
          <StatusBadge
            v-if="facts.get(p.id)?.answer?.conflict_state?.has_conflict"
            semantic="CONFLICT"
          />
        </RouterLink>
      </template>
    </div>

    <PlacePreview
      v-if="isDesktop"
      class="search-preview"
      :place="selectedPlace"
      :status="selectedStatus"
      :snapshot="preview.snapshot"
      :loading="preview.loading"
      :error="preview.error"
    />
  </DesktopContentContainer>
</template>

<style scoped>
/* M2 style constraint: token values only (no hex/rgb/hsl/hard px). */
.search-field {
  position: relative;
}
.search-field input {
  padding-right: var(--pa-size-control-lg);
}
.search-clear {
  position: absolute;
  top: var(--pa-space-1);
  bottom: var(--pa-space-1);
  right: var(--pa-space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-size-control-sm);
  min-height: 0;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--pa-color-text-muted);
  cursor: pointer;
}
.search-clear:hover {
  color: var(--pa-color-text-secondary);
}
.result-card {
  display: block;
}
.recent-bar {
  margin: 0 0 var(--pa-space-3);
}
.search-pane {
  min-width: 0;
}
.result-reality {
  margin-top: var(--pa-space-2);
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
  line-height: var(--pa-line-height-base);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  padding-top: var(--pa-space-2);
}
.result-reality p {
  margin: 0 0 var(--pa-space-1);
}
.result-reality__error {
  color: var(--pa-color-text-secondary);
}
.result-notes {
  margin-top: var(--pa-space-1);
}
.search-preview {
  position: sticky;
  top: var(--pa-space-4);
}
</style>
