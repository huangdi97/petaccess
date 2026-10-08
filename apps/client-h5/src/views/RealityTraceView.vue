<script setup lang="ts">
/**
 * RealityTraceView — timeline-first consumer Reality surface.
 *
 * Reads published, human-verified v0.9 Reality events. Legacy
 * ObservationClaim is intentionally not used here: StaffResponse and
 * AnimalFacility are first-class facts beside observed presence, while all
 * remain separate from Rule / OperatorPolicy.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, session, type RealityEventView, type Zone } from "@petaccess/client-core";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import RealityEventLog from "../components/domain/RealityEventLog.vue";
import { presentDescription } from "../errors";
import { useRealityConfirmation } from "../composables/useRealityConfirmation";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const realityConfirmation = useRealityConfirmation(() => placeId.value);

const events = ref<RealityEventView[]>([]);
const zones = ref<Zone[]>([]);
const loading = ref(true);
const error = ref("");
const filter = ref<"all" | "presence" | "staff" | "facility">("all");

const visibleEvents = computed(() => {
  if (filter.value === "all") return events.value;
  const wanted =
    filter.value === "presence"
      ? "observed_presence"
      : filter.value === "staff"
        ? "staff_response"
        : "animal_facility";
  return events.value.filter((event) => event.event_type === wanted);
});

const emptyCopy = computed(() =>
  filter.value === "all"
    ? {
        title: "暂无近期现场记录",
        description: "这并不代表现场没有动物。",
      }
    : {
        title: "当前筛选下没有对应记录",
        description: "可切换到“全部事实”查看其他经核验记录。",
      },
);

const summaryLine = computed(() => {
  if (!events.value.length) return "";
  const latest = [...events.value].sort((a, b) => b.event_at.localeCompare(a.event_at))[0];
  const presence = events.value.filter((event) => event.event_type === "observed_presence").length;
  const staff = events.value.filter((event) => event.event_type === "staff_response").length;
  const facility = events.value.filter((event) => event.event_type === "animal_facility").length;
  const latestLabel =
    latest.time_evidence_state === "publication_time_only"
      ? `最近一条为 ${latest.event_at.slice(0, 10)} 发布的公开内容`
      : `最近现场日期 ${latest.event_at.slice(0, 10)}`;
  const parts = [`${events.value.length} 条经核验事实`, latestLabel];
  if (presence) parts.push(`${presence} 条动物现场`);
  if (staff) parts.push(`${staff} 条工作人员处理`);
  if (facility) parts.push(`${facility} 条设施`);
  return parts.join(" · ");
});

async function load() {
  if (!placeId.value) return;
  loading.value = true;
  error.value = "";
  try {
    const [eventRows, zoneRows] = await Promise.all([
      client.realityEvents(placeId.value),
      client.zones(placeId.value),
    ]);
    events.value = eventRows;
    zones.value = zoneRows;
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

watch(placeId, () => void load(), { immediate: true });

const uiState = computed<string>(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  return events.value.length > 0 ? "ready" : "empty";
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
      <h1 class="visually-hidden">现场记录</h1>
      <SkeletonList v-if="loading" :rows="4" />
      <StateMessage v-else-if="error" kind="ERROR" title="未能取得现场记录" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>

      <template v-else>
        <header class="reality-head" data-testid="trace-summary">
          <h2 class="reality-head__title">现场记录</h2>
          <p class="muted reality-head__intro">
            这里只展示经人工核验的现场事实；工作人员处理与设施记录都不等于正式准入规则。
          </p>
          <div class="reality-head__meta">
            <span
              v-if="summaryLine"
              class="muted reality-head__summary"
              data-testid="reality-summary"
            >
              {{ summaryLine }}
            </span>
            <label class="visually-hidden" for="reality-filter">筛选现场记录</label>
            <select
              id="reality-filter"
              v-model="filter"
              class="reality-filter"
              data-testid="reality-filter"
              data-ui="reality-filter"
            >
              <option value="all">全部事实</option>
              <option value="presence">动物现场</option>
              <option value="staff">工作人员处理</option>
              <option value="facility">动物设施</option>
            </select>
          </div>
        </header>

        <section
          class="reality-timeline"
          data-testid="trace-observations"
          data-ui="reality-timeline"
        >
          <RealityEventLog
            :events="visibleEvents"
            :zones="zones"
            :place-id="placeId"
            :signed-in="session.signedIn"
            :busy-event-id="realityConfirmation.busyEventId.value"
            :empty-title="emptyCopy.title"
            :empty-description="emptyCopy.description"
            @confirm="realityConfirmation.confirm"
          >
            <template v-if="!events.length" #empty-action>
              <RouterLink
                class="btn primary"
                :to="`/contribute/${placeId}`"
                data-testid="reality-go-enter"
              >
                补充现场情况
              </RouterLink>
            </template>
          </RealityEventLog>
          <p
            v-if="realityConfirmation.message.value"
            class="reality-confirmation-message"
            role="status"
          >
            {{ realityConfirmation.message.value }}
          </p>
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
  padding: var(--pa-space-5) var(--pa-space-6) var(--pa-space-7);
  max-width: var(--pa-layout-content-820);
  margin: 0 auto;
}

.reality-head {
  padding-bottom: var(--pa-space-3);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.reality-head__title {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-22);
  font-weight: var(--pa-font-weight-650);
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
  margin-top: var(--pa-space-4);
}

.reality-filter {
  width: auto;
  min-height: var(--pa-size-control-md);
  margin: 0 0 0 auto;
  background: var(--pa-color-surface);
}

.reality-head__summary {
  font-size: var(--pa-font-size-md);
}

.reality-confirmation-message {
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .reality-workspace__body {
    padding: var(--pa-space-4);
  }

  .reality-head__meta {
    align-items: flex-start;
  }

  .reality-filter {
    margin-left: 0;
  }
}
</style>
