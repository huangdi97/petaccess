<script setup lang="ts">
/**
 * EvidenceStatus — 证据核验状态标签 (V020_DESIGN_SYSTEM_SPEC §13).
 *
 * verified / pending / disputed / historical render through
 * EVIDENCE_STATE_COPY — the raw enum strings never reach the template.
 */
import { computed } from "vue";
import {
  EVIDENCE_STATE_COPY,
  type EvidenceStateCopy,
  type EvidenceStateKey,
} from "@petaccess/design-tokens";
import type { IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

const props = withDefaults(
  defineProps<{
    state?: "verified" | "pending" | "disputed" | "historical" | null;
    block?: boolean;
  }>(),
  { state: null, block: false },
);

defineOptions({ name: "EvidenceStatus" });

const ICON_BY_STATE: Record<EvidenceStateKey, IconName> = {
  verified: "shield-check",
  pending: "clock",
  disputed: "shield-alert",
  historical: "clock",
};

/** Null / unknown states degrade to "pending" (recorded, not yet verified). */
const stateKey = computed<EvidenceStateKey>(() =>
  props.state && props.state in EVIDENCE_STATE_COPY ? props.state : "pending",
);

const copy = computed<EvidenceStateCopy>(() => EVIDENCE_STATE_COPY[stateKey.value]);
</script>

<template>
  <span
    class="evidence-status"
    :class="{ 'evidence-status--block': block }"
    :style="{ color: `var(${copy.colorVar})`, background: `var(${copy.bgVar})` }"
    :data-state="stateKey"
    role="status"
  >
    <PaIcon
      class="evidence-status__icon"
      :name="ICON_BY_STATE[stateKey]"
      size="sm"
      aria-hidden="true"
    />
    <span class="evidence-status__label">{{ copy.label }}</span>
    <span class="visually-hidden">{{ copy.description }}</span>
  </span>
</template>

<style scoped>
.evidence-status {
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

.evidence-status--block {
  display: flex;
  width: 100%;
  justify-content: flex-start;
  padding: var(--pa-space-1) var(--pa-space-3);
  font-size: var(--pa-font-size-base);
}

.evidence-status__icon {
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
