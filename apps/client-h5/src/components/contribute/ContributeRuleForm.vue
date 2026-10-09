<script setup lang="ts">
import { computed, ref } from "vue";
import type { RuleView } from "@petaccess/client-core";
import ContributionStepShell from "./ContributionStepShell.vue";
import ContributionReview from "./ContributionReview.vue";
import {
  ruleLeadConditionLabel,
  ruleLeadEffectLabel,
  ruleLeadSourceBasisLabel,
} from "./ruleLeadCopy";
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

const reviewing = ref(false);
const INTENT_LABELS: Record<string, string> = {
  still_valid: "确认已收录规则仍然有效",
  changed: "报告已收录规则发生变化",
  signage: "提交规则牌 / 公告证据",
  new_lead: "提交新规则线索",
};
const ANIMAL_LABELS: Record<string, string> = {
  ordinary_pet: "普通宠物",
  dog: "犬",
  cat: "猫",
  other: "其他动物",
};
const reviewItems = computed(() => {
  const items = [
    { label: "场所", value: props.placeName },
    { label: "规则动作", value: INTENT_LABELS[intent.value] ?? "规则线索" },
    { label: "适用范围", value: contributionScopeLabel.value },
  ];
  if (intent.value === "changed" || intent.value === "new_lead") {
    items.push(
      { label: "准入结论", value: ruleLeadEffectLabel(effect.value) || "待选择" },
      { label: "适用动物", value: ANIMAL_LABELS[animalScope.value] ?? animalScope.value },
      { label: "来源方式", value: ruleLeadSourceBasisLabel(sourceBasis.value) || "待选择" },
      { label: "已知条件", value: ruleLeadConditionLabel(conditions.value) },
    );
  } else if (intent.value === "still_valid") {
    items.push({ label: "目标规则", value: selectedRuleId.value ? "已选择具体规则" : "尚未选择" });
  } else if (intent.value === "signage") {
    items.push({ label: "规则牌证据", value: mediaId.value ? "已附私有核验图片" : "尚未上传" });
  }
  return items;
});
</script>

<template>
  <ContributionStepShell
    :place-name="placeName"
    :place-zone="contributionScopeLabel"
    :step="reviewing ? 3 : 2"
    :total="4"
    :title="reviewing ? '核对规则线索' : '补充规则信息'"
    :description="
      reviewing
        ? '确认这些结构化信息就是你准备提交的规则线索或核验记录。'
        : '可以确认现有规则、报告变化、只提交规则牌证据，或提供新规则线索；所有内容都先进入核验流程。'
    "
    @back="reviewing ? (reviewing = false) : emit('back')"
  >
    <div v-if="error" class="notice" data-testid="rule-error">{{ error }}</div>

    <template v-if="!reviewing">
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
    </template>

    <ContributionReview
      v-else
      :items="reviewItems"
      guard="确认提交后内容只进入规则线索 / 核验流程；工作人员说明、照片或 OCR 都不会自动升级为正式运营方政策。"
    />

    <template #primary>
      <button
        v-if="!reviewing"
        class="primary"
        :disabled="!canSubmit"
        data-testid="rule-review-next"
        @click="reviewing = true"
      >
        下一步：核对
      </button>
      <button v-else class="primary" :disabled="busy" data-testid="rule-submit" @click="submit">
        {{
          busy
            ? "提交中…"
            : intent === "signage"
              ? "确认提交规则牌证据"
              : intent === "still_valid"
                ? "确认提交核验"
                : "确认提交规则线索"
        }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped src="./ContributeRuleForm.css"></style>
