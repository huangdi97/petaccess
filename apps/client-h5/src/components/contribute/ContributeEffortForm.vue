<script setup lang="ts">
import ContributionStepShell from "./ContributionStepShell.vue";
import {
  OBSERVATION_EFFORT_OPTIONS,
  useObservationEffortContribution,
} from "../../composables/useObservationEffortContribution";

defineOptions({ name: "ContributeEffortForm" });

const props = withDefaults(
  defineProps<{
    placeId: string;
    placeName: string;
    zones: { id: string; name: string }[];
    online: boolean;
    signedIn: boolean;
    targetClaimId?: string | null;
    initialZoneId?: string | null;
  }>(),
  { targetClaimId: null, initialZoneId: null },
);
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const { sourceMode, occurredAt, durationBucket, zoneId, busy, error, canSubmit, submit } =
  useObservationEffortContribution(
    {
      placeId: props.placeId,
      online: props.online,
      signedIn: props.signedIn,
      targetClaimId: props.targetClaimId,
      initialZoneId: props.initialZoneId,
    },
    (message) => emit("done", message),
  );
</script>

<template>
  <ContributionStepShell
    :place-name="placeName"
    :step="2"
    :total="3"
    title="记录这次没看到"
    description="“没看到”只有和停留时间、观察范围一起记录才有意义；它不会被解释成“这里没有动物”。"
    @back="emit('back')"
  >
    <div class="effort-form" data-ui="contribution-form">
      <fieldset class="effort-cluster">
        <legend>什么时候？</legend>
        <label for="effort-source-mode">这次观察</label>
        <select id="effort-source-mode" v-model="sourceMode" data-testid="effort-source-mode">
          <option value="on_site_now">我现在就在这里</option>
          <option value="on_site_past">我之前在这里停留过</option>
        </select>
        <template v-if="sourceMode === 'on_site_past'">
          <label for="effort-date">日期</label>
          <input id="effort-date" v-model="occurredAt" type="date" data-testid="effort-date" />
        </template>
      </fieldset>

      <fieldset class="effort-cluster">
        <legend>观察了多久？</legend>
        <label for="effort-duration">在场时长</label>
        <select id="effort-duration" v-model="durationBucket" data-testid="effort-duration">
          <option value="" disabled>请选择</option>
          <option v-for="item in OBSERVATION_EFFORT_OPTIONS" :key="item.key" :value="item.key">
            {{ item.label }}
          </option>
        </select>
      </fieldset>

      <fieldset class="effort-cluster">
        <legend>观察了哪里？</legend>
        <label for="effort-zone">主要停留区域</label>
        <select id="effort-zone" v-model="zoneId" data-testid="effort-zone">
          <option value="">未能确认具体分区</option>
          <option v-for="zone in zones" :key="zone.id" :value="zone.id">{{ zone.name }}</option>
        </select>
      </fieldset>
    </div>

    <p class="effort-note">
      这是一条观察覆盖信息，不是动物缺席证明。系统会保留较早的“看到了”记录；本次停留作为覆盖信息留存，不会自动进入公开现场事实。
    </p>
    <p v-if="error" class="notice" data-testid="effort-error" role="alert">{{ error }}</p>

    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="effort-submit" @click="submit">
        {{ busy ? "提交中…" : "记录这次观察" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped src="./ContributeEffortForm.css"></style>
