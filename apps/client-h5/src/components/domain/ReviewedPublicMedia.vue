<script setup lang="ts">
/**
 * Fail-closed renderer for media that already passed the public evidence gate.
 *
 * Public URLs are intentionally temporary. Expiry/network failure must not
 * leave a broken-image icon or trigger a private-media fallback. The textual
 * fact/provenance remains the durable consumer record.
 */
import { ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    src: string;
    alt: string;
    loading?: "eager" | "lazy";
  }>(),
  { loading: "lazy" },
);

const failed = ref(false);
watch(
  () => props.src,
  () => {
    failed.value = false;
  },
);
</script>

<template>
  <img
    v-if="!failed"
    :src="src"
    :alt="alt"
    :loading="loading"
    decoding="async"
    referrerpolicy="no-referrer"
    @error="failed = true"
  />
  <span v-else class="reviewed-media-fallback" role="status" data-ui="public-media-unavailable">
    <strong>公开图片暂不可用</strong>
    <small>临时链接可能已失效；事实、来源与核验记录仍可继续查看。</small>
  </span>
</template>

<style scoped>
.reviewed-media-fallback {
  width: 100%;
  height: 100%;
  min-height: 72px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  padding: var(--pa-space-3);
  background:
    linear-gradient(120deg, var(--pa-color-accent-weak), transparent 54%),
    var(--pa-color-surface-muted);
  color: var(--pa-color-text-secondary);
}

.reviewed-media-fallback strong {
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}

.reviewed-media-fallback small {
  font-size: var(--pa-font-size-xs);
  line-height: var(--pa-line-height-20);
}
</style>
