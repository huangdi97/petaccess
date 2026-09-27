<script setup lang="ts">
/**
 * Decision Home — M3 深化收口 (V020_M3_CONSUMER_CORE, DESIGN.md).
 *
 * 变更（相对 M2 基线）：
 *   • 移除旧 AppShell 双层包裹（ModeBar/档案 panel 不再作为全页 chrome）；
 *     页面直接处于 ConsumerAppShell 框架内，宠物/视角上下文收敛为页面级一行。
 *   • 数据统一走 Consumer repository（bounded concurrency + cache + 请求 epoch），
 *     每行 facts = 统一 Rule 结论（accessAnswer）+ Reality 摘要（placeReality）；
 *     transport 错误以 answerError/realityError 呈现，绝不伪装成 UNKNOWN/空态。
 *   • 结果行级呈现 Reality 摘要与 Freshness/Evidence 元数据（Rule 之外的第二事实层）。
 *
 * 产品方向（frozen，未变）：search-first；「去之前，查清规则」；UNKNOWN ≠ ALLOWED；
 * 已核验范围写明（动物 · 区域）；贡献为低优先级 footer。
 */
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { placeTypeLabel, session, type PlaceSummary } from "@petaccess/client-core";
import { type IconName, type StatusKey } from "@petaccess/design-tokens";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import PaIcon from "../components/ui/PaIcon.vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import PlaceResultRow from "../components/domain/PlaceResultRow.vue";
import { ANSWERED_STATUSES, answerConditions, answerScopeLabel, answerStatusKey } from "../answer";
import { bootStage } from "../config/bootTrace";
import { presentDescription } from "../errors";
import { createEpoch, enrichRows, nearbyPlaces, type RowFacts } from "../consumer/repository";

type Perspective = "rules" | "animal" | "coexist";

interface Card {
  place: PlaceSummary;
  facts: RowFacts;
  status: StatusKey;
  scope: string;
  conditions: string[];
}

const RECENT_KEY = "pa.recent.v1";
const MAX_RECENT = 3;

const router = useRouter();
const loading = ref(true);
const error = ref("");
const places = ref<PlaceSummary[]>([]);
const cards = ref<Card[]>([]);
const perspective = ref<Perspective>("rules");
const category = ref("");
const query = ref("");
const recent = ref<{ id: string; name: string }[]>([]);
const epoch = createEpoch();

const PERSPECTIVES: { key: Perspective; label: string }[] = [
  { key: "rules", label: "看场所规则" },
  { key: "animal", label: "携带动物" },
  { key: "coexist", label: "共处偏好" },
];

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

const filtered = computed(() => {
  if (!category.value) return cards.value;
  return cards.value.filter((c) =>
    category.value === "more"
      ? !PRIMARY_TYPES.has(c.place.place_type)
      : c.place.place_type === category.value,
  );
});
const verified = computed(() => filtered.value.filter((c) => ANSWERED_STATUSES.includes(c.status)));
const pending = computed(() => filtered.value.filter((c) => !ANSWERED_STATUSES.includes(c.status)));

const HOME_ENTRIES: { key: string; label: string; hint: string; icon: IconName }[] = [
  { key: "presence", label: "现场是否有动物出现", hint: "看近期现场记录", icon: "eye" },
  { key: "indoor", label: "室内空间情况", hint: "商场 · 餐厅 · 场馆室内", icon: "building" },
  { key: "dining", label: "餐饮区域情况", hint: "堂食区 · 户外座位", icon: "map" },
  { key: "rules", label: "完整规则", hint: "场所全部规则与来源", icon: "document" },
];

function setPerspective(p: Perspective) {
  perspective.value = p;
  if (p === "coexist") {
    void router.push({ name: "boundary" });
    return;
  }
  session.mode = p === "rules" ? "rules_only" : "with_pet";
  void load();
}

function submitSearch() {
  const q = query.value.trim();
  if (!q) return;
  void router.push({ name: "search", query: { q } });
}

function goEntry(key: string) {
  void router.push({ name: "search", query: { lens: key } });
}

function open(id: string) {
  remember(id);
  void router.push({ name: "place", params: { id } });
}

function why(id: string) {
  void router.push({ name: "match-explain", params: { id } });
}

function remember(id: string) {
  const name = cards.value.find((c) => c.place.id === id)?.place.canonical_name ?? id;
  recent.value = [{ id, name }, ...recent.value.filter((r) => r.id !== id)].slice(0, MAX_RECENT);
  try {
    localStorage.setItem(RECENT_KEY, JSON.stringify(recent.value));
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

async function load() {
  const n = epoch.begin();
  loading.value = true;
  error.value = "";
  try {
    places.value = await nearbyPlaces();
    const facts = await enrichRows(places.value);
    if (!epoch.isCurrent(n)) return; // a newer load superseded this one
    cards.value = places.value.map((p) => {
      const f = facts.get(p.id) ?? {
        answer: null,
        answerError: true,
        reality: null,
        realityError: true,
      };
      return {
        place: p,
        facts: f,
        status: answerStatusKey(f.answer),
        scope: answerScopeLabel(f.answer, speciesLabel.value),
        conditions: answerConditions(f.answer, CONDITION_ZH),
      };
    });
  } catch (e) {
    if (epoch.isCurrent(n)) error.value = presentDescription(e);
  } finally {
    if (epoch.isCurrent(n)) loading.value = false;
  }
}

onMounted(async () => {
  await session.restore();
  loadRecent();
  await load();
  bootStage("HOME_READY");
});
</script>

<template>
  <DesktopContentContainer mode="wide">
    <div class="page">
      <!-- coverage header — survives an API failure -->
      <div class="home-topline">
        <strong data-testid="coverage-area">上海 · 试点</strong>
        <span class="row home-topline__actions">
          <RouterLink class="btn-inline" to="/map" data-testid="go-map">看地图 &gt;</RouterLink>
          <RouterLink to="/settings" class="pill" data-testid="coverage-scope">覆盖范围</RouterLink>
        </span>
      </div>

      <h1 data-testid="home-title">去之前，先看看这里的规则和现场。</h1>
      <p class="muted home-subtitle" data-testid="home-subtitle">
        了解场所规则，也参考经核验的现场记录。
      </p>

      <!-- search-first -->
      <form class="panel home-search" data-testid="home-search" @submit.prevent="submitSearch">
        <label class="visually-hidden" for="home-q">搜索场所、商圈或地址</label>
        <input
          id="home-q"
          v-model="query"
          data-testid="home-search-input"
          placeholder="搜索场所、商圈或地址"
          autocomplete="off"
        />
        <button class="primary home-search__submit" type="submit">查询</button>
      </form>

      <!-- 视角（单组；类别收敛为结果区上方次级筛选） -->
      <div class="row home-toolbar" role="group" aria-label="查询视角">
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

      <!-- 附近入口（v0.9-R1 §30 lens，保留语义） -->
      <div class="home-entries">
        <button
          v-for="e in HOME_ENTRIES"
          :key="e.key"
          class="entry"
          :data-testid="'entry-' + e.key"
          @click="goEntry(e.key)"
        >
          <PaIcon :name="e.icon" size="lg" class="entry-icon" />
          <span class="entry-label">{{ e.label }}</span>
          <span class="entry-hint">{{ e.hint }}</span>
        </button>
      </div>

      <section v-if="recent.length" data-testid="recent-section">
        <div class="home-section-header">
          <h2 class="home-section-title">最近查看</h2>
          <button class="pill" data-testid="clear-recent" @click="clearRecent">清空</button>
        </div>
        <p class="muted">打开时重新求值 —— 规则更新后会以最新结果呈现，不复用旧答案。</p>
        <div
          v-for="r in recent"
          :key="r.id"
          class="panel home-recent__item"
          :data-testid="'recent-' + r.id"
          @click="open(r.id)"
        >
          <strong>{{ r.name }}</strong>
        </div>
      </section>

      <!-- 类别（次级筛选，不改变结论） -->
      <div class="row home-toolbar" role="group" aria-label="类别">
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
      <StateMessage v-else-if="error" kind="ERROR" title="未能取得附近场所" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>

      <template v-else>
        <StateMessage
          v-if="!places.length"
          kind="EMPTY"
          data-testid="home-empty"
          title="当前还没有已发布的场所数据"
          description="你仍然可以了解 PetAccess 如何区分规则与现场，或者提交第一条线索。"
        >
          <template #action>
            <RouterLink class="primary" to="/map" data-testid="home-empty-map">探索地图</RouterLink>
            <RouterLink class="secondary" to="/contribute" data-testid="home-empty-contribute"
              >贡献线索</RouterLink
            >
          </template>
        </StateMessage>

        <template v-else>
          <h2 class="home-section-title home-section-title--stacked">附近已核验</h2>
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
            class="panel home-card"
            :data-testid="'verified-' + c.place.id"
            @click="open(c.place.id)"
          >
            <PlaceResultRow
              :place="c.place"
              :answer="c.facts.answer"
              :answer-error="c.facts.answerError"
              :reality="c.facts.reality"
              :reality-error="c.facts.realityError"
              :species-label="speciesLabel"
              :conditions-label="CONDITION_ZH"
              class="home-card__row"
            />
            <div class="row home-card__head">
              <div class="muted" :data-testid="'scope-' + c.place.id">已核验：{{ c.scope }}</div>
              <StatusBadge :semantic="c.status" />
            </div>
            <p v-if="c.conditions.length" class="notice" :data-testid="'conditions-' + c.place.id">
              进入前需满足：{{ c.conditions.join("、") }}
            </p>
            <button class="pill" :data-testid="'why-' + c.place.id" @click.stop="why(c.place.id)">
              为什么？
            </button>
          </div>

          <h2 class="home-section-title home-section-title--stacked">规则待核实</h2>
          <p class="muted">尚未核验 ≠ 允许或禁止。这些场所我们目前没有足够依据下结论。</p>
          <div
            v-for="c in pending"
            :key="c.place.id"
            class="panel home-card"
            :data-testid="'pending-' + c.place.id"
            @click="open(c.place.id)"
          >
            <div class="row home-card__head">
              <div class="home-card__main">
                <strong>{{ c.place.canonical_name }}</strong>
                <div class="muted">{{ placeTypeLabel(c.place.place_type) }}</div>
              </div>
              <StatusBadge :semantic="c.status" />
            </div>
          </div>
        </template>
      </template>

      <p class="notice home-semantics" data-testid="home-semantics">
        「规则待核实」＝ 尚未核验，<strong>不等于允许或禁止</strong>。已核验的结论会写明范围（动物 ·
        区域），不对整个场所下结论。
      </p>

      <footer class="home-footer">
        <RouterLink class="btn" to="/contribute" data-testid="contribute-link"
          >拍规则牌 / 现场核验</RouterLink
        >
        <p class="muted">现场记录与官方规则分开保存；AI/OCR 只生成待审候选，不会自动成为规则。</p>
      </footer>
    </div>
  </DesktopContentContainer>
</template>

<style scoped>
.home-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-2);
  margin-bottom: var(--pa-space-4);
}

.home-subtitle {
  margin: var(--pa-space-1) 0 var(--pa-space-4);
}

.home-search {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-bottom: var(--pa-space-5);
}

.home-entries {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--pa-space-2);
  margin: var(--pa-space-2) 0 var(--pa-space-4);
}

.entry {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  align-items: flex-start;
  padding: var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
  cursor: pointer;
  text-align: left;
  font: inherit;
}

.entry:hover {
  border-color: var(--pa-color-accent);
}

.entry-icon {
  color: var(--pa-color-accent);
  margin-bottom: var(--pa-space-1);
}

.entry-label {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.entry-hint {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.home-toolbar {
  margin: var(--pa-space-1) 0 var(--pa-space-4);
}

.home-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0;
}

.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.home-section-title--stacked {
  margin: var(--pa-space-5) 0 var(--pa-space-2);
}

.home-recent__item {
  cursor: pointer;
}

.home-card {
  cursor: pointer;
}

.home-card__head {
  justify-content: space-between;
}

.home-card__row {
  margin-bottom: var(--pa-space-2);
}

.home-semantics {
  margin-top: var(--pa-space-5);
}

.home-footer {
  margin-top: var(--pa-space-5);
}

.home-footer p {
  margin-bottom: 0;
}

@media (min-width: 768px) {
  .home-entries {
    grid-template-columns: repeat(4, 1fr);
    gap: var(--pa-space-4);
  }

  .home-search {
    flex-direction: row;
    align-items: center;
  }

  .home-search input {
    flex: 1;
    min-width: 0;
  }

  .home-search__submit {
    flex-shrink: 0;
    margin-top: var(--pa-space-1);
  }
}
</style>
