<script setup lang="ts">
import { computed } from "vue";
import type { RuleView } from "@petaccess/client-core";
import ContributionStepShell from "./ContributionStepShell.vue";
import RuleLeadFields from "./RuleLeadFields.vue";
import RuleTargetPicker from "./RuleTargetPicker.vue";
import RuleEvidenceUpload from "./RuleEvidenceUpload.vue";
import { useRuleLeadContribution } from "../../composables/useRuleLeadContribution";

defineOptions({ name: "ContributeRuleForm" });

const props = defineProps<{
  placeId: string;
  placeName: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const {
  intent,
  effect,
  animalScope,
  zone,
  conditions,
  sourceBasis,
  mediaId,
  ocrText,
  uploading,
  busy,
  error,
  selectedRuleId,
  canSubmit,
  submit,
} = useRuleLeadContribution(props, (message) => emit("done", message));

function applyRuleScope(rule: RuleView | null) {
  if (intent.value !== "still_valid" && intent.value !== "changed") return;
  zone.value = rule?.zone_id ?? "";
}

const contributionScopeLabel = computed(() => {
  if (!zone.value) return "场所整体（未限定分区）";
  return props.zones.find((item) => item.id === zone.value)?.name ?? "分区记录待确认";
});
</script>

<template>
  <ContributionStepShell
    :place-name="placeName"
    :place-zone="contributionScopeLabel"
    :step="2"
    :total="3"
    title="补充规则信息"
    description="可以确认现有规则、报告变化、只提交规则牌证据，或提供新规则线索；所有内容都先进入核验流程。"
    @back="emit('back')"
  >
    <div v-if="error" class="notice" data-testid="rule-error">{{ error }}</div>

    <RuleLeadFields
      v-model:intent="intent"
      v-model:effect="effect"
      v-model:animal-scope="animalScope"
      v-model:zone="zone"
      v-model:conditions="conditions"
      v-model:source-basis="sourceBasis"
      :zones="zones"
    />

    <RuleTargetPicker
      v-if="intent === 'still_valid' || intent === 'changed'"
      v-model="selectedRuleId"
      :place-id="placeId"
      :zones="zones"
      @selected="applyRuleScope"
    />

    <RuleEvidenceUpload
      v-model:media-id="mediaId"
      v-model:ocr-text="ocrText"
      v-model:uploading="uploading"
      :place-id="placeId"
      :required="intent === 'signage'"
      @error="error = $event"
    />

    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="rule-submit" @click="submit">
        {{
          busy
            ? "提交中…"
            : intent === "signage"
              ? "提交规则牌证据"
              : intent === "still_valid"
                ? "提交核验"
                : "提交规则线索"
        }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped src="./ContributeRuleForm.css"></style>
