<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, freshnessLabel, type ObservationView } from "@petaccess/client-core";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import AppShell from "../components/AppShell.vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
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
  <AppShell>
    <DesktopContentContainer mode="single-column">
      <h1 class="visually-hidden">现场轨迹</h1>
      <SkeletonList v-if="loading" :rows="4" />
      <StateMessage v-else-if="error" kind="ERROR" title="未能取得现场轨迹" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>
      <template v-else-if="trace">
        <header class="panel" data-testid="trace-summary">
          <h2>现场轨迹（≠ 规则）</h2>
          <p class="trace-summary__state">{{ trace.summary }}</p>
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
          :class="g.key === 'review' ? 'trace-review' : 'trace-facts'"
          :data-testid="g.testid"
          :aria-label="g.title"
        >
          <h2>{{ g.title }}</h2>
          <div v-for="s in g.sections" :key="s.label" class="trace-section">
            <span class="trace-section__label">{{ s.label }}</span>
            <div class="trace-section__body">
              <p>{{ s.value ?? "暂无" }}</p>
              <p v-if="s.note" class="muted">{{ s.note }}</p>
            </div>
          </div>
        </section>
        <section class="trace-timeline" data-testid="trace-observations">
          <h2>现场记录时间线</h2>
          <div v-for="o in observations" :key="o.id" class="trace-row">
            <div class="trace-row__head">
              <EvidenceStatus :state="evidenceStateFor(o)" />
              <span class="muted">{{ freshnessLabel(o.occurred_at) }}</span>
            </div>
            <p>
              {{ o.animal_scope }} · {{ o.observed_action }}
              <span v-if="o.staff_action" class="muted">（工作人员：{{ o.staff_action }}）</span>
            </p>
            <p v-if="o.note" class="muted">{{ o.note }}</p>
          </div>
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
    </DesktopContentContainer>
  </AppShell>
</template>

<style scoped>
.trace-summary__state {
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-semibold);
  color: var(--pa-color-text-primary);
  margin: var(--pa-space-2) 0;
}
.trace-facts h2,
.trace-review h2,
.trace-timeline h2 {
  font-size: var(--pa-font-size-lg);
  color: var(--pa-color-text-primary);
  margin: var(--pa-space-4) 0 var(--pa-space-2);
}
.trace-review {
  background: var(--pa-color-bg-sunken);
  border-radius: var(--pa-radius-md);
  padding: var(--pa-space-3);
}
.trace-section {
  display: grid;
  grid-template-columns: 6.5rem 1fr;
  gap: var(--pa-space-3);
  align-items: start;
  padding: var(--pa-space-1) 0;
}
.trace-section__label {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}
.trace-section__body p {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}
.trace-row {
  border-bottom: 1px solid var(--pa-color-border-subtle);
  padding: var(--pa-space-2) 0;
}
.trace-row__head {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
}
.trace-row p {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
}
</style>
