<script setup lang="ts">
/**
 * RealityPanel — the "近期现场 / 工作人员处理 / 动物设施 / 规则与现场差异 / 证据"
 * block of the v0.9 Place Coexistence Passport (AC10).
 *
 * Consumes ONE CoexistenceSnapshot — it never recomputes rule or reality
 * (AC9). Every sentence comes from the shared H5 reality vocabulary in
 * ../reality.ts, so a state can only be worded one way across the app.
 */
import type { CoexistenceSnapshot } from "@petaccess/client-core";
import {
  divergenceLabel,
  facilityLines,
  realityStateLabel,
  realityTone,
  staffResponseLines,
} from "../reality";

defineProps<{ snapshot: CoexistenceSnapshot | null; loading?: boolean }>();
</script>

<template>
  <section class="panel" data-testid="reality-panel">
    <h2>近期现场（≠ 规则）</h2>
    <div v-if="loading" class="muted">加载中…</div>
    <template v-else-if="snapshot">
      <div class="row">
        <span class="badge" :class="realityTone(snapshot.reality_answer.state)">
          {{ realityStateLabel(snapshot.reality_answer) }}
        </span>
        <span v-if="snapshot.reality_answer.days_since_last_seen != null" class="muted">
          {{ snapshot.reality_answer.days_since_last_seen }} 天前最近一次记录
        </span>
      </div>
      <p v-if="snapshot.reality_answer.note" class="muted">{{ snapshot.reality_answer.note }}</p>
      <ul v-if="snapshot.reality_answer.observed_zones.length" class="facts">
        <li>出现区域：{{ snapshot.reality_answer.observed_zones.join("、") }}</li>
      </ul>
      <ul v-if="snapshot.reality_answer.observed_actions.length" class="facts">
        <li>观察动作：{{ snapshot.reality_answer.observed_actions.join("、") }}</li>
      </ul>

      <h3>工作人员处理（计数，仅事实）</h3>
      <ul v-if="staffResponseLines(snapshot.staff_response_summary).length" class="facts">
        <li v-for="(l, i) in staffResponseLines(snapshot.staff_response_summary)" :key="i">{{ l }}</li>
      </ul>
      <p v-else class="muted">暂无已核验的工作人员处理记录（≠ 未处理）。</p>

      <h3>动物相关设施</h3>
      <ul v-if="facilityLines(snapshot.facility_summary).length" class="facts">
        <li v-for="(l, i) in facilityLines(snapshot.facility_summary)" :key="i">{{ l }}</li>
      </ul>
      <p v-else class="muted">暂无已核验的动物设施记录（设施 ≠ 入场政策）。</p>

      <h3>规则与现场差异</h3>
      <p>
        <strong>{{ divergenceLabel(snapshot.divergence) }}</strong>
      </p>
      <p v-if="snapshot.divergence" class="muted">{{ snapshot.divergence.note }}</p>

      <h3>证据</h3>
      <ul class="facts">
        <li>现实证据：{{ snapshot.evidence_summary.reality_evidence_count }} 条 /
          {{ snapshot.evidence_summary.reality_distinct_source_count }} 个独立来源</li>
        <li>现实核验状态：{{ snapshot.evidence_summary.reality_verification_state ?? "未记录" }}</li>
      </ul>
      <p class="muted small">所有现实事实经人工核验后才展示；过期事实不呈现为近期。</p>
    </template>
    <p v-else class="muted">暂无现场数据（暂无记录 ≠ 没有动物）。</p>
  </section>
</template>

<style scoped>
.panel {
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 14px;
  margin-top: 12px;
}
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.badge {
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 13px;
}
.badge.info {
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
}
.badge.warn {
  background: var(--pa-color-status-conditional-bg);
  color: var(--pa-color-status-conditional);
}
.badge.neutral {
  background: var(--pa-color-bg-sunken);
  color: var(--pa-color-text-secondary);
}
.facts {
  margin: 6px 0;
  padding-left: 18px;
}
.facts li {
  margin: 2px 0;
}
.muted {
  color: var(--muted);
}
.small {
  font-size: 12px;
}
</style>