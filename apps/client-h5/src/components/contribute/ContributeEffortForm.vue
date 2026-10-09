<script setup lang="ts">
import { computed, ref } from "vue";
import ContributionStepShell from "./ContributionStepShell.vue";
import ContributionReview from "./ContributionReview.vue";
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
const emit = defineEmits<{ done: [msg: string]; back: []; reviewing: [value: boolean] }>();

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

const contributionScopeLabel = computed(() => {
  if (!zoneId.value) return "观察范围未能确认具体分区";
  return props.zones.find((item) => item.id === zoneId.value)?.name ?? "分区记录待确认";
});

const reviewing = ref(false);
function setReviewing(value: boolean) {
  reviewing.value = value;
  emit("reviewing", value);
}
const durationLabel = computed(
  () =>
    OBSERVATION_EFFORT_OPTIONS.find((item) => item.key === durationBucket.value)?.label ??
    "尚未选择",
);
const reviewItems = computed(() => [
  { label: "场所", value: props.placeName },
  { label: "观察范围", value: contributionScopeLabel.value },
  {
    label: "观察时间",
    value:
      sourceMode.value === "on_site_now"
        ? "现在（以提交时刻记录）"
        : occurredAt.value || "尚未选择日期",
  },
  { label: "停留时长", value: durationLabel.value },
  { label: "本次事实", value: "这次认真观察，但没有看到动物" },
]);
</script>

<template>
  <ContributionStepShell
    :place-name="placeName"
    :place-zone="contributionScopeLabel"
    :step="reviewing ? 3 : 2"
    :total="4"
    :title="reviewing ? '核对观察覆盖' : '记录这次没看到'"
    :description="
      reviewing
        ? '确认时间、范围与停留时长；这仍只是一条本次观察覆盖记录。'
        : '“没看到”只有和停留时间、观察范围一起记录才有意义；它不会被解释成“这里没有动物”。'
    "
    @back="reviewing ? setReviewing(false) : emit('back')"
  >
    <template v-if="!reviewing">
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
            <input
              id="effort-date"
              v-model="occurredAt"
              type="date"
              :max="new Date().toISOString().slice(0, 10)"
              required
              data-testid="effort-date"
            />
            <p v-if="!occurredAt" class="effort-note">
              请填写你实际停留的日期；未填写时不能提交历史观察。
            </p>
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
    </template>

    <ContributionReview
      v-else
      :items="reviewItems"
      guard="确认提交后只记录本次观察覆盖；它不是动物缺席证明，也不会删除或否定更早的“看到了”记录。"
    />

    <template #primary>
      <button
        v-if="!reviewing"
        class="primary"
        :disabled="!canSubmit"
        data-testid="effort-review-next"
        @click="setReviewing(true)"
      >
        下一步：核对
      </button>
      <button v-else class="primary" :disabled="busy" data-testid="effort-submit" @click="submit">
        {{ busy ? "提交中…" : "确认记录这次观察" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped src="./ContributeEffortForm.css"></style>
