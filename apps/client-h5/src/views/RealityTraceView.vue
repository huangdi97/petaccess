<script setup lang="ts">
/**
 * RealityTraceView — v0.2.4 Reality v4 (§34–36): Timeline-First.
 *
 * The page's FIRST surface is the event log — the summary ledgers that used
 * to sit above the fold (观察到的事实 / 核验姿态) are gone; at most ONE line of
 * metadata (N 条记录 · 最近日期 · M 条待核验) separates the header from the
 * timeline. Timeline rendering is the shared RealityEventLog (§24 reuse).
 * Filter state lives here (§34 筛选：全部 ▾) and constrains the observations
 * passed down. Empty state is inline, not a card.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, type ObservationView, type Zone } from "@petaccess/client-core";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import RealityEventLog from "../components/domain/RealityEventLog.vue";
import { presentDescription } from "../errors";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const observations = ref<ObservationView[]>([]);
const zones = ref<Zone[]>([]);
const loading = ref(true);
const error = ref("");
/** 筛选：全部 / 已核验 / 待核验（§34 筛选：全部 ▾）。 */
const filter = ref<"all" | "verified" | "pending">("all");

function evidenceStateFor(o: ObservationView): "verified" | "pending" | "disputed" | "historical" {
  if (o.dispute_status === "DISPUTED") return "disputed";
  if (o.dispute_status && o.dispute_status !== "NONE") return "pending";
  return "verified";
}

/** §34 one-line metadata（可省但非表格）：N 条记录 · 最近 DATE · M 条待核验。 */
const summaryLine = computed(() => {
  const n = observations.value.length;
  if (!n) return "";
  const latest = [...observations.value].sort((a, b) =>
    b.occurred_at.localeCompare(a.occurred_at),
  )[0];
  const pending = observations.value.filter((o) => evidenceStateFor(o) !== "verified").length;
  const parts = [`${n} 条记录`, `最近 ${latest.occurred_at.slice(0, 10)}`];
  if (pending > 0) parts.push(`${pending} 条待核验`);
  return parts.join(" · ");
});

/** Filter applied before handing off to the shared event log. */
const visibleObservations = computed<ObservationView[]>(() => {
  if (filter.value === "all") return observations.value;
  const wantVerified = filter.value === "verified";
  return observations.value.filter((o) => (evidenceStateFor(o) === "verified") === wantVerified);
});

async function load() {
  if (!placeId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const [obs, zs] = await Promise.all([
      client.observations(placeId.value),
      client.zones(placeId.value),
    ]);
    observations.value = obs;
    zones.value = zs;
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

watch(placeId, () => void load(), { immediate: true });

/** O6 capture-state integrity: ready = observations exist. */
const uiState = computed<string>(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  return observations.value.length > 0 ? "ready" : "empty";
});
const uiFixture = computed<string>(() =>
  uiState.value === "ready"
    ? "reality-ready-v1"
    : uiState.value === "empty"
      ? "reality-empty-v1"
      : "reality-other",
);
</script>

<template>
  <div
    class="reality-workspace"
    data-testid="reality-workspace"
    data-ui-page="reality"
    :data-ui-state="uiState"
    :data-ui-fixture="uiFixture"
  >
    <QueryContextBar />
    <div class="reality-workspace__body">
      <h1 class="visually-hidden">现场轨迹</h1>
      <SkeletonList v-if="loading" :rows="4" />
      <StateMessage v-else-if="error" kind="ERROR" title="未能取得现场轨迹" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>

      <template v-else>
        <!-- v0.2.4 §34：页顶只允许 title + 一句说明 + 筛选；随后就是 Timeline。 -->
        <header class="reality-head" data-testid="trace-summary">
          <h2 class="reality-head__title">现场记录</h2>
          <p class="muted reality-head__intro">这些记录描述现场观察，不代表运营方正式规则。</p>
          <div class="reality-head__meta">
            <label class="visually-hidden" for="reality-filter">筛选现场记录</label>
            <select
              id="reality-filter"
              v-model="filter"
              class="reality-filter"
              data-testid="reality-filter"
              data-ui="reality-filter"
            >
              <option value="all">筛选：全部 ▾</option>
              <option value="verified">筛选：已核验 ▾</option>
              <option value="pending">筛选：待核验 ▾</option>
            </select>
            <span
              v-if="summaryLine"
              class="muted reality-head__summary"
              data-testid="reality-summary"
            >
              {{ summaryLine }}
            </span>
          </div>
        </header>

        <section
          class="reality-timeline"
          data-testid="trace-observations"
          data-ui="reality-timeline"
        >
          <RealityEventLog :observations="visibleObservations" :zones="zones" :place-id="placeId">
            <template #empty-action>
              <RouterLink
                class="btn primary"
                :to="`/place/${placeId}`"
                data-testid="reality-go-enter"
              >
                记录现场情况
              </RouterLink>
            </template>
          </RealityEventLog>
        </section>
      </template>
    </div>
  </div>
</template>

<style scoped>
.reality-workspace {
  min-height: 100%;
}
.reality-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding: var(--pa-space-4);
  max-width: var(--pa-layout-content-820);
  margin: 0 auto;
}
/* §34：头部必须轻 —— title + 一句说明 + 筛选行，timeline 才能进入首屏。 */
.reality-head {
  padding-bottom: var(--pa-space-3);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}
.reality-head__title {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-18);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.reality-head__intro {
  margin: 0;
  line-height: var(--pa-line-height-base);
}
.reality-head__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-2);
}
.reality-filter {
  width: auto;
  min-height: var(--pa-size-control-md);
  margin: 0;
}
.reality-head__summary {
  font-size: var(--pa-font-size-md);
}
</style>
