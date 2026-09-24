<script setup lang="ts">
/**
 * PaStatusLabel — rule-status pill that supersedes the legacy StatusBadge
 * visually (V020 catalog #14). Status semantics come from @petaccess/design-
 * tokens: icon + label + colour, never colour alone. Keeps the `data-status`
 * attribute = the semantic key for the existing tests.
 */
import { computed } from "vue";
import {
  STATUS_SEMANTICS,
  semanticForAnswerStatus,
  semanticForEffect,
  type IconName,
  type StatusKey,
  type StatusSemantics,
} from "@petaccess/design-tokens";
import PaIcon from "./PaIcon.vue";

/** ICONS has no glyphs for ✓/◐/✕/?/⚠/⟳; map the semantic key to the family. */
const STATUS_ICON: Record<StatusKey, IconName> = {
  ALLOWED: "check-circle",
  CONDITIONAL: "sliders",
  RESTRICTED: "x-circle",
  UNKNOWN: "question-circle",
  CONFLICT: "warning",
  STALE: "refresh",
};

const props = withDefaults(
  defineProps<{
    /** Resolver `Answer.status` (MATCH / CONDITIONAL / RESTRICTED / UNKNOWN / CONFLICT). */
    status?: string | null;
    /** A stored rule effect (allowed / conditional / prohibited). */
    effect?: string | null;
    /** A semantic key directly; takes precedence over status/effect. */
    semantic?: StatusKey | null;
    /** Full-width variant. */
    block?: boolean;
  }>(),
  { status: null, effect: null, semantic: null, block: false },
);

defineOptions({ name: "PaStatusLabel" });

const semantics = computed<StatusSemantics>(() => {
  if (props.semantic) return STATUS_SEMANTICS[props.semantic];
  if (props.effect) return semanticForEffect(props.effect);
  if (props.status) return semanticForAnswerStatus(props.status);
  return STATUS_SEMANTICS.UNKNOWN;
});

const icon = computed<IconName>(() => STATUS_ICON[semantics.value.key]);

const style = computed(() => ({
  color: `var(${semantics.value.colorVar})`,
  backgroundColor: `var(${semantics.value.bgVar})`,
}));
</script>

<template>
  <span
    class="pa-status-label"
    :class="{ 'pa-status-label--block': block }"
    :style="style"
    role="status"
    :data-status="semantics.key"
  >
    <PaIcon :name="icon" size="sm" class="pa-status-label__icon" aria-hidden="true" />
    <span class="pa-status-label__label">{{ semantics.label }}</span>
    <span class="visually-hidden">{{ semantics.ariaLabel }}</span>
  </span>
</template>

<style scoped>
.pa-status-label {
  display: inline-flex;
  align-items: center;
  gap: var(--pa-space-1);
  border: var(--pa-border-width) solid currentColor;
  border-radius: var(--pa-radius-sm);
  padding: var(--pa-space-1) var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  white-space: nowrap;
}

.pa-status-label--block {
  display: flex;
  width: 100%;
  justify-content: flex-start;
}

.pa-status-label__icon {
  flex-shrink: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}
</style>
