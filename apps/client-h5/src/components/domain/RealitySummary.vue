<script setup lang="ts">
/**
 * RealitySummary — 现场维度的事实小结.
 *
 * Renders RealityStatus plus only the evidence-count and freshness facts that
 * actually exist on the answer — nothing is invented when `reality` is null.
 */
import { computed } from "vue";
import type { RealityAnswer } from "@petaccess/client-core";
import RealityStatus from "./RealityStatus.vue";
import FreshnessStatus from "./FreshnessStatus.vue";

const props = withDefaults(
  defineProps<{
    reality?: RealityAnswer | null;
    title?: string;
  }>(),
  { reality: null, title: "近期现场" },
);

defineOptions({ name: "RealitySummary" });

const countsLine = computed(() => {
  if (!props.reality) return "";
  return `${props.reality.evidence_count} 条依据 · ${props.reality.distinct_source_count} 个来源`;
});
</script>

<template>
  <section class="reality-summary" :aria-label="title">
    <h3 class="reality-summary__title">{{ title }}</h3>
    <RealityStatus :state="reality?.state ?? null" />
    <template v-if="reality">
      <p class="reality-summary__counts">{{ countsLine }}</p>
      <p v-if="reality.recent_count_30d > 0" class="reality-summary__recent">
        近 30 天 {{ reality.recent_count_30d }} 条
      </p>
      <FreshnessStatus
        v-if="reality.freshness_state"
        :freshness="reality.freshness_state"
        :last-verified-at="reality.last_seen_at ?? null"
      />
    </template>
  </section>
</template>

<style scoped>
.reality-summary {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.reality-summary__title {
  margin: 0;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.reality-summary__counts,
.reality-summary__recent {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}
</style>
