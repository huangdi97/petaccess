<script setup lang="ts">
/**
 * ContributeObservationForm — 我有现场经历（结构化，legacy createObservation 路径）。
 * 只记录可观察行为，不记录主观推断；现场记录 ≠ 场所正式政策。
 * v0.2.5 §28–32：统一走 ContributeStepShell。
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { isoAt, proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";
import ContributionStepShell from "./ContributionStepShell.vue";

defineOptions({ name: "ContributeObservationForm" });

const props = defineProps<{
  placeId: string;
  placeName: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const occurredAt = ref(new Date().toISOString().slice(0, 10));
const zone = ref("");
const observedAction = ref("enter");
const staffAction = ref("no_interaction_observed");
const placeConfidence = ref("confirmed_on_site");
const note = ref("");
const busy = ref(false);
const error = ref("");

const canSubmit = computed(() => props.online && props.signedIn && !busy.value);

async function submit() {
  if (!canSubmit.value) return;
  error.value = "";
  busy.value = true;
  try {
    await client.createObservation({
      place_id: props.placeId,
      zone_id: zone.value || null,
      occurred_at: isoAt(occurredAt.value),
      occurred_precision: "same_day",
      animal_scope: "dog",
      observed_action: observedAction.value,
      staff_action: staffAction.value,
      place_confidence: placeConfidence.value,
      note: note.value.trim() || null,
      evidence_refs: null,
      ...proximity(),
    });
    emit("done", "现场记录已提交。现场记录与场所正式政策分开呈现，不会互相混同。");
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
    :step="1"
    :total="3"
    title="我有现场经历"
    description="只记录可观察到的行为，不记录主观推断。现场记录不代表场所正式政策。"
    @back="emit('back')"
  >
    <div v-if="error" class="notice" data-testid="exp-error">{{ error }}</div>

    <label for="exp-date">日期</label>
    <input v-model="occurredAt" type="date" id="exp-date" data-testid="exp-date" />

    <label for="exp-zone">适用区域</label>
    <select v-model="zone" id="exp-zone">
      <option value="">全场 / 不确定</option>
      <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
    </select>

    <label for="exp-action">当时发生了什么</label>
    <select v-model="observedAction" id="exp-action" data-testid="exp-action">
      <option value="enter">进入</option>
      <option value="dine">就餐</option>
      <option value="walk">通行</option>
      <option value="stay">停留</option>
    </select>

    <label for="exp-staff">工作人员的反应</label>
    <select v-model="staffAction" id="exp-staff" data-testid="exp-staff">
      <option value="no_interaction_observed">未见工作人员介入</option>
      <option value="explicitly_allowed">明确允许</option>
      <option value="explicitly_refused">明确拒绝</option>
      <option value="asked_to_remove">被要求离开</option>
      <option value="interaction_unknown">不确定</option>
    </select>

    <label for="exp-confidence">你对在场情况的确认程度</label>
    <select v-model="placeConfidence" id="exp-confidence" data-testid="exp-confidence">
      <option value="confirmed_on_site">我在现场确认</option>
      <option value="high">高</option>
      <option value="medium">中</option>
      <option value="low">低</option>
      <option value="uncertain">不确定</option>
    </select>

    <label for="exp-note">结构化补充（非评论区）</label>
    <input
      v-model="note"
      id="exp-note"
      maxlength="500"
      placeholder="如：工作日下午，未见工作人员介入"
    />

    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="exp-submit" @click="submit">
        {{ busy ? "提交中…" : "提交现场记录" }}
      </button>
    </template>
  </ContributionStepShell>
</template>