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
import {
  client,
  session,
  type PublicEvidenceMediaView,
  type RealityEventView,
  type Zone,
} from "@petaccess/client-core";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import RealityEventLog from "../components/domain/RealityEventLog.vue";
import { presentDescription } from "../errors";
import { useRealityConfirmation } from "../composables/useRealityConfirmation";
import { realityEventDisplayDate } from "../consumer/realityEvent";
import { zoneConsumerLine } from "../consumer/labels";
import { createEpoch } from "../consumer/repository";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const realityConfirmation = useRealityConfirmation(() => placeId.value);

const events = ref<RealityEventView[]>([]);
const zones = ref<Zone[]>([]);
const publicMediaByBundle = ref<Map<string, PublicEvidenceMediaView>>(new Map());
const loading = ref(true);
const error = ref("");
const privateSessionReady = ref(false);
const privateSessionNote = ref("");
const filter = ref<"all" | "presence" | "staff" | "facility">("all");
const zoneId = computed(() => (typeof route.query.zone === "string" ? route.query.zone : ""));
const activeZone = computed(() => zones.value.find((zone) => zone.id === zoneId.value));
const scopedEvents = computed(() =>
  zoneId.value ? events.value.filter((event) => event.zone_id === zoneId.value) : events.value,
);

const visibleEvents = computed(() => {
  if (filter.value === "all") return scopedEvents.value;
  const wanted =
    filter.value === "presence"
      ? "observed_presence"
      : filter.value === "staff"
        ? "staff_response"
        : "animal_facility";
  return scopedEvents.value.filter((event) => event.event_type === wanted);
});

const emptyCopy = computed(() =>
  zoneId.value && !activeZone.value
    ? {
        title: "所选区域无法确认",
        description: "当前场所未收录该区域，不能将其他区域的记录归到这里。请返回全部区域重新选择。",
      }
    : filter.value === "all"
      ? {
          title: zoneId.value ? "该区域暂无经核验现场记录" : "暂无近期现场记录",
          description: zoneId.value
            ? "仅显示所选区域的事实。无记录不代表该区域没有动物，可返回全部区域查看。"
            : "这并不代表现场没有动物。",
        }
      : {
          title: "当前筛选下没有对应记录",
          description: "可切换到“全部事实”查看其他经核验记录。",
        },
);

const summaryLine = computed(() => {
  if (!scopedEvents.value.length) return "";
  const latest = [...scopedEvents.value].sort((a, b) => b.event_at.localeCompare(a.event_at))[0];
  const presence = scopedEvents.value.filter(
    (event) => event.event_type === "observed_presence",
  ).length;
  const staff = scopedEvents.value.filter((event) => event.event_type === "staff_response").length;
  const facility = scopedEvents.value.filter(
    (event) => event.event_type === "animal_facility",
  ).length;
  const latestDate = realityEventDisplayDate(latest);
  const latestLabel =
    latest.time_evidence_state === "publication_time_only"
      ? `最近一条为 ${latestDate} 发布的公开内容`
      : `最近现场日期 ${latestDate}`;
  const parts = [`${scopedEvents.value.length} 条经核验事实`, latestLabel];
  if (presence) parts.push(`${presence} 条动物现场`);
  if (staff) parts.push(`${staff} 条工作人员处理`);
  if (facility) parts.push(`${facility} 条设施`);
  return parts.join(" · ");
});

const loadEpoch = createEpoch();

async function restorePrivateSession(epoch: number, id: string) {
  privateSessionReady.value = false;
  privateSessionNote.value = "";
  try {
    await session.restore();
    if (!loadEpoch.isCurrent(epoch) || placeId.value !== id) return;
    if (session.restoreIssue) {
      privateSessionNote.value =
        session.restoreIssue === "auth_invalid"
          ? "登录状态已失效；现场事实仍可公开查看，重新登录后可参与确认。"
          : "账号状态暂不可用；现场事实仍可公开查看，确认操作暂时隐藏。";
      return;
    }
    privateSessionReady.value = session.signedIn;
  } catch {
    if (!loadEpoch.isCurrent(epoch) || placeId.value !== id) return;
    privateSessionNote.value = "账号状态暂不可用；现场事实仍可公开查看，确认操作暂时隐藏。";
  }
}

async function loadPublicMedia(eventRows: RealityEventView[], epoch: number) {
  const bundleIds = [
    ...new Set(
      eventRows.map((event) => event.evidence_bundle_id).filter((id): id is string => Boolean(id)),
    ),
  ].slice(0, 8);
  const rows = await Promise.all(
    bundleIds.map(async (bundleId) => {
      try {
        return [bundleId, await client.publicEvidenceMedia(bundleId)] as const;
      } catch {
        // Public display is fail-closed. Missing permission or media never
        // turns into a placeholder image on the Reality timeline.
        return null;
      }
    }),
  );
  if (!loadEpoch.isCurrent(epoch)) return;
  publicMediaByBundle.value = new Map(rows.filter((row) => row !== null));
}

async function load() {
  const id = placeId.value;
  if (!id) return;
  const epoch = loadEpoch.begin();
  loading.value = true;
  error.value = "";
  events.value = [];
  zones.value = [];
  publicMediaByBundle.value = new Map();
  privateSessionReady.value = false;
  privateSessionNote.value = "";
  const isCurrent = () => loadEpoch.isCurrent(epoch) && placeId.value === id;
  void restorePrivateSession(epoch, id);
  try {
    const [eventRows, zoneRows] = await Promise.all([client.realityEvents(id), client.zones(id)]);
    if (!isCurrent()) return;
    events.value = eventRows;
    zones.value = zoneRows;
    void loadPublicMedia(eventRows, epoch);
  } catch (e) {
    if (isCurrent()) error.value = presentDescription(e);
  } finally {
    if (isCurrent()) loading.value = false;
  }
}

watch(placeId, () => void load(), { immediate: true });

const uiState = computed<string>(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  // A filtered-out timeline is visibly empty, even when the unfiltered
  // location holds other facts. Screenshot states follow what users see.
  return visibleEvents.value.length > 0 ? "ready" : "empty";
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
        <StateMessage
          v-if="privateSessionNote"
          kind="PARTIAL"
          :description="privateSessionNote"
          data-testid="reality-private-session-note"
        />
        <header class="reality-head" data-testid="trace-summary">
          <h2 class="reality-head__title">现场记录</h2>
          <p v-if="zoneId" class="reality-head__zone" data-testid="reality-zone-scope">
            <span
              >{{ activeZone ? zoneConsumerLine(activeZone) : "所选区域未收录" }} · 区域筛选</span
            >
            <RouterLink :to="{ name: 'reality-trace', params: { id: placeId } }">
              查看全部区域 →
            </RouterLink>
          </p>
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
            :public-media-by-bundle="publicMediaByBundle"
            :place-id="placeId"
            :signed-in="privateSessionReady"
            :busy-event-id="realityConfirmation.busyEventId.value"
            :empty-title="emptyCopy.title"
            :empty-description="emptyCopy.description"
            @confirm="realityConfirmation.confirm"
          >
            <template v-if="!scopedEvents.length && (!zoneId || activeZone)" #empty-action>
              <RouterLink
                class="btn primary"
                :to="{
                  name: 'contribute',
                  params: { id: placeId },
                  query: activeZone ? { zone: activeZone.id } : {},
                }"
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
  background: var(--pa-color-surface-muted);
}

.reality-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding: var(--pa-space-5) var(--pa-space-6) var(--pa-space-7);
  max-width: 920px;
  margin: 0 auto;
}

.reality-head {
  padding: var(--pa-space-5);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background: var(--pa-color-surface-raised);
  box-shadow: var(--pa-elevation-1);
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
.reality-head__zone {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
  margin: var(--pa-space-3) 0;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-md);
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
