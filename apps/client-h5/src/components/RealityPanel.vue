<script setup lang="ts">
/**
 * RealityPanel — the "近期现场" block of the Place Coexistence Passport (AC10).
 *
 * VISUAL FIDELITY (Goal §3.2/§3.3): the block is a flat divider-led section,
 * NOT a card (no white-card wall inside the dossier), and every raw enum
 * (observed zone/action, staff response action, facility type/state) renders
 * through the shared consumer label mapper — raw values never reach the
 * screen. Consumes ONE CoexistenceSnapshot — it never recomputes rule or
 * reality (AC9). Every sentence comes from the shared H5 reality vocabulary
 * in ../reality.ts and the consumer label mapper, so a state can only be
 * worded one way across the app.
 */
import type { CoexistenceSnapshot } from "@petaccess/client-core";
import { divergenceLabel, realityStateLabel, realityTone } from "../reality";
import {
  animalFacilityLabel,
  facilityStateLabel,
  observedActionLabel,
  staffActionLabel,
  zoneTypeLabel,
} from "../consumer/labels";

import EvidenceStatus from "./domain/EvidenceStatus.vue";
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    snapshot: CoexistenceSnapshot | null;
    loading?: boolean;
    placeId?: string | null;
  }>(),
  { loading: false, placeId: null },
);

/** M5 B1 — map the raw verification enum to the shared evidence vocabulary. */
const verification = computed(() => {
  const raw = props.snapshot?.evidence_summary.reality_verification_state;
  return raw === "VERIFIED"
    ? "verified"
    : raw === "DISPUTED"
      ? "disputed"
      : raw === "HISTORICAL"
        ? "historical"
        : "pending";
});

/** 近期出现区域 — consumer zone names, never raw zone_type values. */
const observedZones = computed(() =>
  (props.snapshot?.reality_answer.observed_zones ?? []).map(zoneTypeLabel),
);

/** 近期观察动作 — consumer labels, never raw ObservedAction enums. */
const observedActions = computed(() =>
  (props.snapshot?.reality_answer.observed_actions ?? []).map(observedActionLabel),
);

/** 工作人员处理计数 — consumer labels, never raw StaffResponseAction. */
const staffLines = computed(() =>
  (props.snapshot?.staff_response_summary ?? []).map(
    (s) => `${staffActionLabel(s.response_action)}：${s.count} 次`,
  ),
);

/** 动物相关设施 — consumer labels, never raw facility enums. */
const facilityLines = computed(() =>
  (props.snapshot?.facility_summary ?? []).map((f) => {
    const op = facilityStateLabel(f.operational_state);
    const state = op === "正常使用中" ? "" : `（${op}）`;
    return `${animalFacilityLabel(f.facility_type)}${state}：${f.count} 处`;
  }),
);
</script>

<template>
  <section class="reality-panel" data-testid="reality-panel">
    <h2 class="reality-panel__title">近期现场（≠ 规则）</h2>
    <div v-if="loading" class="muted">加载中…</div>
    <template v-else-if="snapshot">
      <div class="reality-panel__headline">
        <span class="reality-panel__state" :class="realityTone(snapshot.reality_answer.state)">
          {{ realityStateLabel(snapshot.reality_answer) }}
        </span>
        <span v-if="snapshot.reality_answer.days_since_last_seen != null" class="muted">
          {{ snapshot.reality_answer.days_since_last_seen }} 天前最近一次记录
        </span>
      </div>
      <p v-if="snapshot.reality_answer.note" class="muted">{{ snapshot.reality_answer.note }}</p>
      <ul v-if="observedZones.length" class="reality-panel__facts">
        <li>出现区域：{{ observedZones.join("、") }}</li>
      </ul>
      <ul v-if="observedActions.length" class="reality-panel__facts">
        <li>观察动作：{{ observedActions.join("、") }}</li>
      </ul>

      <h3 class="reality-panel__subtitle">工作人员处理（计数，仅事实）</h3>
      <ul v-if="staffLines.length" class="reality-panel__facts">
        <li v-for="(l, i) in staffLines" :key="i">{{ l }}</li>
      </ul>
      <p v-else class="muted">暂无经核验的处理记录（≠ 未处理）。</p>

      <h3 class="reality-panel__subtitle">动物相关设施</h3>
      <ul v-if="facilityLines.length" class="reality-panel__facts">
        <li v-for="(l, i) in facilityLines" :key="i">{{ l }}</li>
      </ul>
      <p v-else class="muted">暂无经核验的设施记录（设施 ≠ 入场政策）。</p>

      <h3 class="reality-panel__subtitle">规则与现场差异</h3>
      <p>
        <strong>{{ divergenceLabel(snapshot.divergence) }}</strong>
      </p>
      <p v-if="snapshot.divergence" class="muted">{{ snapshot.divergence.note }}</p>

      <h3 class="reality-panel__subtitle">证据</h3>
      <ul class="reality-panel__facts">
        <li>
          现实证据：{{ snapshot.evidence_summary.reality_evidence_count }} 条 /
          {{ snapshot.evidence_summary.reality_distinct_source_count }} 个独立来源
        </li>
        <li>
          现实核验状态：
          <EvidenceStatus :state="verification" />
        </li>
      </ul>
      <p class="muted small">所有现实事实经人工核验后才展示；过期事实不呈现为近期。</p>
      <footer class="reality-panel__foot">
        <RouterLink
          v-if="placeId"
          class="btn"
          :to="`/place/${placeId}/reality`"
          data-testid="open-reality-trace"
        >
          查看现场轨迹
        </RouterLink>
      </footer>
    </template>
    <p v-else class="muted">暂无足够现场记录（暂无记录 ≠ 没有动物）。</p>
  </section>
</template>

<style scoped>
/* Flat divider-led section inside the dossier — deliberately NOT a card. */
.reality-panel {
  margin: 0;
}

.reality-panel__title {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}

.reality-panel__headline {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  flex-wrap: wrap;
}

.reality-panel__state {
  display: inline-block;
  padding: 2px var(--pa-space-2);
  border-radius: var(--pa-radius-sm);
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-medium);
}

.reality-panel__state.info {
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
}

.reality-panel__state.warn {
  background: var(--pa-color-status-conditional-bg);
  color: var(--pa-color-status-conditional);
}

.reality-panel__state.neutral {
  background: var(--pa-color-bg-sunken);
  color: var(--pa-color-text-secondary);
}

.reality-panel__subtitle {
  margin: var(--pa-space-4) 0 var(--pa-space-2);
  font-size: var(--pa-font-size-17);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-secondary);
}

.reality-panel__facts {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.reality-panel__facts li {
  margin: 0;
}

.muted {
  color: var(--pa-color-text-muted);
}

.small {
  font-size: var(--pa-font-size-md);
}

.reality-panel__foot {
  margin-top: var(--pa-space-3);
}
</style>
