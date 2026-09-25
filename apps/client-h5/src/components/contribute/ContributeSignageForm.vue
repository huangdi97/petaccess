<script setup lang="ts">
/**
 * ContributeSignageForm — 拍规则牌：上传 → OCR 预览（仅供审核参考）→ 结构化确认 →
 * legacy verify（signage_uploaded）。照片/OCR 永不自动成规则（ADR-005/022）。
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { evidenceRefs, proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";

defineOptions({ name: "ContributeSignageForm" });

const props = defineProps<{
  placeId: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const mediaId = ref<string | null>(null);
const ocrText = ref("");
const ocrCandidates = ref<string[]>([]);
const uploadMsg = ref("");
const uploading = ref(false);
const zone = ref("");
const conditions = ref<string[]>([]);
const note = ref("");
const placeConfirmed = ref(false);
const busy = ref(false);
const error = ref("");

const CONDITION_OPTIONS = [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
];

const canSubmit = computed(() => props.online && props.signedIn && !busy.value);

async function upload(e: Event) {
  const input = e.target as HTMLInputElement;
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
    uploadMsg.value = media.duplicate_of
      ? "该图片此前已上传过（内容一致）。仍会作为本次证据提交。"
      : `已上传（${Math.round(media.byte_size / 1024)}KB）。证据媒体不公开，仅审核可见。`;
    try {
      const meta = await client.mediaMeta(media.id);
      ocrText.value = meta.ocr_text ?? "";
      ocrCandidates.value = Array.isArray(meta.ocr_rule_candidates)
        ? (meta.ocr_rule_candidates as unknown[]).map(String)
        : [];
    } catch {
      ocrText.value = "";
      ocrCandidates.value = [];
    }
  } catch (err) {
    error.value = presentDescription(err);
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function submit() {
  if (!canSubmit.value) return;
  if (!mediaId.value) {
    error.value = "请先上传规则牌照片。";
    return;
  }
  if (!placeConfirmed.value) {
    error.value = "请确认照片拍摄于本场所。";
    return;
  }
  error.value = "";
  busy.value = true;
  try {
    const parts: string[] = [];
    if (note.value.trim()) parts.push(note.value.trim());
    if (ocrText.value.trim()) parts.push(`[OCR 待人工核对] ${ocrText.value.trim()}`);
    if (conditions.value.length) parts.push(`条件：${conditions.value.join(",")}`);
    await client.verify({
      place_id: props.placeId,
      zone_id: zone.value || null,
      rule_id: null,
      event_type: "signage_uploaded",
      result: "uncertain",
      note: parts.join(" | ").slice(0, 1000) || null,
      evidence_refs: evidenceRefs(mediaId.value),
      ...proximity(),
    });
    emit(
      "done",
      "证据已提交，等待人工审核。照片与 OCR 文本都只是审核材料，不会自动成为规则，也不会自动发布。",
    );
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div>
    <strong>拍规则牌</strong>
    <div class="notice" style="margin-top: 8px">
      证据说明：照片用于人工审核，属受控长期保存的证据媒体，不对外公开；平台不会仅凭照片自动生成或发布规则。
    </div>
    <div v-if="error" class="notice" data-testid="signage-error">{{ error }}</div>

    <label for="signage-file">现场告示照片（相机 / 相册）</label>
    <input
      id="signage-file"
      type="file"
      accept="image/png,image/jpeg,image/webp"
      capture="environment"
      data-testid="signage-file"
      :disabled="uploading"
      @change="upload"
    />
    <div v-if="uploading" class="muted" data-testid="signage-uploading">上传中…</div>
    <div v-if="uploadMsg" class="notice" data-testid="signage-upload-msg">{{ uploadMsg }}</div>

    <template v-if="mediaId">
      <label>OCR 预览（仅作审核参考，需人工核对）</label>
      <div class="panel" data-testid="ocr-preview">
        <div v-if="ocrText" style="white-space: pre-wrap">{{ ocrText }}</div>
        <div v-else class="muted">
          未取得 OCR 文本（信息不完整）。照片仍会作为证据提交，由人工阅读。
        </div>
        <div v-if="ocrCandidates.length" class="muted" style="margin-top: 6px">
          可能的规则要点：{{ ocrCandidates.join(" / ") }}
        </div>
      </div>

      <label for="signage-zone">拍摄区域（可选）</label>
      <select v-model="zone" id="signage-zone">
        <option value="">全场 / 不确定</option>
        <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
      </select>

      <label>条件（可多选 / 全不选）</label>
      <div class="row">
        <button
          v-for="c in CONDITION_OPTIONS"
          :key="c.key"
          class="pill"
          :class="{ active: conditions.includes(c.key) }"
          @click="
            conditions.includes(c.key)
              ? (conditions = conditions.filter((k) => k !== c.key))
              : conditions.push(c.key)
          "
        >
          {{ c.label }}
        </button>
      </div>

      <label for="signage-note">补充说明（结构化补充，非评论区）</label>
      <input v-model="note" id="signage-note" maxlength="500" placeholder="如：告示位于入口右侧" />

      <label style="display: flex; gap: 8px; align-items: center; margin-top: 10px">
        <input v-model="placeConfirmed" type="checkbox" data-testid="signage-place-confirm" />
        <span>我确认这张照片拍摄于本场所</span>
      </label>

      <div class="row" style="margin-top: 14px">
        <button
          class="primary"
          :disabled="!canSubmit || !placeConfirmed"
          data-testid="signage-submit"
          @click="submit"
        >
          {{ busy ? "提交中…" : "提交证据" }}
        </button>
        <button :disabled="busy" @click="emit('back')">返回</button>
      </div>
    </template>
    <div v-else class="row" style="margin-top: 14px">
      <button :disabled="busy" @click="emit('back')">返回</button>
    </div>
  </div>
</template>
