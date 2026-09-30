<script setup lang="ts">
/**
 * RealityTraceView — M5 Reality Trace as a Temporal Event Log (freeze §9).
 *
 * Events are rows on a timeline (TIME → EVENT → LOCATION → EVIDENCE), never
 * cards. Fact and review sections render as a divider-led ledger. The page
 * sits inside ConsumerAppShell, so it carries no AppShell / content wrapper.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, freshnessLabel, type ObservationView } from "@petaccess/client-core";
import { animalScopeLabel, ruleActionLabel, staffActionLabel } from "../consumer/labels";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import EvidenceMeta from "../components/domain/EvidenceMeta.vue";
import EvidenceStatus from "../components/domain/EvidenceStatus.vue";
import { presentDescription } from "../errors";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

interface TraceSection {
  label: string;
  value: string | null;
  note?: string | null;
}
interface Trace {
  summary: string;
  fact_sections: TraceSection[];
  review_sections: TraceSection[];
  evidence_count: number;
}

const trace = ref<Trace | null>(null);
const observations = ref<ObservationView[]>([]);
const loading = ref(true);
const error = ref("");

function evidenceStateFor(o: ObservationView): "verified" | "pending" | "disputed" | "historical" {
  if (o.dispute_status === "DISPUTED") return "disputed";
  if (o.dispute_status && o.dispute_status !== "NONE") return "pending";
  return "verified";
}

/** Location confidence rendered as consumer copy — the raw enum stays off-screen. */
const CONFIDENCE_LABELS: Record<string, string> = {
  confirmed_on_site: "现场确认",
  high: "位置高可信",
  medium: "位置中等可信",
  low: "位置低可信",
  uncertain: "位置不确定",
};

function confidenceLabel(v: string): string {
  return CONFIDENCE_LABELS[v] ?? "位置未记录";
}

/** Render "2026-09-20 10:30" for a timestamp, "2026-09-20" for a bare date. */
function displayTime(iso: string): string {
  return iso.length >= 16 ? `${iso.slice(0, 10)} ${iso.slice(11, 16)}` : iso;
}

/** §38: the 72px time column shows the clock time; the date lives in the
 * date-group header, so the column never wraps. */
function timeOnly(iso: string): string {
  return iso.length >= 16 ? iso.slice(11, 16) : iso.slice(0, 10);
}

const traceGroups = computed(() =>
  trace.value
    ? [
        {
          key: "facts",
          title: "观察到的事实",
          testid: "trace-facts",
          sections: trace.value.fact_sections,
        },
        {
          key: "review",
          title: "核验姿态",
          testid: "trace-review",
          sections: trace.value.review_sections,
        },
      ]
    : [],
);

async function load() {
  if (!placeId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const [t, obs] = await Promise.all([
      client.realityTrace(placeId.value),
      client.observations(placeId.value),
    ]);
    trace.value = t;
    observations.value = obs;
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

watch(placeId, () => void load(), { immediate: true });

/** Segment observations into date groups, newest date first (§38 date groups). */
interface ObservationGroup {
  date: string;
  items: ObservationView[];
}

const observationGroups = computed<ObservationGroup[]>(() => {
  const byDate = new Map<string, ObservationView[]>();
  for (const o of observations.value) {
    const date = o.occurred_at.slice(0, 10);
    const list = byDate.get(date);
    if (list) list.push(o);
    else byDate.set(date, [o]);
  }
  return [...byDate.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([date, items]) => ({ date, items }));
});

/** O6 capture-state integrity (numbered where states differ from the plain id). */
const uiState = computed<string>(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  if (!trace.value) return "unavailable";
  return observations.value.length > 0 ? "ready" : "empty";
});
const uiFixture = computed<string>(() => (uiState.value === "ready" ? "reality-ready-v1" : uiState.value === "empty" ? "reality-empty-v1" : "reality-other"));

</script>

<template>
  <div class="reality-workspace" data-testid="reality-workspace" data-ui-page="reality" :data-ui-state="uiState" :data-ui-fixture="uiFixture">
    <QueryContextBar />
    <div class="reality-workspace__body">
      <h1 class="visually-hidden">现场轨迹</h1>
      <SkeletonList v-if="loading" :rows="4" />
      <StateMessage v-else-if="error" kind="ERROR" title="未能取得现场轨迹" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>
      <template v-else-if="trace">
        <header class="reality-head" data-testid="trace-summary">
          <h2>现场轨迹（≠ 规则）</h2>
          <p class="reality-head__state">{{ trace.summary }}</p>
          <p class="muted">
            现场记录与平台核验姿态分开呈现：事实说明观察到了什么，核验说明平台如何确认。
          </p>
          <EvidenceMeta
            v-if="trace.evidence_count != null"
            :evidence-count="trace.evidence_count"
          />
        </header>

        <section
          v-for="g in traceGroups"
          :key="g.key"
          :class="
            g.key === 'review'
              ? 'reality-ledger reality-ledger--review'
              : 'reality-ledger reality-ledger--facts'
          "
          :data-testid="g.testid"
          :aria-label="g.title"
        >
          <h2 class="reality-ledger__title">{{ g.title }}</h2>
          <div v-for="s in g.sections" :key="s.label" class="surface-row">
            <span class="reality-ledger__label">{{ s.label }}</span>
            <div class="reality-ledger__body">
              <p>{{ s.value ?? "暂无" }}</p>
              <p v-if="s.note" class="muted">{{ s.note }}</p>
            </div>
          </div>
        </section>

        <section
          class="reality-timeline"
          data-testid="trace-observations"
          data-ui="reality-timeline"
        >
          <h2 class="reality-ledger__title">现场记录时间线</h2>
          <div class="timeline" role="list" data-ui="reality-timeline-list">
            <span class="timeline-rail" data-ui="reality-rail" aria-hidden="true"></span>
            <template v-for="g in observationGroups" :key="g.date">
              <div class="timeline-date" data-ui="timeline-date">{{ g.date }}</div>
              <div
                v-for="o in g.items"
                :key="o.id"
                class="trace-row"
                data-ui="reality-event"
              >
                <time class="trace-row__time" data-ui="reality-event-time">{{ displayTime(o.occurred_at) }}</time>
                <span class="trace-row__dot" aria-hidden="true" data-ui="reality-event-marker"></span>
                <div class="trace-row__content">
                  <div class="trace-row__head">
                    <EvidenceStatus :state="evidenceStateFor(o)" />
                  </div>
                  <p class="trace-row__event">
                    {{ animalScopeLabel(o.animal_scope) }} · {{ ruleActionLabel(o.observed_action) }}
                    <span v-if="o.staff_action" class="muted"
                      >（工作人员：{{ staffActionLabel(o.staff_action) }}）</span
                    >
                  </p>
                  <p class="muted trace-row__meta">
                    <span>地点：{{ confidenceLabel(o.place_confidence) }}</span>
                    <span>{{ freshnessLabel(o.occurred_at) }}</span>
                  </p>
                  <p v-if="o.note" class="muted trace-row__note">{{ o.note }}</p>
                </div>
              </div>
            </template>
          </div>
          <StateMessage
            v-if="!observations.length"
            kind="PARTIAL"
            :title="EMPTY_STATE_COPY.REALITY.title"
            :description="EMPTY_STATE_COPY.REALITY.description"
            data-testid="trace-empty"
            data-ui="reality-empty"
          >
            <template #action>
              <button class="primary" @click="load">刷新</button>
              <RouterLink class="btn" :to="`/place/${placeId}`" style="margin-left: 8px"
                >查看场所准入</RouterLink
              >
            </template>
          </StateMessage>
        </section>
      </template>
      <StateMessage
        v-else
        kind="PARTIAL"
        :title="EMPTY_STATE_COPY.REALITY.title"
        :description="EMPTY_STATE_COPY.REALITY.description"
      />
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
.reality-head {
  padding-bottom: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}
.reality-head h2 {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-18);
}
.reality-head__state {
  margin: var(--pa-space-2) 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-semibold);
  color: var(--pa-color-text-primary);
}
.reality-ledger {
  margin: var(--pa-space-4) 0 0;
  padding: var(--pa-space-3);
}
.reality-ledger--facts {
  background: var(--pa-color-surface);
}
.reality-ledger--review {
  background: var(--pa-color-bg-sunken);
}
.reality-ledger__title {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-18);
  color: var(--pa-color-text-primary);
}
.reality-ledger__label {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}
.reality-ledger__body p {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}
/* Timeline — a vertical guide with one dot per event row. */
.timeline {
  position: relative;
  margin: var(--pa-space-2) 0 0;
  padding: 0;
  list-style: none;
}
.timeline-rail {
  /* §38: continuous rail across the whole timeline, centered in the 24px
   * marker column (72px time col + 12px) so time/marker/rail all align. */
  content: "";
  position: absolute;
  left: calc(72px + 11px);
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--pa-color-border-subtle);
  pointer-events: none;
}
.timeline-date {
  /* §38: date group separation >= 28px between groups. */
  margin: 28px 0 20px 0;
  padding-left: calc(72px + 24px);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-semibold);
  color: var(--pa-color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.timeline > .timeline-date:first-child {
  margin-top: 0;
}
.trace-row {
  display: grid;
  grid-template-columns: 72px 24px 1fr;
  gap: 0 var(--pa-space-3);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  padding: 0 0 24px 0;
  margin-bottom: 24px;
  /* §38: events are timeline rows, never cards (no panel/card surface). */
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}
.trace-row:last-child {
  border-bottom: none;
}
.trace-row__time {
  padding-top: 2px;
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
  text-align: left;
  white-space: nowrap;
}
.trace-row__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-accent);
  margin: 6px auto 0;
}
.trace-row__head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  min-height: 22px;
}
.trace-row__event,
.trace-row__note {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}
.trace-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-3);
  margin: var(--pa-space-1) 0 0;
}
</style>
