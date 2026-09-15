<script setup lang="ts">
/**
 * Search — place name / category / nearby, with the spec §2.2 filters.
 *
 * Filters are applied client-side over the search results. Unknown results are
 * NEVER filtered out unless the user explicitly asks for a status; the hint says
 * so, and clearing filters is one tap.
 *
 * Expensive per-place signals (extras, conflict state) are only fetched when the
 * corresponding filter is active, so a plain search stays a single request.
 */
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  client,
  session,
  synthDemoCamera,
  type BoundaryProfile,
  type PlaceSummary,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import FilterChips from "../components/FilterChips.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { useOnline } from "../composables/useOnline";

const router = useRouter();
const { online } = useOnline();
const q = ref("");
const results = ref<PlaceSummary[]>([]);
const statuses = ref<Record<string, string>>({});
const verified = ref<Record<string, boolean>>({});
const hasPetZone = ref<Record<string, boolean>>({});
const serviceDogInfo = ref<Record<string, boolean>>({});
const conflicts = ref<Record<string, boolean>>({});
const boundary = ref<BoundaryProfile | null>(null);
const searched = ref(false);
const loading = ref(false);
const error = ref("");

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
      try {
        const r = await client.evaluate({
          animal: {
            species: session.activePet?.species ?? "dog",
            service_role: session.activePet?.service_role ?? "none",
            weight_kg: session.activePet?.weight_kg ?? null,
          },
          place_id: p.id,
          intended_action: "enter",
        });
        status[p.id] = r.status;
      } catch {
        status[p.id] = "UNKNOWN";
      }
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
      try {
        const eff = await client.effectiveRules(p.id, { animal: "dog" });
        conflict[p.id] = eff.compliance_state === "POTENTIAL_CONFLICT";
      } catch {
        conflict[p.id] = false;
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
  error.value = "";
  loading.value = true;
  searched.value = true;
  try {
    results.value = q.value.trim()
      ? await client.searchPlaces(q.value)
      : await client.nearby(synthDemoCamera().lat, synthDemoCamera().lng, 5000);
    await enrich(results.value);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

async function applyFilters() {
  if (searched.value) await enrich(results.value);
}

onMounted(async () => {
  await session.restore();
  try {
    boundary.value = (await client.defaultBoundaryProfile()).profile;
  } catch {
    boundary.value = null;
  }
  await search();
});
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：搜索需要联网，提交类操作已暂停。</span>
    </div>
    <div class="panel">
      <input
        v-model="q"
        placeholder="搜索场所名称 / 类别 / 附近（留空则查附近）"
        data-testid="search-input"
        @keydown.enter="search"
      />
      <button
        class="primary block"
        style="margin-top: 8px"
        :disabled="loading"
        @click="search"
        data-testid="search-btn"
      >
        {{ loading ? "搜索中…" : "搜索" }}
      </button>
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
        <button class="primary" @click="search">重试</button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="searched && !visible.length"
      kind="PARTIAL"
      :description="
        results.length
          ? '当前筛选下没有结果。清除筛选可查看全部（含信息不足的场所）。'
          : '没有匹配的场所。未收录不代表该场所没有规则。'
      "
    >
      <template #action>
        <button v-if="active.length" class="primary" @click="active = []">清除筛选</button>
      </template>
    </StateMessage>
    <template v-else>
      <div
        v-for="p in visible"
        :key="p.id"
        class="panel"
        :data-testid="'result-' + p.canonical_name"
      >
        <div style="cursor: pointer" @click="router.push({ name: 'place', params: { id: p.id } })">
          <div class="row" style="justify-content: space-between">
            <strong>{{ p.canonical_name }}</strong>
            <StatusBadge :status="statuses[p.id] ?? 'UNKNOWN'" />
          </div>
          <div class="muted">{{ p.place_type }} · {{ p.canonical_address ?? "" }}</div>
          <div class="row" style="margin-top: 6px">
            <span v-if="verified[p.id]" class="tag">已核验</span>
            <span v-if="hasPetZone[p.id]" class="tag">独立携宠区</span>
            <span v-if="serviceDogInfo[p.id]" class="tag">含服务犬信息</span>
            <StatusBadge v-if="conflicts[p.id]" semantic="CONFLICT" />
          </div>
        </div>
      </div>
    </template>
  </AppShell>
</template>
