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

defineOptions({ name: "ContributeRuleForm" });

const props = defineProps<{
  placeId: string;
  placeName: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

type RuleIntent = "still_valid" | "changed" | "new_lead";
const intent = ref<RuleIntent>("new_lead");
const effect = ref<"allowed" | "restricted" | "conditional" | "">("");
const zone = ref("");
const conditions = ref<string[]>([]);
const mediaId = ref<string | null>(null);
const uploadMsg = ref("");
const ocrText = ref("");
const uploading = ref(false);
const busy = ref(false);
const error = ref("");

const needsRuleDescription = computed(() => intent.value !== "still_valid");
const canSubmit = computed(
  () =>
    props.online &&
    props.signedIn &&
    !busy.value &&
    !uploading.value &&
    (!needsRuleDescription.value || Boolean(effect.value)),
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
    const currentRules = await client.rules(props.placeId);
    const target = currentRules.find((rule) => rule.status === "current") ?? null;
    if (intent.value !== "new_lead" && !target) {
      error.value = "当前没有可核验的已收录规则。请选择“我看到或了解到一条规则”提交新线索。";
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
        rule_id: target?.id ?? null,
        event_type: "field_check",
        result: "still_valid",
        note: "现场核验：页面规则仍然如此",
        evidence_refs: evidenceRefs(mediaId.value),
        ...proximity(),
      });
      emit("done", "核验已提交。它会补充该规则的核验记录，但不会改写规则内容。");
      return;
    }

    await client.verify({
      place_id: props.placeId,
      zone_id: zone.value || null,
      rule_id: intent.value === "changed" ? (target?.id ?? null) : null,
      event_type: intent.value === "changed" ? "rule_changed" : "rule_lead_submitted",
      result: intent.value === "changed" ? "changed" : "uncertain",
      note: `规则线索：${effectLabel}；区域：${zoneLabel}；条件：${conditionLabel}${evidenceNote}`,
      evidence_refs: evidenceRefs(mediaId.value),
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
    title="补充规则线索"
    description="确认、变化和新规则都先作为可核验线索提交；现场 Observation 与正式 Rule 始终分开。"
    @back="emit('back')"
  >
    <div v-if="error" class="notice" data-testid="rule-error">{{ error }}</div>

    <RuleLeadFields
      v-model:intent="intent"
      v-model:effect="effect"
      v-model:zone="zone"
      v-model:conditions="conditions"
      :zones="zones"
    />

    <div class="rule-evidence">
      <h3>规则牌 / 公告照片（可选）</h3>
      <label for="rule-evidence-file">上传照片</label>
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
      <p class="rule-upload-note">照片和 OCR 都只是证据材料，不会自动生成或发布规则。</p>
    </div>

    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="rule-submit" @click="submit">
        {{ busy ? "提交中…" : "提交规则线索" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped src="./ContributeRuleForm.css"></style>
