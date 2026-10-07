<script setup lang="ts">
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { evidenceRefs, proximity } from "./contributeSupport";
import {
  ruleLeadConditionLabel,
  ruleLeadEffectLabel,
  ruleLeadSourceBasisLabel,
} from "./ruleLeadCopy";
import { presentDescription } from "../../errors";
import ContributionStepShell from "./ContributionStepShell.vue";
import RuleLeadFields from "./RuleLeadFields.vue";
import RuleTargetPicker from "./RuleTargetPicker.vue";
import RuleEvidenceUpload from "./RuleEvidenceUpload.vue";

defineOptions({ name: "ContributeRuleForm" });

const props = defineProps<{
  placeId: string;
  placeName: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

type RuleIntent = "still_valid" | "changed" | "signage" | "new_lead";
const intent = ref<RuleIntent>("new_lead");
const effect = ref<"allowed" | "restricted" | "conditional" | "">("");
const animalScope = ref<"ordinary_pet" | "dog" | "cat" | "other">("ordinary_pet");
const zone = ref("");
const conditions = ref<string[]>([]);
const sourceBasis = ref("");
const mediaId = ref<string | null>(null);
const ocrText = ref("");
const uploading = ref(false);
const busy = ref(false);
const error = ref("");
const selectedRuleId = ref("");

const needsRuleDescription = computed(
  () => intent.value === "changed" || intent.value === "new_lead",
);
const needsExistingRule = computed(
  () => intent.value === "still_valid" || intent.value === "changed",
);
const canSubmit = computed(
  () =>
    props.online &&
    props.signedIn &&
    !busy.value &&
    !uploading.value &&
    (!needsExistingRule.value || Boolean(selectedRuleId.value)) &&
    (!needsRuleDescription.value || (Boolean(effect.value) && Boolean(sourceBasis.value))) &&
    (intent.value !== "signage" || Boolean(mediaId.value)),
);

async function submit() {
  if (!canSubmit.value || !props.placeId) return;
  error.value = "";
  busy.value = true;
  try {
    if (needsExistingRule.value && !selectedRuleId.value) {
      error.value = "请选择这次要确认或修正的具体规则。";
      return;
    }
    if (intent.value === "signage" && !mediaId.value) {
      error.value = "请先上传规则牌或公告照片。";
      return;
    }

    if (intent.value === "signage") {
      const rawText = ocrText.value.trim()
        ? `规则牌 / 公告证据；OCR 待人工核对：${ocrText.value.trim().slice(0, 500)}`
        : "规则牌 / 公告证据；OCR 未取得或未完成。";
      await client.contributeRuleLead(props.placeId, {
        zone_id: zone.value || null,
        raw_text: rawText,
        source_basis: "onsite_signage",
        media_id: mediaId.value,
        ...proximity(),
      });
      emit(
        "done",
        "规则牌证据已进入规则候选提取与人工审核流程。系统不会因为照片或 OCR 自动猜测允许 / 禁止，也不会自动发布正式规则。",
      );
      return;
    }

    const effectLabel = ruleLeadEffectLabel(effect.value);
    const zoneLabel = props.zones.find((item) => item.id === zone.value)?.name ?? "全场 / 不确定";
    const conditionLabel = ruleLeadConditionLabel(conditions.value);
    const sourceBasisLabel = ruleLeadSourceBasisLabel(sourceBasis.value);
    const evidenceNote = ocrText.value.trim()
      ? `；OCR 待人工核对：${ocrText.value.trim().slice(0, 300)}`
      : "";

    if (intent.value === "still_valid") {
      await client.verify({
        place_id: props.placeId,
        zone_id: zone.value || null,
        rule_id: selectedRuleId.value || null,
        event_type: "rule_confirmed",
        result: "still_valid",
        note: "现场核验：页面规则仍然如此",
        evidence_refs: evidenceRefs(mediaId.value),
        ...proximity(),
      });
      emit("done", "核验已提交。它会补充该规则的核验记录，但不会改写规则内容。");
      return;
    }

    const canonicalEffect = effect.value === "restricted" ? "prohibited" : effect.value;
    if (!canonicalEffect) return;
    await client.contributeRuleLead(props.placeId, {
      zone_id: zone.value || null,
      animal_scope: animalScope.value,
      effect: canonicalEffect,
      proposed_conditions: conditions.value,
      raw_text: `规则线索：${effectLabel}；来源：${sourceBasisLabel}；区域：${zoneLabel}；条件：${conditionLabel}${evidenceNote}`,
      source_basis:
        sourceBasis.value === "onsite_signage" ||
        sourceBasis.value === "staff_statement" ||
        sourceBasis.value === "official_online" ||
        sourceBasis.value === "other" ||
        sourceBasis.value === "uncertain"
          ? sourceBasis.value
          : "uncertain",
      media_id: mediaId.value,
      current_rule_id: intent.value === "changed" ? selectedRuleId.value || null : null,
      ...proximity(),
    });
    emit(
      "done",
      intent.value === "changed"
        ? "规则变化线索已提交，进入人工复核；现有正式规则不会自动改写。"
        : "新规则线索已提交，进入人工复核；核验并进入正式候选流程前不会改变准入结论。",
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
