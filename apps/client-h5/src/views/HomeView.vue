<script setup lang="ts">
/**
 * Decision Home — the Consumer UX Baseline v1 home screen (goal §9–§12).
 *
 * Product direction (frozen):
 *   • Search-first. The home is NOT the map; the map is its own tab.
 *   • Answer the question "去之前，查清规则" in ~20 seconds.
 *   • Three query perspectives: 看场所规则（默认）/ 携带动物 / 共处偏好.
 *   • UNKNOWN ≠ ALLOWED: places we know nothing about are shown, labelled
 *     「规则待核实」, never hidden and never rendered as permitted.
 *
 * §12 corrections applied here:
 *   1. "已核验" states its exact scope (species · zone), not a vague venue badge.
 *   2. "待核实场所" → 「规则待核实」.
 *   3. Status presentation is neutral — no wall of green.
 *   4. Conditions are phrased 「进入前需满足」.
 *   5. Every answer links to 「为什么？」 (the rule trace).
 *   6. Contribution is a low-priority footer action.
 */
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  client,
  placeTypeLabel,
  session,
  synthDemoCamera,
  type AccessAnswer,
  type PlaceSummary,
} from "@petaccess/client-core";
import { type StatusKey } from "@petaccess/design-tokens";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { ANSWERED_STATUSES, answerConditions, answerScopeLabel, answerStatusKey } from "../answer";
import { useOnline } from "../composables/useOnline";

type Perspective = "rules" | "animal" | "coexist";

interface Card {
  place: PlaceSummary;
  /** Neutral status key from the unified answer model — never a score. */
  status: StatusKey;
  /** §12.1 — the exact scope the verification covers, e.g. 普通犬 · 南侧草坪 */
  scope: string;
  /** §12.4 — 「进入前需满足」 */
  conditions: string[];
}

const RECENT_KEY = "pa.recent.v1";
const MAX_RECENT = 3;

const router = useRouter();
const { online } = useOnline();

const loading = ref(true);
const error = ref("");
const places = ref<PlaceSummary[]>([]);
const cards = ref<Card[]>([]);
const perspective = ref<Perspective>("rules");
const category = ref("");
const query = ref("");
const recent = ref<{ id: string; name: string }[]>([]);

/** §13 — consumer-facing perspective labels; 看场所规则 is the default. */
const PERSPECTIVES: { key: Perspective; label: string }[] = [
  { key: "rules", label: "看场所规则" },
  { key: "animal", label: "携带动物" },
  { key: "coexist", label: "共处偏好" },
];

/** Category chips run over the already-loaded nearby set (no extra requests). */
const CATEGORIES = [
  { key: "", label: "全部" },
  { key: "park", label: "公园" },
  { key: "mall", label: "商场" },
  { key: "cafe", label: "餐饮" },
  { key: "hotel", label: "酒店" },
  { key: "more", label: "更多" },
];
const PRIMARY_TYPES = new Set(["park", "mall", "cafe", "restaurant", "hotel"]);

const speciesLabel = computed(() => {
  const s = session.activePet?.species ?? "dog";
  if (session.activePet?.service_role === "working") return "服务犬";
  return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
});

/** The declared role, when the user's own pet profile pins one (ADR-025). */
const declaredRole = computed<string | null>(() => session.activePet?.declared_role ?? null);

const filtered = computed(() => {
  if (!category.value) return cards.value;
  return cards.value.filter((c) =>
    category.value === "more"
      ? !PRIMARY_TYPES.has(c.place.place_type)
      : c.place.place_type === category.value,
  );
});
/** Places that actually carry a rule we can stand behind. */
const verified = computed(() => filtered.value.filter((c) => ANSWERED_STATUSES.includes(c.status)));
/** §12.2 — known to exist, but we have no rule: 「规则待核实」. */
const pending = computed(() => filtered.value.filter((c) => !ANSWERED_STATUSES.includes(c.status)));

function setPerspective(p: Perspective) {
  perspective.value = p;
  if (p === "coexist") {
    router.push({ name: "boundary" });
    return;
  }
  // §13 — 看场所规则 is the default; 携带动物 asks the same question per animal.
  session.mode = p === "rules" ? "rules_only" : "with_pet";
  void load();
}

function submitSearch() {
  const q = query.value.trim();
  if (!q) return;
  void router.push({ name: "search", query: { q } });
}

function open(id: string) {
  remember(id);
  void router.push({ name: "place", params: { id } });
}

/** §12.5 — every answer can explain itself. */
function why(id: string) {
  void router.push({ name: "match-explain", params: { id } });
}

/** §17 — recent history is local-only, capped, clearable and signed-out safe. */
function remember(id: string) {
  const name = cards.value.find((c) => c.place.id === id)?.place.canonical_name ?? id;
  const next = [{ id, name }, ...recent.value.filter((r) => r.id !== id)].slice(0, MAX_RECENT);
  recent.value = next;
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  } catch {
    /* storage unavailable (private mode): history simply does not persist */
  }
}

function clearRecent() {
  recent.value = [];
  try {
    localStorage.removeItem(RECENT_KEY);
  } catch {
    /* ignore */
  }
}

function loadRecent() {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    recent.value = raw
      ? (JSON.parse(raw) as { id: string; name: string }[]).slice(0, MAX_RECENT)
      : [];
  } catch {
    recent.value = [];
  }
}

const CONDITION_ZH: Record<string, string> = {
  leash_required: "全程牵引",
  muzzle_required: "佩戴嘴套",
  carrier_required: "装载（笼/包）",
  stroller_required: "使用推车",
  no_ground: "不可落地",
  vaccination_required: "免疫证明",
  registration_required: "登记证明",
  reservation_required: "需预约",
};

/**
 * Bounded-concurrency enrichment through the **unified answer model**.
 *
 * Previously this asked two engines (`/rules/evaluate` for the status, then
 * `effective-rules` for scope and conditions) and patched the scope label from a
 * separate zone lookup — three round trips, three chances to disagree, and a page
 * deciding for itself what the scope was. One call now returns the conclusion,
 * the level that actually governs, and the conditions, so the card renders what
 * the server decided instead of re-deriving it (design §10).
 */
async function enrich(list: PlaceSummary[]) {
  const limit = 4;
  const queue = [...list];
  const out: Card[] = new Array(list.length);
  const index = new Map(list.map((p, i) => [p.id, i]));

  const worker = async () => {
    for (;;) {
      const p = queue.shift();
      if (!p) return;
      let answer: AccessAnswer | null = null;
      try {
        answer = await client.accessAnswer(p.id, {
          animal: session.activePet?.species ?? "dog",
          service_role: session.activePet?.service_role ?? "none",
          // ADR-025: declare the role when the profile pins one, so a hearing-dog
          // question does not inherit a guide-dog proviso.
          declared_role: declaredRole.value,
        });
      } catch {
        // A failed lookup is information-insufficient, never a verdict: the
        // status falls through to UNKNOWN, which is exactly "we don't know".
        answer = null;
      }
      out[index.get(p.id)!] = {
        place: p,
        status: answerStatusKey(answer),
        scope: answerScopeLabel(answer, speciesLabel.value),
        conditions: answerConditions(answer, CONDITION_ZH),
      };
    }
  };

  await Promise.all(Array.from({ length: Math.min(limit, list.length) }, worker));
  cards.value = out.filter(Boolean);
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const cam = synthDemoCamera();
    places.value = await client.nearby(cam.lat, cam.lng, 5000);
    await enrich(places.value);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await session.restore();
  loadRecent();
  await load();
});
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：已加载内容仍可查看，提交类操作已暂停。</span>
    </div>

    <!-- coverage header — the map link lives here so it survives an API failure -->
    <div class="row" style="justify-content: space-between">
      <strong data-testid="coverage-area">上海 · 试点</strong>
      <span class="row">
        <RouterLink class="btn-inline" to="/map" data-testid="go-map">看地图 &gt;</RouterLink>
        <RouterLink to="/settings" class="pill" data-testid="coverage-scope">覆盖范围</RouterLink>
      </span>
    </div>

    <h1 data-testid="home-title">去之前，查清规则</h1>

    <!-- §9.1 search-first -->
    <form class="panel" data-testid="home-search" @submit.prevent="submitSearch">
      <label class="muted" for="home-q">搜索场所名、分店或地址</label>
      <input
        id="home-q"
        v-model="query"
        data-testid="home-search-input"
        placeholder="例如：星巴克臻选 / 前滩太古里 / 某路 123 号"
        autocomplete="off"
      />
      <button class="primary" type="submit" style="margin-top: 8px">查询规则</button>
    </form>

    <!-- §13 three perspectives -->
    <div class="row" role="group" aria-label="查询视角" style="margin: 8px 0">
      <button
        v-for="p in PERSPECTIVES"
        :key="p.key"
        class="pill"
        :class="{ active: perspective === p.key }"
        :aria-pressed="perspective === p.key"
        :data-testid="'perspective-' + p.key"
        @click="setPerspective(p.key)"
      >
        {{ p.label }}
      </button>
    </div>

    <!-- §12.2 wording, stated up front — not only once data happens to load. -->
    <p class="notice" data-testid="home-semantics">
      「规则待核实」＝ 尚未核验，<strong>不等于允许或禁止</strong>。已核验的结论会写明范围（动物 ·
      区域），不对整个场所下结论。
    </p>

    <!-- §17 recent — only when there is something to show -->
    <section v-if="recent.length" data-testid="recent-section">
      <div class="row" style="justify-content: space-between">
        <h2>最近查看</h2>
        <button class="pill" data-testid="clear-recent" @click="clearRecent">清空</button>
      </div>
      <p class="muted">打开时重新求值 —— 规则更新后会以最新结果呈现，不复用旧答案。</p>
      <div
        v-for="r in recent"
        :key="r.id"
        class="panel"
        style="cursor: pointer"
        :data-testid="'recent-' + r.id"
        @click="open(r.id)"
      >
        <strong>{{ r.name }}</strong>
      </div>
    </section>

    <!-- categories -->
    <div class="row" role="group" aria-label="类别" style="margin: 8px 0">
      <button
        v-for="c in CATEGORIES"
        :key="c.key"
        class="pill"
        :class="{ active: category === c.key }"
        :aria-pressed="category === c.key"
        :data-testid="'category-' + (c.key || 'all')"
        @click="category = c.key"
      >
        {{ c.label }}
      </button>
    </div>

    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" :description="`未能取得附近场所：${error}`">
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>

    <template v-else>
      <h2>附近已核验</h2>
      <p class="muted">
        已核验 = 有规则依据。核验范围写清楚（动物 · 区域），不写成对整个场所的结论。
      </p>

      <StateMessage
        v-if="!verified.length"
        kind="PARTIAL"
        data-testid="verified-empty"
        description="这一区域暂无已核验场所。可切换类别、看地图，或改用搜索指定场所名。"
      />

      <div
        v-for="c in verified"
        :key="c.place.id"
        class="panel"
        :data-testid="'verified-' + c.place.id"
        style="cursor: pointer"
        @click="open(c.place.id)"
      >
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>{{ c.place.canonical_name }}</strong>
            <div class="muted">{{ placeTypeLabel(c.place.place_type) }}</div>
            <!-- §12.1 exact verified scope -->
            <div class="muted" :data-testid="'scope-' + c.place.id">已核验：{{ c.scope }}</div>
          </div>
          <!-- §12.3 neutral status -->
          <StatusBadge :semantic="c.status" />
        </div>
        <!-- §12.4 conditions -->
        <p v-if="c.conditions.length" class="notice" :data-testid="'conditions-' + c.place.id">
          进入前需满足：{{ c.conditions.join("、") }}
        </p>
        <!-- §12.5 why -->
        <button class="pill" :data-testid="'why-' + c.place.id" @click.stop="why(c.place.id)">
          为什么？
        </button>
      </div>

      <h2>规则待核实</h2>
      <p class="muted">尚未核验 ≠ 允许或禁止。这些场所我们目前没有足够依据下结论。</p>
      <div
        v-for="c in pending"
        :key="c.place.id"
        class="panel"
        :data-testid="'pending-' + c.place.id"
        style="cursor: pointer"
        @click="open(c.place.id)"
      >
        <div class="row" style="justify-content: space-between">
          <div>
            <strong>{{ c.place.canonical_name }}</strong>
            <div class="muted">{{ placeTypeLabel(c.place.place_type) }}</div>
          </div>
          <StatusBadge :semantic="c.status" />
        </div>
      </div>
    </template>

    <!-- §12.6 contribution is deliberately a low-priority footer action, and it
         stays available even when the nearby query fails. -->
    <footer>
      <RouterLink class="btn" to="/contribute" data-testid="contribute-link"
        >拍规则牌 / 现场核验</RouterLink
      >
      <p class="muted">现场记录与官方规则分开保存；AI/OCR 只生成待审候选，不会自动成为规则。</p>
    </footer>
  </AppShell>
</template>
