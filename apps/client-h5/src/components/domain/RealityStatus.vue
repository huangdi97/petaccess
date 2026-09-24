<script setup lang="ts">
/**
 * RealityStatus — 现场维度的状态标签 (V020_DESIGN_SYSTEM_SPEC §13).
 *
 * Every reality state renders through @petaccess/design-tokens
 * REALITY_STATE_COPY — pages never translate OBSERVED_RECENTLY /
 * INSUFFICIENT_OBSERVATION / DISPUTED themselves.
 */
import { computed } from "vue";
import {
  REALITY_STATE_COPY,
  realityCopyFor,
  type RealityStateCopy,
} from "@petaccess/design-tokens";
import type { IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

const props = withDefaults(
  defineProps<{
    /** `RealityAnswer.state` (OBSERVED_RECENTLY / ... / DISPUTED). */
    state?: string | null;
    block?: boolean;
  }>(),
  { state: null, block: false },
);

defineOptions({ name: "RealityStatus" });

/** Unknown / null states degrade to the neutral "no record" copy. */
const copy = computed<RealityStateCopy>(() => realityCopyFor(props.state));

const ICON_BY_STATE: Record<string, IconName> = {
  OBSERVED_RECENTLY: "eye",
  MULTI_EVIDENCE_OBSERVED: "eye",
  NO_RECENT_RECORD: "question-circle",
  INSUFFICIENT_OBSERVATION: "question-circle",
  DISPUTED: "flag",
  OBSERVED_HISTORICALLY: "clock",
};

/** Unrecognised states share the neutral question glyph with the degraded copy. */
const icon = computed<IconName>(() => ICON_BY_STATE[props.state ?? ""] ?? "question-circle");

/** `data-state` reflects the state actually resolved (null → NO_RECENT_RECORD). */
const stateKey = computed<string>(() => {
  if (props.state && props.state in REALITY_STATE_COPY) return props.state;
  return "NO_RECENT_RECORD";
});
</script>

<template>
  <span
    class="reality-status"
    :class="{ 'reality-status--block': block }"
    :style="{ color: `var(${copy.colorVar})`, background: `var(${copy.bgVar})` }"
    :data-state="stateKey"
    role="status"
  >
    <PaIcon class="reality-status__icon" :name="icon" size="sm" aria-hidden="true" />
    <span class="reality-status__label">{{ copy.label }}</span>
    <span class="visually-hidden">{{ copy.ariaLabel }}</span>
  </span>
</template>

<style scoped>
.reality-status {
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

.reality-status--block {
  display: flex;
  width: 100%;
  justify-content: flex-start;
  padding: var(--pa-space-1) var(--pa-space-3);
  font-size: var(--pa-font-size-base);
}

.reality-status__icon {
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
