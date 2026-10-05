<script setup lang="ts">
/**
 * ContributeEffortForm — structured "this visit I did not see an animal" record.
 *
 * A negative observation is only interpretable together with observation
 * effort. The form therefore records time + duration + covered zone and never
 * creates a NO_ANIMAL_PRESENCE claim. When opened from an existing presence
 * event it also links the effort to that fact without rewriting history. The
 * effort stays provenance/coverage data; it is not published as a presence claim.
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { isoAt } from "./contributeSupport";
import { presentDescription } from "../../errors";
import ContributionStepShell from "./ContributionStepShell.vue";

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

type SourceMode = "on_site_now" | "on_site_past";
const sourceMode = ref<SourceMode>("on_site_now");
const occurredAt = ref(new Date().toISOString().slice(0, 10));
const durationBucket = ref("");
const zoneId = ref(props.initialZoneId ?? "");
const busy = ref(false);
const error = ref("");

const EFFORT_OPTIONS = [
  { key: "lt_10_min", label: "不到 10 分钟" },
  { key: "min_10_30", label: "10–30 分钟" },
  { key: "min_30_120", label: "30 分钟 – 2 小时" },
  { key: "gt_120_min", label: "超过 2 小时" },
] as const;

const canSubmit = computed(
  () => props.online && props.signedIn && !busy.value && Boolean(durationBucket.value),
);

async function submit() {
  if (!canSubmit.value) return;
  error.value = "";
  busy.value = true;
  try {
    const observedAt =
      sourceMode.value === "on_site_now" ? new Date().toISOString() : isoAt(occurredAt.value);
    await client.createRealityReport(props.placeId, {
      report: {
        origin: sourceMode.value,
        place_id: props.placeId,
        subject_place_id: props.placeId,
        place_match_state: "exact_place",
        place_match_evidence_types: ["user_confirmation"],
        observed_at: observedAt,
        time_evidence_state:
          sourceMode.value === "on_site_now" ? "live_device_time" : "exact_event_date",
        time_certainty: "exact",
        fact_evidence_state: "first_hand_no_media",
        privacy_state: "private",
      },
      candidates: [],
      effort: {
        place_id: props.placeId,
        duration_bucket: durationBucket.value,
        covered_zone_ids: zoneId.value ? [zoneId.value] : [],
        animal_observed: false,
        observed_at: observedAt,
      },
      confirmation: props.targetClaimId
        ? {
            confirmation_type: "not_seen_now",
            place_id: props.placeId,
            target_claim_id: props.targetClaimId,
            observed_at: observedAt,
          }
        : null,
      external_content: null,
    });
    emit(
      "done",
      "已记录这次现场观察：本次停留没有看到动物。它不会删除较早记录，也不会生成“这里没有动物”的结论。",
    );
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
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
          <option v-for="item in EFFORT_OPTIONS" :key="item.key" :value="item.key">
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
