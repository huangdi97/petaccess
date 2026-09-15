<script setup lang="ts">
/**
 * Foreground source badge (UI_UX_IMPLEMENTATION_SPEC §4).
 *
 * Users see a coarse, meaningful provenance label ("官方法规", "政府来源",
 * "管理方确认", "现场核验", "用户现场报告", "需要复核"); the backend keeps the finer
 * evidence strength for review purposes.
 */
import { computed } from "vue";
import { badgeForSourceType } from "@petaccess/design-tokens";

const props = withDefaults(defineProps<{ sourceType?: string | null; label?: string | null }>(), {
  sourceType: null,
  label: null,
});

const badge = computed(() => badgeForSourceType(props.sourceType));
</script>

<template>
  <span class="source-badge" :data-source-badge="badge.key">
    <span class="source-badge__icon" aria-hidden="true">{{ badge.icon }}</span>
    <span>{{ label ?? badge.label }}</span>
  </span>
</template>
