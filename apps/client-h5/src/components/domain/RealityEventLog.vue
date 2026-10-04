<script setup lang="ts">
/**
 * RealityEventLog — shared timeline of onsite observation events (§24/§34/§35).
 *
 * Used by the Reality page (timeline-first) AND the Place Dossier Reality view
 * (embedded with optional `limit`). Events are rows on a timeline
 * (TIME → LOCATION → EVENT → STATUS → EVIDENCE), never cards. Zone names are
 * resolved through the zones prop so records read 一层公共区域 instead of a raw
 * enum. Empty state is inline, not a card.
 */
import { computed } from "vue";
import type { ObservationView, Zone } from "@petaccess/client-core";
import {
  animalScopeLabel,
  ruleActionLabel,
  staffActionLabel,
  zoneConsumerLine,
} from "../../consumer/labels";
import PaIcon from "../ui/PaIcon.vue";

const props = withDefaults(
  defineProps<{
    observations: ObservationView[];
    zones: Zone[];
    placeId: string;
    /** 内嵌时限制条数；默认全部。 */
    limit?: number;
  }>(),
  { limit: 0 },
);

function evidenceStateFor(o: ObservationView): "verified" | "pending" | "disputed" | "historical" {
  if (o.dispute_status === "DISPUTED") return "disputed";
  if (o.dispute_status && o.dispute_status !== "NONE") return "pending";
  return "verified";
}

/** §35 status：小号 muted 文本；待核验用 clock icon 标注，不用强 badge。 */
function eventStatusLine(o: ObservationView): string {
  const confirmed =
    o.place_confidence === "confirmed_on_site" || o.place_confidence === "high"
      ? "地点已确认"
      : "地点待核验";
  const timeState = evidenceStateFor(o) === "verified" ? "时间已核验" : "时间待核验";
  return `${confirmed} · ${timeState}`;
}

/** §35：pending 事件单独标记（小号 muted + clock icon）。 */
function isPending(o: ObservationView): boolean {
  return evidenceStateFor(o) !== "verified";
}

function zoneNameFor(o: ObservationView): string | null {
  if (!o.zone_id) return null;
  const z = props.zones.find((z) => z.id === o.zone_id);
  return z ? zoneConsumerLine(z) : null;
}

/** Time column shows clock time; the date lives in the date-group header. */
function timeOnly(iso: string): string {
  return iso.length >= 16 ? iso.slice(11, 16) : iso.slice(0, 10);
}

/** Date groups, newest first. */
interface ObservationGroup {
  date: string;
  items: ObservationView[];
}

const groups = computed<ObservationGroup[]>(() => {
  const byDate = new Map<string, ObservationView[]>();
  for (const o of props.observations) {
    const date = o.occurred_at.slice(0, 10);
    const list = byDate.get(date);
    if (list) list.push(o);
    else byDate.set(date, [o]);
  }
  return [...byDate.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([date, items]) => ({ date, items }));
});
</script>

<template>
  <div class="reality-event-log" data-ui="reality-event-log">
    <div class="timeline" role="list" data-ui="reality-timeline-list">
      <span class="timeline-rail" data-ui="reality-rail" aria-hidden="true"></span>
      <template v-for="g in groups" :key="g.date">
        <div class="timeline-date" data-ui="timeline-date">{{ g.date }}</div>
        <!-- Timeline is a flat list; events are NOT cards. `limit` truncates
             embed views to the latest rows (v0.2.4 §24). -->
        <template v-for="(o, i) in g.items" :key="o.id">
          <div v-if="limit === 0 || i < limit" class="trace-row" data-ui="reality-event">
            <time class="trace-row__time" data-ui="reality-event-time">{{
              timeOnly(o.occurred_at)
            }}</time>
            <span class="trace-row__dot" aria-hidden="true" data-ui="reality-event-marker"></span>
            <div class="trace-row__content">
              <!-- v0.2.7 §24：Observed Fact = primary；Location = secondary；
                   Staff Response 从属于事实；Review metadata = tertiary。 -->
              <p class="trace-row__event" data-testid="event-fact">
                {{ animalScopeLabel(o.animal_scope) }} · {{ ruleActionLabel(o.observed_action) }}
              </p>
              <p class="trace-row__location" data-testid="event-location">
                {{ zoneNameFor(o) ?? "地点待确认" }}
              </p>
              <p v-if="o.staff_action" class="trace-row__staff" data-testid="event-staff-response">
                <span class="trace-row__staff-label">工作人员</span>
                {{ staffActionLabel(o.staff_action) }}
              </p>
              <div class="trace-row__meta">
                <span class="trace-row__status" data-testid="event-status">
                  <PaIcon v-if="isPending(o)" name="clock" size="sm" label="待核验" />
                  {{ eventStatusLine(o) }}
                </span>
                <RouterLink
                  class="btn-inline trace-row__evidence"
                  :to="`/place/${placeId}/evidence`"
                  data-testid="event-evidence-link"
                >
                  查看证据 →
                </RouterLink>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>

    <!-- §36 empty：inline，无大卡。 -->
    <div
      v-if="!observations.length"
      class="reality-empty"
      data-testid="trace-empty"
      data-ui="reality-empty"
    >
      <p class="reality-empty__title">暂无近期现场记录</p>
      <p class="muted">这并不代表现场没有动物。</p>
      <slot name="empty-action" />
    </div>
  </div>
</template>

<style scoped>
.timeline {
  position: relative;
  margin: var(--pa-space-1) 0 0;
  padding: 0;
  list-style: none;
}
.timeline-rail {
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
  margin: var(--pa-space-4) 0 var(--pa-space-2);
  padding-left: calc(72px + 24px);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-semibold);
  color: var(--pa-color-text-secondary);
  letter-spacing: var(--pa-letter-spacing-wide);
}
.timeline > .timeline-date:first-child {
  margin-top: 0;
}
.trace-row {
  display: grid;
  grid-template-columns: 72px 24px 1fr;
  gap: 0 var(--pa-space-3);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  padding: 0 0 var(--pa-space-3) 0;
  margin-bottom: var(--pa-space-3);
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
  font-weight: var(--pa-font-weight-650);
  font-variant-numeric: tabular-nums;
  color: var(--pa-color-text-primary);
  text-align: left;
  white-space: nowrap;
}
.trace-row__dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--pa-color-surface);
  border: var(--pa-border-width) solid var(--pa-color-accent);
  margin: 6px auto 0;
}
.trace-row__content {
  min-width: 0;
}
/* v0.2.7 §24：Observed Fact = 主行（事实优先）；Location = 次要上下文；
   Staff Response = 从属于事实；Review metadata = 第三层。 */
.trace-row__event {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-23);
  overflow-wrap: anywhere;
}
.trace-row__staff {
  display: flex;
  gap: var(--pa-space-2);
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

.trace-row__staff-label {
  color: var(--pa-color-text-muted);
}
.trace-row__location {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}
.trace-row__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-1);
}
.trace-row__status {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}
.trace-row__evidence {
  font-size: var(--pa-font-size-sm);
}

/* inline empty — no card, single action. */
.reality-empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
}
.reality-empty__title {
  margin: 0;
  font-weight: var(--pa-font-weight-600);
}

@media (max-width: 767px) {
  .timeline-rail {
    left: calc(52px + 9px);
  }

  .timeline-date {
    padding-left: calc(52px + 20px);
    margin: var(--pa-space-4) 0 var(--pa-space-2);
  }

  .trace-row {
    grid-template-columns: 52px 20px 1fr;
    column-gap: var(--pa-space-2);
    padding-bottom: var(--pa-space-3);
    margin-bottom: var(--pa-space-3);
  }

  .trace-row__time {
    font-size: var(--pa-font-size-sm);
  }

  .trace-row__event {
    font-size: var(--pa-font-size-base);
  }

  .trace-row__meta {
    gap: var(--pa-space-2);
  }
}
</style>
