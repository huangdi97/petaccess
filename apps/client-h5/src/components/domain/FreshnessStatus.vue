<script setup lang="ts">
/**
 * FreshnessStatus — 核验时效标签.
 *
 * Renders the freshness bucket (FRESH / RECENT / AGING / HISTORICAL /
 * EXPIRED_FOR_SUMMARY) through FRESHNESS_COPY. When only a verification
 * timestamp is available, the bucket is derived from its age in days.
 */
import { computed } from "vue";
import { FRESHNESS_COPY, type FreshnessKey } from "@petaccess/design-tokens";
import PaBadge from "../ui/PaBadge.vue";

const props = withDefaults(
  defineProps<{
    /** One of FRESH / RECENT / AGING / HISTORICAL / EXPIRED_FOR_SUMMARY. */
    freshness?: string | null;
    /** ISO timestamp; used to derive the bucket when `freshness` is missing. */
    lastVerifiedAt?: string | null;
  }>(),
  { freshness: null, lastVerifiedAt: null },
);

defineOptions({ name: "FreshnessStatus" });

const DAY_MS = 86_400_000;

function bucketFromTimestamp(iso: string): FreshnessKey | null {
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return null;
  const days = (Date.now() - then.getTime()) / DAY_MS;
  if (days < 7) return "FRESH";
  if (days < 30) return "RECENT";
  if (days < 90) return "AGING";
  if (days < 365) return "HISTORICAL";
  return "EXPIRED_FOR_SUMMARY";
}

const freshnessKey = computed<FreshnessKey | null>(() => {
  if (props.freshness && props.freshness in FRESHNESS_COPY) {
    return props.freshness as FreshnessKey;
  }
  return props.lastVerifiedAt ? bucketFromTimestamp(props.lastVerifiedAt) : null;
});

const freshnessCopy = computed(() =>
  freshnessKey.value ? FRESHNESS_COPY[freshnessKey.value] : null,
);
</script>

<template>
  <span v-if="freshnessCopy" class="freshness-status" :data-freshness="freshnessKey">
    <PaBadge :text="freshnessCopy.label" tone="info" />
    <span class="freshness-status__detail">{{ freshnessCopy.detail }}</span>
  </span>
</template>

<style scoped>
.freshness-status {
  display: inline-flex;
  align-items: center;
  gap: var(--pa-space-1);
  white-space: nowrap;
}

.freshness-status__detail {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}
</style>
