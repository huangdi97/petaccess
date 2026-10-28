<script setup lang="ts">
/**
 * PlaceRealityPane — Place Dossier 现场 view.
 * Reality timeline stays shared; Staff Response is a first-class factual
 * dimension from the same CoexistenceSnapshot, never promoted into policy.
 */
import type { RealityEventView, StaffResponseSummaryItem, Zone } from "@petaccess/client-core";
import RealityEventLog from "../domain/RealityEventLog.vue";
import { staffResponseSummaryLabel } from "../../consumer/labels";

defineProps<{
  events: RealityEventView[];
  staffResponses: StaffResponseSummaryItem[];
  zones: Zone[];
  placeId: string;
  signedIn: boolean;
  busyEventId?: string | null;
  confirmationMessage?: string;
}>();

const emit = defineEmits<{
  confirm: [
    event: RealityEventView,
    type: "still_present" | "facility_still_present" | "facility_removed",
  ];
}>();
</script>

<template>
  <div data-ui="place-reality-view" data-testid="place-reality-view">
    <section class="reality-fact-section" data-ui="place-staff-response">
      <h2 class="reality-fact-section__title">工作人员处理</h2>
      <p v-if="!staffResponses.length" class="muted">暂无经核验的工作人员处理记录。</p>
      <div
        v-for="item in staffResponses"
        :key="item.response_action"
        class="reality-fact-row"
        data-testid="staff-response-summary-row"
      >
        <span>{{
          staffResponseSummaryLabel(item.response_action, item.staff_awareness_state)
        }}</span>
        <strong>× {{ item.count }}</strong>
      </div>
      <p class="reality-fact-section__note muted">
        这里描述被观察到的处理行为，不代表场所正式政策，也不评价工作人员个人。
      </p>
    </section>

    <section class="reality-fact-section" data-ui="place-observation-timeline">
      <h2 class="reality-fact-section__title">现场时间线</h2>
      <RealityEventLog
        :events="events"
        :zones="zones"
        :place-id="placeId"
        :signed-in="signedIn"
        :busy-event-id="busyEventId"
        @confirm="(event, type) => emit('confirm', event, type)"
      >
        <template #empty-action>
          <RouterLink
            v-if="signedIn"
            class="btn-inline"
            :to="{ path: `/contribute/${placeId}`, query: { mode: 'effort' } }"
          >
            记录这次没看到 →
          </RouterLink>
        </template>
      </RealityEventLog>
      <p v-if="confirmationMessage" class="reality-confirmation-message" role="status">
        {{ confirmationMessage }}
      </p>
      <RouterLink
        class="btn-inline reality-full-link"
        :to="`/place/${placeId}/reality`"
        data-testid="place-reality-full-link"
      >
        查看全部现场记录 →
      </RouterLink>
    </section>
  </div>
</template>

<style scoped>
.reality-fact-section {
  margin-bottom: var(--pa-space-6);
}

.reality-fact-section__title {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.reality-fact-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pa-space-4);
  min-height: 48px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  color: var(--pa-color-text-primary);
}

.reality-fact-row strong {
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-600);
}

.reality-fact-section__note {
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

.reality-confirmation-message {
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

.reality-full-link {
  display: inline-flex;
  margin-top: var(--pa-space-3);
}
</style>
