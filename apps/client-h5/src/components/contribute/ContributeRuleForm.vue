<script setup lang="ts">
/**
 * Rule contribution stays a review transaction:
 * existing-rule confirmation / changed-rule lead / new-rule lead + optional
 * signage evidence. Nothing here writes ObservationClaim or publishes Rule.
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { evidenceRefs, proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";
import ContributionStepShell from "./ContributionStepShell.vue";
import RuleLeadFields from "./RuleLeadFields.vue";
import RuleTargetPicker from "./RuleTargetPicker.vue";

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
const mediaId = ref<string | null>(null);
const uploadMsg = ref("");
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
    (!needsRuleDescription.value || Boolean(effect.value)) &&
    (intent.value !== "signage" || Boolean(mediaId.value)),
);

async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (!file) return;
  error.value = "";
  uploadMsg.value = "";
  uploading.value = true;
  try {
    const media = await client.uploadMedia(file, "signage_evidence", {
      ownerType: "place",
      ownerId: props.placeId,
    });
    mediaId.value = media.id;
    uploadMsg.value = "规则牌照片已作为私有审核证据上传，不会直接公开。";
    const meta = await client.mediaMeta(media.id).catch(() => null);
    ocrText.value = meta?.ocr_text ?? "";
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

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
      const note = ocrText.value.trim()
        ? `规则牌 / 公告证据；OCR 待人工核对：${ocrText.value.trim().slice(0, 500)}`
        : "规则牌 / 公告证据；OCR 未取得或未完成。";
      await client.verify({
        place_id: props.placeId,
        zone_id: zone.value || null,
        rule_id: null,
        event_type: "signage_uploaded",
        result: "uncertain",
        note,
        evidence_refs: evidenceRefs(mediaId.value),
        ...proximity(),
      });
      emit("done", "规则牌证据已提交，等待人工核验。照片与 OCR 都不会自动生成或发布正式规则。");
      return;
    }

    const effectLabel =
      effect.value === "allowed"
        ? "明确允许"
        : effect.value === "restricted"
          ? "明确限制"
          : effect.value === "conditional"
            ? "有条件进入"
            : "";
    const zoneLabel = props.zones.find((item) => item.id === zone.value)?.name ?? "全场 / 不确定";
    const conditionLabel = conditions.value.length ? conditions.value.join("、") : "未补充条件";
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
      raw_text: `规则线索：${effectLabel}；区域：${zoneLabel}；条件：${conditionLabel}${evidenceNote}`,
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
    :step="1"
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
      :zones="zones"
    />

    <RuleTargetPicker
      v-if="intent === 'still_valid' || intent === 'changed'"
      v-model="selectedRuleId"
      :place-id="placeId"
      :zones="zones"
    />

    <div class="rule-evidence">
      <h3>{{ intent === "signage" ? "规则牌 / 公告照片" : "规则牌 / 公告照片（可选）" }}</h3>
      <label for="rule-evidence-file">
        {{ intent === "signage" ? "上传一张可核验照片" : "上传照片" }}
      </label>
      <input
        id="rule-evidence-file"
        type="file"
        accept="image/png,image/jpeg,image/webp"
        capture="environment"
        :disabled="uploading"
        data-testid="rule-evidence-file"
        @change="upload"
      />
      <p v-if="uploading" class="rule-upload-note">上传中…</p>
      <p v-else-if="uploadMsg" class="rule-upload-note" data-testid="rule-upload-msg">
        {{ uploadMsg }}
      </p>
      <p v-if="ocrText" class="rule-ocr">OCR 仅供人工核对：{{ ocrText.slice(0, 240) }}</p>
      <p class="rule-upload-note">
        照片和 OCR 都只是证据材料，不会自动生成或发布规则。
        <template v-if="intent === 'signage'"
          >你不需要先替平台判断“允许 / 禁止 / 有条件”。</template
        >
      </p>
    </div>

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
