<script setup lang="ts">
/**
 * Search — place name / category / nearby, with the spec §2.2 filters.
 *
 * Filters are applied client-side over the search results. Unknown results are
 * NEVER filtered out unless the user explicitly asks for a status; the hint
 * says so, and clearing filters is one tap.
 *
 * Expensive per-place signals (extras, conflict state) are only fetched when
 * the corresponding filter is active, so a plain search stays a single request.
 *
 * M2: each result row is ONE RouterLink control (no nested interactive
 * element), and recent searches (localStorage pa.searchRecent.v1) are
 * local-only, capped at 5 and clearable.
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  client,
  placeTypeLabel,
  ruleSummaryLabel,
  session,
  synthDemoCamera,
  type AccessAnswer,
  type BoundaryProfile,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import AppShell from "../components/AppShell.vue";
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
const route = useRoute();
const router = useRouter();
const { online } = useOnline();
const q = ref(typeof route.query.q === "string" ? route.query.q : "");
const results = ref<PlaceSummary[]>([]);
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
const verified = ref<Record<string, boolean>>({});
const hasPetZone = ref<Record<string, boolean>>({});
const serviceDogInfo = ref<Record<string, boolean>>({});
const conflicts = ref<Record<string, boolean>>({});
const boundary = ref<BoundaryProfile | null>(null);
const searched = ref(false);
const loading = ref(false);
const error = ref("");

/** M3 D2 — desktop split preview: which row is previewed, and its snapshot. */
const { desktop: isDesktop } = useBreakpoint();
const selectedId = ref<string | null>(null);
const preview = ref<{
  snapshot: CoexistenceSnapshot | null;
  loading: boolean;
  error: string;
}>({ snapshot: null, loading: false, error: "" });
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
  { key: "pet_zone", label: "有独立携宠区" },
  { key: "service_dog", label: "含服务犬信息" },
];
const active = ref<string[]>([]);

const visible = computed(() =>
  results.value.filter((p) => {
    if (!active.value.length) return true;
    const statusFilters = active.value.filter(
      (k) => !["verified", "pet_zone", "service_dog"].includes(k),
    );
    const checks: boolean[] = [];
    if (statusFilters.length) {
      checks.push(statusFilters.includes(statuses.value[p.id] ?? "UNKNOWN"));
    }
    if (active.value.includes("verified")) checks.push(Boolean(verified.value[p.id]));
    if (active.value.includes("pet_zone")) checks.push(Boolean(hasPetZone.value[p.id]));
    if (active.value.includes("service_dog")) checks.push(Boolean(serviceDogInfo.value[p.id]));
    return checks.every(Boolean);
  }),
);

/**
 * Row rule-material line comes from the shared client-core vocabulary
 * (ruleSummaryLabel), so the list and PlacePreview word it identically (M3 C1).
 */

/**
 * Per-row signals, all read from the **unified answer model**.
 *
 * The status badge and the conflict flag used to come from `/rules/evaluate`
 * plus `effective-rules` — two engines for one row. The answer model returns both
 * (the conclusion and `conflict_state`), so the page renders a decision instead of
 * combining two of them.
 *
 * Two signals are deliberately NOT taken from the answer and are not conclusions
 * either: `verified` is a freshness fact about the row, and `service_dog` is a
 * filter meaning "a service-dog rule is on file" — a listing question, not a
 * verdict. Both stay on the plain rule listing; nothing here interprets them.
 */
async function enrich(list: PlaceSummary[]) {
  const status: Record<string, string> = {};
  const ver: Record<string, boolean> = {};
  const zone: Record<string, boolean> = {};
  const sd: Record<string, boolean> = {};
  const conflict: Record<string, boolean> = {};
  const needExtras = active.value.includes("pet_zone");
  const needRules = active.value.includes("verified") || active.value.includes("service_dog");

  await Promise.all(
    list.map(async (p) => {
      let answer: AccessAnswer | null = null;
      try {
        answer = await client.accessAnswer(p.id, {
          animal: session.activePet?.species ?? "dog",
          service_role: session.activePet?.service_role ?? "none",
          declared_role: session.activePet?.declared_role ?? null,
        });
      } catch {
        // An unreachable answer is information-insufficient: UNKNOWN, never a
        // silent "no rules here".
        answer = null;
      }
      status[p.id] = answerStatusKey(answer);
      conflict[p.id] = Boolean(answer?.conflict_state?.has_conflict);
      if (needRules) {
        try {
          const rules = await client.rules(p.id);
          ver[p.id] = rules.some((r) => Boolean(r.last_verified_at));
          sd[p.id] = rules.some((r) => r.animal_scope === "service_dog");
        } catch {
          ver[p.id] = false;
          sd[p.id] = false;
        }
      }
      if (needExtras) {
        try {
          const ex = await client.placeExtras(p.id);
          zone[p.id] = ex.coexistence.some((c) => c.attribute === "dedicated_pet_zone");
        } catch {
          zone[p.id] = false;
        }
      }
    }),
  );
  statuses.value = status;
  verified.value = ver;
  hasPetZone.value = zone;
  serviceDogInfo.value = sd;
  conflicts.value = conflict;
}

async function search() {
  if (!online.value) {
    error.value = "当前无网络连接，搜索需要联网。";
    return;
  }
  const query = q.value.trim();
  error.value = "";
  loading.value = true;
  searched.value = true;
  try {
    results.value = query
      ? await client.searchPlaces(q.value)
      : await client.nearby(synthDemoCamera().lat, synthDemoCamera().lng, 5000);
    await enrich(results.value);
    if (query) {
      rememberRecent(query);
      syncRouteQuery(query);
    } else {
      syncRouteQuery("");
    }
    // M3 D2: on desktop, preview the first hit so the pane starts populated.
    if (isDesktop.value && results.value.length) {
      const first = results.value[0];
      if (!selectedId.value || !results.value.some((p) => p.id === selectedId.value)) {
        void selectPlace(first);
      }
    }
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

/** M3: keep the URL query in sync with what the user searched (B1/B2). */
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
      snapshot: await client.coexistenceSnapshot(p.id, {
        animal: session.activePet?.species ?? "dog",
        service_role: session.activePet?.service_role ?? "none",
        action: "enter",
      }),
      loading: false,
      error: "",
    };
  } catch (e) {
    preview.value = { snapshot: null, loading: false, error: presentDescription(e) };
  }
}

// Back/forward or an external deep link changes route.query.q → re-run the
// search with that value (B1/B2); the syncRouteQuery guard keeps this from
// looping when it was our own push.
watch(
  () => route.query.q,
  (v) => {
    const next = typeof v === "string" ? v : "";
    if (next === q.value) return;
    q.value = next;
    void search();
  },
);

async function applyFilters() {
  if (searched.value) await enrich(results.value);
}

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

/** Clear the field; re-query (nearby) only when a search already ran. */
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
  // Account-scoped, so a signed-out visitor gets a 401 rather than an empty
  // profile. Only ask when there is an account to ask about.
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
  <AppShell>
    <DesktopContentContainer :mode="isDesktop ? 'split' : 'single-column'">
      <div class="search-pane">
        <!-- The search field is the page's headline action, but a field is not a
           heading: without this, screen-reader users get no page title at all. -->
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

        <!-- Recent searches (M2 §11): local-only, capped, clearable. -->
        <div v-if="recent.length" class="recent-bar" data-testid="search-recent">
          <div class="row" style="justify-content: space-between">
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
          @update:model-value="applyFilters"
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
            <!-- Branch first: two rows of one brand must be separable at a glance,
               otherwise a branch's rules get read as the whole brand's.
               "所属" and not "位于" — the parent may be a brand (分店) or a
               container (商场里的店铺), and only "所属" is true for both. -->
            <div v-if="p.parent_place_name" class="muted" data-testid="result-branch">
              所属 {{ p.parent_place_name }}
            </div>
            <div class="muted" data-testid="result-meta">
              {{ placeTypeLabel(p.place_type) }} ·
              {{ p.canonical_address ?? "地址待补充" }}
            </div>
            <!-- Why a place the user never named came back. -->
            <div v-if="p.matched_alias" class="muted" data-testid="result-alias">
              以「{{ p.matched_alias }}」匹配（曾用名／别称）
            </div>
            <div class="muted" data-testid="result-rules">{{ ruleSummaryLabel(p) }}</div>
            <div class="row" style="margin-top: var(--pa-space-1h)">
              <span v-if="verified[p.id]" class="tag">已核验</span>
              <span v-if="hasPetZone[p.id]" class="tag">独立携宠区</span>
              <span v-if="serviceDogInfo[p.id]" class="tag">含服务犬信息</span>
              <span v-if="p.rule_count === 0" class="tag">尚未收录规则</span>
              <StatusBadge v-if="conflicts[p.id]" semantic="CONFLICT" />
            </div>
          </RouterLink>
        </template>
      </div>

      <!-- M3 D2 — desktop split pane: the previewed place's summary. -->
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
  </AppShell>
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
/* Each result row is a single link control (M2 §9). */
.result-card {
  display: block;
}
.recent-bar {
  margin: 0 0 var(--pa-space-3);
}

/* M3 D2 — split layout: the list pane wraps, the preview sticks to the top. */
.search-pane {
  min-width: 0;
}

.search-preview {
  position: sticky;
  top: var(--pa-space-4);
}
</style>
