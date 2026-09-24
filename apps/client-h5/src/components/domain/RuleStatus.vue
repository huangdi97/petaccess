<script setup lang="ts">
/**
 * RuleStatus — 规则维度的状态标签 (V020_DESIGN_SYSTEM_SPEC §13).
 *
 * Renders the rule-side conclusion from the unified answer model. Every rule
 * status goes through @petaccess/design-tokens STATUS_SEMANTICS — pages never
 * translate ALLOWED/RESTRICTED/UNKNOWN themselves.
 */
import { computed } from "vue";
import {
  STATUS_SEMANTICS,
  semanticForAnswerStatus,
  semanticForEffect,
  type StatusKey,
  type StatusSemantics,
} from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";
import type { IconName } from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{
    /** Resolver `Answer.status` (MATCH / CONDITIONAL / RESTRICTED / UNKNOWN / CONFLICT). */
    status?: string | null;
    /** A stored rule effect (allowed / conditional / prohibited). */
    effect?: string | null;
    /** A semantic key directly; takes precedence over status/effect. */
    semantic?: StatusKey | null;
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

const ICON_BY_KEY: Record<StatusKey, IconName> = {
  ALLOWED: "check-circle",
  CONDITIONAL: "sliders",
  RESTRICTED: "x-circle",
  UNKNOWN: "question-circle",
  CONFLICT: "warning",
  STALE: "refresh",
};
</script>

<template>
  <span
    class="rule-status"
    :class="{ 'rule-status--block': block }"
    :style="{ color: `var(${semantics.colorVar})`, background: `var(${semantics.bgVar})` }"
    :data-status="semantics.key"
    role="status"
  >
    <PaIcon
      class="rule-status__icon"
      :name="ICON_BY_KEY[semantics.key]"
      size="sm"
      aria-hidden="true"
    />
    <span class="rule-status__label">{{ semantics.label }}</span>
    <span class="visually-hidden">{{ semantics.ariaLabel }}</span>
  </span>
</template>

<style scoped>
.rule-status {
  display: inline-flex;
  align-items: center;
  gap: var(--pa-space-1);
  border: var(--pa-border-width) solid currentColor;
  border-radius: var(--pa-radius-sm);
  padding: 2px var(--pa-space-2);
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  white-space: nowrap;
}

.rule-status--block {
  display: flex;
  width: 100%;
  justify-content: flex-start;
  padding: var(--pa-space-1) var(--pa-space-3);
  font-size: var(--pa-font-size-base);
}

.rule-status__icon {
  flex: none;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  margin: -1px;
  padding: 0;
  border: 0;
  white-space: nowrap;
}
</style>
