<script setup lang="ts">
/** ContributeRealityForm — M7 reality contribution on the parent-flow API (A2). */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { isoAt, realityPayload, reportOrigin } from "./contributeSupport";
import { presentDescription } from "../../errors";
import {
  ANIMAL_FACILITY_LABELS,
  FACILITY_STATE_LABELS,
  OBSERVED_ACTION_LABELS,
  STAFF_ACTION_LABELS,
} from "../../consumer/labels";
import ContributionStepShell from "./ContributionStepShell.vue";
defineOptions({ name: "ContributeRealityForm" });
const props = defineProps<{
  placeId: string;
  placeName: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
  kind: "observed_presence" | "staff_response" | "animal_facility";
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();
const KIND_LABELS: Record<string, string> = {
  observed_presence: "我刚刚看到动物",
  staff_response: "我看到工作人员怎么处理",
  animal_facility: "我发现这里有动物相关设施",
};

const occurredAt = ref(new Date().toISOString().slice(0, 10));
const zone = ref("");
const animal = ref("dog");
const count = ref("");
const action = ref("present");
const staffAction = ref("unknown");
const staffOutcome = ref("");
const facilityType = ref("other");
const facilityOperational = ref("unknown");
const context = ref("");
const effortBucket = ref("lt_10_min");

const EFFORT_LABELS: Record<string, string> = {
  lt_10_min: "不到 10 分钟",
  min_10_30: "10–30 分钟",
  min_30_120: "30 分钟 – 2 小时",
  gt_120_min: "超过 2 小时",
  unknown: "不确定",
};

const OBSERVED_ACTION_KEYS = [
  "present",
  "entered",
  "stayed",
  "dined_near_table",
  "leashed",
  "off_leash",
  "in_carrier",
  "in_stroller",
] as const;

const STAFF_RESPONSE_KEYS = [
  "proactive_accommodation",
  "provide_water",
  "provide_container_or_stroller",
  "direct_to_allowed_zone",
  "remind_leash",
  "require_carrier",
  "request_relocation",
  "request_wait_outside",
  "deny_entry",
  "request_exit",
  "policy_explanation",
  "escalate_to_manager",
  "no_intervention_observed",
  "unknown",
] as const;

const FACILITY_TYPE_KEYS = [
  "outdoor_holding_cage",
  "kennel",
  "tether_point",
  "pet_waiting_area",
  "pet_parking",
  "water_bowl",
  "pet_stroller",
  "carrier_storage",
  "pet_entrance",
  "pet_elevator",
  "dedicated_pet_zone",
  "waste_bag_station",
  "cleaning_station",
  "washing_point",
  "dedicated_pet_tableware",
  "other",
] as const;

const FACILITY_STATE_KEYS = ["active", "temporarily_unavailable", "removed", "unknown"] as const;

const busy = ref(false);
const error = ref("");
const canSubmit = computed(() => props.online && props.signedIn && !busy.value);

async function submit() {
  if (!canSubmit.value || !props.placeId) return;
  error.value = "";
  busy.value = true;
  try {
    const kind = props.kind;
    const at = isoAt(occurredAt.value);
    const { payload, animalScope } = realityPayload(props.kind, {
      animal: animal.value,
      count: count.value,
      action: action.value,
      context: context.value,
      staffAction: staffAction.value,
      staffOutcome: staffOutcome.value,
      facilityType: facilityType.value,
      facilityOperational: facilityOperational.value,
    });
    const res = await client.createRealityReport(props.placeId, {
      report: {
        origin: reportOrigin(occurredAt.value),
        place_id: props.placeId,
        observed_at: at,
        privacy_state: "private",
      },
      candidates: [
        {
          candidate_type: kind,
          zone_id: zone.value || null,
          animal_scope: animalScope,
          observed_at: at,
          payload,
        },
      ],
      effort: {
        place_id: props.placeId,
        duration_bucket: effortBucket.value,
        observed_at: at,
        animal_observed: kind === "observed_presence" ? true : undefined,
      },
      confirmation: null,
      external_content: null,
    });
    const pending = res.moderation_state === "pending" || res.moderation_state === "flagged";
    emit(
      "done",
      pending
        ? "现场情况已提交，进入人工审核队列。AI 不会自动裁定 —— 审核通过后才作为现场事实展示。"
        : "现场情况已提交并记录。审核通过后才会作为现场事实展示。",
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
    :title="KIND_LABELS[kind]"
    description="只回答结构化问题。提交进入人工审核队列，AI 不会自动裁定。"
    @back="emit('back')"
  >
    <!-- §33 question clusters：什么时候 / 在哪里 / 你看到了什么 -->
    <!-- §19 field groups：真实结构化表单包一层 contribution-form 供几何 gate
         测量 group rhythm（When / Where / What 三组，组距 20–28px）。 -->
    <div class="reality-form" data-ui="contribution-form">
      <fieldset class="cluster">
        <legend class="cluster__title">什么时候？</legend>
        <label for="reality-date">日期</label>
        <input v-model="occurredAt" type="date" id="reality-date" data-testid="reality-date" />
        <label for="reality-effort">在场时长</label>
        <select v-model="effortBucket" id="reality-effort" data-testid="reality-effort">
          <option v-for="(label, key) in EFFORT_LABELS" :key="key" :value="key">{{ label }}</option>
        </select>
      </fieldset>

      <fieldset class="cluster">
        <legend class="cluster__title">在哪里？</legend>
        <label for="reality-zone">适用区域</label>
        <select v-model="zone" id="reality-zone">
          <option value="">全场 / 不确定</option>
          <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
        </select>
      </fieldset>

      <fieldset class="cluster">
        <legend class="cluster__title">你看到了什么？</legend>
        <template v-if="kind === 'observed_presence'">
          <label for="reality-animal">动物</label>
          <select v-model="animal" id="reality-animal">
            <option value="dog">犬</option>
            <option value="cat">猫</option>
            <option value="other">其他</option>
          </select>
          <label for="reality-count">大概几只</label>
          <input
            v-model="count"
            type="number"
            min="1"
            placeholder="1"
            id="reality-count"
            data-testid="reality-count"
          />
          <label for="reality-action">在做什么</label>
          <select v-model="action" id="reality-action">
            <option v-for="key in OBSERVED_ACTION_KEYS" :key="key" :value="key">
              {{ OBSERVED_ACTION_LABELS[key] }}
            </option>
          </select>
        </template>

        <template v-else-if="kind === 'staff_response'">
          <label for="reality-staff-action">工作人员做了什么</label>
          <select v-model="staffAction" id="reality-staff-action">
            <option v-for="key in STAFF_RESPONSE_KEYS" :key="key" :value="key">
              {{ STAFF_ACTION_LABELS[key] }}
            </option>
          </select>
          <label for="reality-staff-outcome">结果（可选）</label>
          <input
            v-model="staffOutcome"
            placeholder="一两句话即可，不填也可以"
            id="reality-staff-outcome"
          />
        </template>

        <template v-else>
          <label for="reality-facility-type">设施类型</label>
          <select v-model="facilityType" id="reality-facility-type">
            <option v-for="key in FACILITY_TYPE_KEYS" :key="key" :value="key">
              {{ ANIMAL_FACILITY_LABELS[key] }}
            </option>
          </select>
          <label for="reality-facility-status">状态</label>
          <select v-model="facilityOperational" id="reality-facility-status">
            <option v-for="key in FACILITY_STATE_KEYS" :key="key" :value="key">
              {{ FACILITY_STATE_LABELS[key] }}
            </option>
          </select>
        </template>

        <label for="reality-context">补充（可选）</label>
        <input
          v-model="context"
          id="reality-context"
          data-testid="reality-context"
          placeholder="一两句话即可，不填也可以"
        />
      </fieldset>
    </div>

    <p v-if="error" class="notice" data-testid="reality-error" role="alert">{{ error }}</p>
    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="reality-submit" @click="submit">
        {{ busy ? "提交中…" : "提交现场情况" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped>
.cluster {
  margin: 0 0 var(--pa-space-5);
  padding: 0;
  border: none;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.cluster + .cluster {
  padding-top: var(--pa-space-5);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.cluster__title {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
  margin-bottom: var(--pa-space-2);
}
.cluster label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}
.cluster input,
.cluster select {
  min-height: var(--pa-size-control-md);
  border: var(--pa-border-width) solid var(--pa-color-border-strong);
  border-radius: var(--pa-radius-control);
  padding: var(--pa-space-1) var(--pa-space-2);
  font-size: var(--pa-font-size-base);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
}
</style>
