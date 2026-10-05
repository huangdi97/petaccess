<script setup lang="ts">
/**
 * RealityEventLog — shared timeline of published Reality facts.
 *
 * Consumer truth comes from v0.9 human-verified Reality claims, not the legacy
 * ObservationClaim lane. Presence / staff response / facility remain distinct
 * event types on one temporal rail. Time basis is explicit so a facility's
 * verification date is never presented as an observation time.
 */
import { computed } from "vue";
import type { RealityEventView, Zone } from "@petaccess/client-core";
import { zoneConsumerLine } from "../../consumer/labels";
import {
  realityEventDetail,
  realityEventDisplayDate,
  realityEventDisplayTime,
  realityEventHeadline,
  realityEventTimeBasis,
  realityEventVerification,
} from "../../consumer/realityEvent";

const props = withDefaults(
  defineProps<{
    events: RealityEventView[];
    zones: Zone[];
    placeId: string;
    limit?: number;
    signedIn?: boolean;
    busyEventId?: string | null;
  }>(),
  { limit: 0, signedIn: false, busyEventId: null },
);

const emit = defineEmits<{
  confirm: [
    event: RealityEventView,
    type: "still_present" | "facility_still_present" | "facility_removed",
  ];
}>();

function zoneNameFor(event: RealityEventView): string {
  if (!event.zone_id) return "场所范围";
  const zone = props.zones.find((item) => item.id === event.zone_id);
  return zone ? zoneConsumerLine(zone) : "分区待确认";
}

function effortRoute(event: RealityEventView) {
  return {
    path: `/contribute/${props.placeId}`,
    query: {
      mode: "effort",
      target: event.id,
      ...(event.zone_id ? { zone: event.zone_id } : {}),
    },
  };
}

interface EventGroup {
  date: string;
  items: RealityEventView[];
}

const groups = computed<EventGroup[]>(() => {
  const byDate = new Map<string, RealityEventView[]>();
  for (const event of props.events) {
    const date = realityEventDisplayDate(event);
    const list = byDate.get(date);
    if (list) list.push(event);
    else byDate.set(date, [event]);
  }
  return [...byDate.entries()]
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([date, items]) => ({
      date,
      items: [...items].sort((a, b) => b.event_at.localeCompare(a.event_at)),
    }));
});

const visibleGroups = computed<EventGroup[]>(() => {
  if (!props.limit) return groups.value;
  let left = props.limit;
  const out: EventGroup[] = [];
  for (const group of groups.value) {
    if (left <= 0) break;
    const items = group.items.slice(0, left);
    if (items.length) out.push({ date: group.date, items });
    left -= items.length;
  }
  return out;
});
</script>

<template>
  <div class="reality-event-log" data-ui="reality-event-log">
    <div class="timeline" role="list" data-ui="reality-timeline-list">
      <span class="timeline-rail" data-ui="reality-rail" aria-hidden="true"></span>
      <template v-for="group in visibleGroups" :key="group.date">
        <div class="timeline-date" data-ui="timeline-date">{{ group.date }}</div>
        <div
          v-for="event in group.items"
          :key="event.id"
          class="trace-row"
          role="listitem"
          data-ui="reality-event"
          :data-event-type="event.event_type"
        >
          <time class="trace-row__time" data-ui="reality-event-time">
            {{ realityEventDisplayTime(event) }}
          </time>
          <span class="trace-row__dot" aria-hidden="true" data-ui="reality-event-marker"></span>
          <div class="trace-row__content">
            <p class="trace-row__event" data-testid="event-fact">
              {{ realityEventHeadline(event) }}
            </p>
            <p class="trace-row__location" data-testid="event-location">
              {{ zoneNameFor(event) }}
            </p>
            <p v-if="realityEventDetail(event)" class="trace-row__detail">
              {{ realityEventDetail(event) }}
            </p>
            <div class="trace-row__meta">
              <span class="trace-row__status" data-testid="event-status">
                {{ realityEventVerification(event) }} · {{ realityEventTimeBasis(event) }}
              </span>
              <RouterLink
                v-if="event.evidence_bundle_id"
                class="btn-inline trace-row__evidence"
                :to="`/place/${placeId}/evidence`"
                data-testid="event-evidence-link"
              >
                查看证据 →
              </RouterLink>
            </div>
            <div
              v-if="signedIn && ['observed_presence', 'animal_facility'].includes(event.event_type)"
              class="trace-row__confirm"
              aria-label="补充当前现场确认"
            >
              <template v-if="event.event_type === 'observed_presence'">
                <button
                  type="button"
                  :disabled="busyEventId === event.id"
                  @click="emit('confirm', event, 'still_present')"
                >
                  我现在也看到了
                </button>
                <RouterLink class="trace-row__effort-link" :to="effortRoute(event)">
                  这次没看到
                </RouterLink>
              </template>
              <template v-else>
                <button
                  type="button"
                  :disabled="busyEventId === event.id"
                  @click="emit('confirm', event, 'facility_still_present')"
                >
                  设施还在
                </button>
                <button
                  type="button"
                  :disabled="busyEventId === event.id"
                  @click="emit('confirm', event, 'facility_removed')"
                >
                  设施已撤除
                </button>
              </template>
            </div>
          </div>
        </div>
      </template>
    </div>

    <div
      v-if="!events.length"
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
}

.timeline-rail {
  position: absolute;
  left: calc(72px + 11px);
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--pa-color-border-subtle);
  pointer-events: none;
}

.timeline-date {
  margin: var(--pa-space-28) 0 var(--pa-space-4);
  padding-left: calc(72px + 24px);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-600);
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
  padding: 0 0 var(--pa-space-4);
  margin-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: transparent;
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
  white-space: nowrap;
}

.trace-row__dot {
  width: 11px;
  height: 11px;
  margin: 6px auto 0;
  border: var(--pa-border-width) solid var(--pa-color-accent);
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-surface);
}

.trace-row__content {
  min-width: 0;
}

.trace-row__event {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-primary);
  overflow-wrap: anywhere;
}

.trace-row__location,
.trace-row__detail {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
}

.trace-row__detail {
  color: var(--pa-color-text-primary);
}

.trace-row__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-2);
}

.trace-row__status,
.trace-row__evidence {
  font-size: var(--pa-font-size-sm);
}

.trace-row__status {
  color: var(--pa-color-text-muted);
}

.trace-row__confirm {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-2);
}

.trace-row__confirm button,
.trace-row__effort-link {
  min-height: var(--pa-size-control-sm);
  padding: 0 var(--pa-space-2);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-sm);
  cursor: pointer;
}

.trace-row__effort-link {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}

.trace-row__confirm button:hover,
.trace-row__confirm button:focus-visible,
.trace-row__effort-link:hover,
.trace-row__effort-link:focus-visible {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.trace-row__confirm button:disabled {
  color: var(--pa-color-text-muted);
  cursor: progress;
  text-decoration: none;
}

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
    margin: var(--pa-space-5) 0 var(--pa-space-3);
  }

  .trace-row {
    grid-template-columns: 52px 20px 1fr;
    column-gap: var(--pa-space-2);
    padding-bottom: var(--pa-space-4);
    margin-bottom: var(--pa-space-4);
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
