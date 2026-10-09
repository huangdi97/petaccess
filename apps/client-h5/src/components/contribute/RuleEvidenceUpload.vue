<script setup lang="ts">
/**
 * RuleEvidenceUpload — governed rule-evidence uploader.
 *
 * Media remains private review evidence. OCR is presentation-only preview and
 * never creates/publishes a Rule.
 */
import { client } from "@petaccess/client-core";
import { presentDescription } from "../../errors";

const props = defineProps<{
  placeId: string;
  required: boolean;
  mediaId: string | null;
  ocrText: string;
  uploading: boolean;
}>();

const emit = defineEmits<{
  "update:mediaId": [value: string | null];
  "update:ocrText": [value: string];
  "update:uploading": [value: boolean];
  error: [message: string];
}>();

async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (!file) return;
  emit("error", "");
  emit("update:uploading", true);
  try {
    const media = await client.uploadMedia(file, "signage_evidence", {
      ownerType: "place",
      ownerId: props.placeId,
    });
    emit("update:mediaId", media.id);
    const meta = await client.mediaMeta(media.id).catch(() => null);
    emit("update:ocrText", meta?.ocr_text ?? "");
  } catch (error) {
    emit("error", presentDescription(error));
  } finally {
    emit("update:uploading", false);
    input.value = "";
  }
}
</script>

<template>
  <section class="rule-evidence" data-ui="rule-evidence">
    <h3>{{ required ? "规则牌 / 公告照片" : "规则牌 / 公告照片（可选）" }}</h3>
    <span class="rule-evidence__label">
      {{ required ? "上传一张可核验照片" : "上传照片" }}
    </span>
    <label
      class="rule-file-picker"
      :class="{ 'rule-file-picker--disabled': uploading }"
      for="rule-evidence-file"
    >
      <span>{{ uploading ? "上传中…" : mediaId ? "重新选择照片" : "选择规则牌照片" }}</span>
      <span class="rule-file-picker__hint">PNG / JPG / WebP</span>
    </label>
    <input
      id="rule-evidence-file"
      class="visually-hidden-file"
      type="file"
      accept="image/png,image/jpeg,image/webp"
      capture="environment"
      :disabled="uploading"
      data-testid="rule-evidence-file"
      @change="upload"
    />
    <p v-if="uploading" class="rule-upload-note">上传中…</p>
    <p v-else-if="mediaId" class="rule-upload-note" data-testid="rule-upload-msg">
      规则牌照片已作为私有审核证据上传，不会直接公开。
    </p>
    <p v-if="ocrText" class="rule-ocr">OCR 仅供人工核对：{{ ocrText.slice(0, 240) }}</p>
    <p class="rule-upload-note">
      照片和 OCR 都只是证据材料，不会自动生成或发布规则。
      <template v-if="required">你不需要先替平台判断“允许 / 禁止 / 有条件”。</template>
    </p>
  </section>
</template>

<style scoped>
.rule-evidence {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.rule-evidence h3 {
  margin: 0 0 var(--pa-space-1);
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
}

.rule-evidence__label,
.rule-upload-note,
.rule-ocr {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

.rule-upload-note,
.rule-ocr {
  margin: 0;
  line-height: var(--pa-line-height-20);
}

.rule-file-picker {
  min-height: var(--pa-size-control-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border-strong);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-accent);
  cursor: pointer;
}

.rule-file-picker:hover,
.rule-file-picker:focus-within {
  background: var(--pa-color-surface-interactive);
}

.rule-file-picker--disabled {
  opacity: 0.55;
  cursor: wait;
}

.rule-file-picker__hint {
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-xs);
}

.visually-hidden-file {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

.rule-ocr {
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
</style>
