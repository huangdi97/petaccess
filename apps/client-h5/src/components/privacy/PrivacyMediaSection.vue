<script setup lang="ts">
import { ref, watch } from "vue";
import { client, type MediaMetaView } from "@petaccess/client-core";
import SkeletonList from "../SkeletonList.vue";
import StateMessage from "../StateMessage.vue";
import { presentDescription } from "../../errors";

const props = defineProps<{ signedIn: boolean }>();

const items = ref<MediaMetaView[]>([]);
const loading = ref(false);
const error = ref("");
const deleting = ref<string | null>(null);
const confirmDelete = ref<string | null>(null);

const PURPOSE_LABELS: Record<string, string> = {
  signage_evidence: "规则牌 / 标识证据",
  reality_evidence: "现场事实证据",
  scene_photo: "场所场景图片",
  avatar: "头像",
  import_document: "导入文档",
};

const MODERATION_LABELS: Record<string, string> = {
  pending: "待审核",
  approved: "已审核可用",
  rejected: "审核未通过",
  flagged: "需要复核",
};

function sizeLabel(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

async function load() {
  if (!props.signedIn) {
    items.value = [];
    loading.value = false;
    error.value = "";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    items.value = await client.myMedia();
  } catch (cause) {
    error.value = presentDescription(cause);
  } finally {
    loading.value = false;
  }
}

async function remove(item: MediaMetaView) {
  if (deleting.value) return;
  deleting.value = item.id;
  error.value = "";
  try {
    await client.deleteMedia(item.id);
    items.value = items.value.filter((row) => row.id !== item.id);
    confirmDelete.value = null;
  } catch (cause) {
    error.value = presentDescription(cause);
  } finally {
    deleting.value = null;
  }
}

watch(() => props.signedIn, load, { immediate: true });
</script>

<template>
  <section class="privacy-section" data-testid="privacy-media-section">
    <div class="privacy-section__lead">
      <h2>我的上传媒体</h2>
      <p class="muted">只列出你自己仍在保存的上传文件；隐私页不会自动加载私有图片内容。</p>
    </div>
    <div class="privacy-section__body">
      <StateMessage
        v-if="!signedIn"
        kind="PERMISSION_DENIED"
        description="登录后可以查看和管理自己上传的证据图片、场景图片与头像文件。"
      />
      <SkeletonList v-else-if="loading" :rows="2" />
      <StateMessage
        v-else-if="error && !items.length"
        kind="ERROR"
        title="未能取得上传媒体"
        :description="error"
      >
        <template #action>
          <button type="button" class="primary" @click="load">重试</button>
        </template>
      </StateMessage>
      <p v-else-if="!items.length" class="privacy-media__empty">当前没有仍在保存的上传媒体。</p>

      <div v-else class="privacy-media__list">
        <article v-for="item in items" :key="item.id" class="privacy-media__row">
          <div class="privacy-media__copy">
            <strong>{{ PURPOSE_LABELS[item.purpose] ?? "上传媒体" }}</strong>
            <span class="muted">
              {{ MODERATION_LABELS[item.moderation_status] ?? "审核状态待确认" }}
              · {{ sizeLabel(item.byte_size) }} · {{ item.created_at.slice(0, 10) }}
            </span>
            <span class="muted">
              {{ item.privacy_class === "evidence" ? "核验证据 · 默认私有" : "场景类媒体" }}
            </span>
          </div>

          <button
            v-if="confirmDelete !== item.id"
            type="button"
            class="privacy-media__delete"
            :disabled="Boolean(deleting)"
            @click="confirmDelete = item.id"
          >
            删除文件
          </button>
          <div v-else class="privacy-media__confirm">
            <span>确认删除存储文件？已发布事实本身不会因此被改写。</span>
            <button
              type="button"
              class="privacy-media__delete privacy-media__delete--danger"
              :disabled="Boolean(deleting)"
              @click="remove(item)"
            >
              {{ deleting === item.id ? "删除中…" : "确认删除" }}
            </button>
            <button type="button" class="privacy-media__cancel" @click="confirmDelete = null">
              取消
            </button>
          </div>
        </article>
      </div>

      <p v-if="error && items.length" class="privacy-media__error" role="alert">
        操作未完成：{{ error }}
      </p>
      <p class="privacy-media__note muted">
        删除媒体只删除你的存储文件，不等于撤回已经提交的贡献，也不会自动改变正式规则或已发布现场事实。
      </p>
    </div>
  </section>
</template>

<style scoped>
.privacy-media__empty,
.privacy-media__note,
.privacy-media__error {
  margin: 0;
}

.privacy-media__list {
  display: flex;
  flex-direction: column;
}

.privacy-media__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-4);
  min-height: 72px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.privacy-media__copy {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.privacy-media__copy strong {
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-primary);
}

.privacy-media__copy span {
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

.privacy-media__delete,
.privacy-media__cancel {
  min-height: var(--pa-size-control-md);
  border: 0;
  background: transparent;
  color: var(--pa-color-accent);
  cursor: pointer;
}

.privacy-media__delete--danger {
  color: var(--pa-color-status-restricted);
}

.privacy-media__confirm {
  display: flex;
  flex: 0 1 360px;
  align-items: center;
  justify-content: flex-end;
  gap: var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

.privacy-media__error {
  margin-top: var(--pa-space-3);
  color: var(--pa-color-status-restricted);
}

.privacy-media__note {
  margin-top: var(--pa-space-3);
  font-size: var(--pa-font-size-sm);
}

@media (max-width: 767px) {
  .privacy-media__row {
    align-items: flex-start;
    flex-direction: column;
  }

  .privacy-media__confirm {
    flex: 1 1 auto;
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
