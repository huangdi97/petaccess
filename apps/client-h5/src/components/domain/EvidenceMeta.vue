<script setup lang="ts">
/**
 * EvidenceMeta — 依据数量的一行元信息 (`N 条依据 · M 个来源 · D 天前`).
 *
 * Only segments with data are rendered; when every segment is null the line
 * degrades to a neutral hint instead of showing zeroes.
 */
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    evidenceCount?: number | null;
    distinctSourceCount?: number | null;
    daysAgo?: number | null;
  }>(),
  { evidenceCount: null, distinctSourceCount: null, daysAgo: null },
);

defineOptions({ name: "EvidenceMeta" });

const EMPTY_HINT = "依据待补充";

const segments = computed<string[]>(() => {
  const out: string[] = [];
  if (props.evidenceCount != null) out.push(`${props.evidenceCount} 条依据`);
  if (props.distinctSourceCount != null) out.push(`${props.distinctSourceCount} 个来源`);
  if (props.daysAgo != null) out.push(`${props.daysAgo} 天前`);
  return out;
});

const text = computed(() => segments.value.join(" · "));
</script>

<template>
  <p class="evidence-meta">{{ text || EMPTY_HINT }}</p>
</template>

<style scoped>
.evidence-meta {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}
</style>
