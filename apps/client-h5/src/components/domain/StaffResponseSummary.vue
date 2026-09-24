<script setup lang="ts">
/**
 * StaffResponseSummary — 工作人员响应记录小结.
 *
 * Pure facts from the reality answer (`{action}：{count} 次`); renders
 * nothing when there are no rows rather than inventing copy.
 */
import { computed } from "vue";
import type { StaffResponseSummaryItem } from "@petaccess/client-core";
import { staffResponseLines } from "../../reality";

const props = withDefaults(
  defineProps<{
    items: StaffResponseSummaryItem[];
  }>(),
  { items: () => [] },
);

defineOptions({ name: "StaffResponseSummary" });

const lines = computed(() => staffResponseLines(props.items));
</script>

<template>
  <ul v-if="lines.length" class="staff-response-summary">
    <li v-for="line in lines" :key="line" class="staff-response-summary__line">{{ line }}</li>
  </ul>
</template>

<style scoped>
.staff-response-summary {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin: 0;
  padding: 0;
  list-style: none;
}

.staff-response-summary__line {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}
</style>
