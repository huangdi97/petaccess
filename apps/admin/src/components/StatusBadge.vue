<script setup lang="ts">
/**
 * Neutral status badge — admin build (UI_UX_IMPLEMENTATION_SPEC §3).
 *
 * Deliberately the same three-channel contract as the consumer app: icon +
 * label + colour, with the label always in the DOM. Admin tables previously
 * used ad-hoc `.tag.ok` / `.tag.restricted` pills that carried meaning in the
 * class name only; this component makes the vocabulary shared and testable.
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
