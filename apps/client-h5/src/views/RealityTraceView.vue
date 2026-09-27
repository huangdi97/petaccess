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
</script>

<template>
  <div class="reality-workspace" data-testid="reality-workspace">
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

        <section class="reality-timeline" data-testid="trace-observations">
          <h2 class="reality-ledger__title">现场记录时间线</h2>
          <ul class="timeline" role="list">
            <li v-for="o in observations" :key="o.id" class="trace-row">
              <span class="trace-row__dot" aria-hidden="true"></span>
              <div class="trace-row__content">
                <div class="trace-row__head">
                  <time class="trace-row__time">{{ displayTime(o.occurred_at) }}</time>
                  <EvidenceStatus :state="evidenceStateFor(o)" />
                </div>
                <p class="trace-row__event">
                  {{ o.animal_scope }} · {{ o.observed_action }}
                  <span v-if="o.staff_action" class="muted"
                    >（工作人员：{{ o.staff_action }}）</span
                  >
                </p>
                <p class="muted trace-row__meta">
                  <span>地点：{{ confidenceLabel(o.place_confidence) }}</span>
                  <span>{{ freshnessLabel(o.occurred_at) }}</span>
                </p>
                <p v-if="o.note" class="muted trace-row__note">{{ o.note }}</p>
              </div>
            </li>
          </ul>
          <StateMessage
            v-if="!observations.length"
            kind="PARTIAL"
            :title="EMPTY_STATE_COPY.REALITY.title"
            :description="EMPTY_STATE_COPY.REALITY.description"
            data-testid="trace-empty"
          />
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
  max-width: var(--pa-layout-content-narrow);
  margin: 0 auto;
}
.reality-head {
  padding-bottom: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}
.reality-head h2 {
  margin: 0 0 var(--pa-space-2);
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
/* Facts and review are distinct ledger surfaces — distinguishable beyond colour */
.reality-ledger--facts {
  background: var(--pa-color-surface);
}
.reality-ledger--review {
  background: var(--pa-color-bg-sunken);
}
.reality-ledger__title {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
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
.timeline::before {
  content: "";
  position: absolute;
  left: 5px;
  top: 8px;
  bottom: 8px;
  width: var(--pa-border-width);
  background: var(--pa-color-border-subtle);
}
.trace-row {
  display: grid;
  grid-template-columns: 14px 1fr;
  gap: var(--pa-space-3);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  padding: var(--pa-space-3) 0;
}
.trace-row:last-child {
  border-bottom: none;
}
.trace-row__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-accent);
  margin: 4px auto 0;
}
.trace-row__head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
}
.trace-row__time {
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
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
