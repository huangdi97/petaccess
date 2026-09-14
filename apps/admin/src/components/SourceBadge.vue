<script setup lang="ts">
/**
 * Foreground source badge — admin build (UI_UX_IMPLEMENTATION_SPEC §4).
 *
 * Admin keeps the finer `evidence_strength` in the evidence viewer; this badge
 * is the coarse provenance label shared with the consumer app.
 */
import { computed } from "vue";
import { badgeForSourceType } from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{ sourceType?: string | null; label?: string | null }>(),
  { sourceType: null, label: null },
);

const badge = computed(() => badgeForSourceType(props.sourceType));
</script>

<template>
  <span class="source-badge" :data-source-badge="badge.key">
    <span class="source-badge__icon" aria-hidden="true">{{ badge.icon }}</span>
    <span>{{ label ?? badge.label }}</span>
  </span>
</template>
