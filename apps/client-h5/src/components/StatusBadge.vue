<script setup lang="ts">
/**
 * Neutral status badge (UI_UX_IMPLEMENTATION_SPEC §3).
 *
 * A status is always icon + text + colour. The icon and label are rendered as
 * real DOM, so the meaning survives greyscale, colour-blindness, screenshots and
 * screen readers; colour is decoration on top, never the signal.
 */
import { computed } from "vue";
import {
  STATUS_SEMANTICS,
  semanticForAnswerStatus,
  semanticForEffect,
  type StatusKey,
  type StatusSemantics,
} from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{
    /** Resolver `Answer.status` (MATCH / CONDITIONAL / RESTRICTED / UNKNOWN / CONFLICT). */
    status?: string | null;
    /** A stored rule effect (allowed / conditional / prohibited). */
    effect?: string | null;
    /** A semantic key directly. Takes precedence over status/effect. */
    semantic?: StatusKey | null;
    /** Full-width variant for detail headers. */
    block?: boolean;
  }>(),
  { status: null, effect: null, semantic: null, block: false },
);

const semantics = computed<StatusSemantics>(() => {
  if (props.semantic) return STATUS_SEMANTICS[props.semantic];
  if (props.effect) return semanticForEffect(props.effect);
  if (props.status) return semanticForAnswerStatus(props.status);
  return STATUS_SEMANTICS.UNKNOWN;
});

const style = computed(() => ({
  color: `var(${semantics.value.colorVar})`,
  backgroundColor: `var(${semantics.value.bgVar})`,
}));
</script>

<template>
  <span
    class="status-badge"
    :class="{ 'status-badge--block': block }"
    :style="style"
    :data-status="semantics.key"
    role="status"
  >
    <span class="status-badge__icon" aria-hidden="true">{{ semantics.icon }}</span>
    <span class="status-badge__label">{{ semantics.label }}</span>
    <span class="visually-hidden">（{{ semantics.ariaLabel }}）</span>
  </span>
</template>
