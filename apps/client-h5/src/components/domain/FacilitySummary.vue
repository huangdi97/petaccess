<script setup lang="ts">
/**
 * FacilitySummary — 场所设施信息小结.
 *
 * Facts only: `{facility_type}：{count} 处` with a state suffix unless the
 * facility is active, and a verified date when one exists. Empty → nothing.
 */
import { computed } from "vue";
import type { FacilitySummaryItem } from "@petaccess/client-core";
import { facilityLines } from "../../reality";

const props = withDefaults(
  defineProps<{
    items: FacilitySummaryItem[];
  }>(),
  { items: () => [] },
);

defineOptions({ name: "FacilitySummary" });

const lines = computed(() => facilityLines(props.items));
</script>

<template>
  <ul v-if="lines.length" class="facility-summary">
    <li v-for="line in lines" :key="line" class="facility-summary__line">{{ line }}</li>
  </ul>
</template>

<style scoped>
.facility-summary {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin: 0;
  padding: 0;
  list-style: none;
}

.facility-summary__line {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}
</style>
