<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  client,
  ApiError,
  session,
  type AccessAnswer,
  type BoundaryMatchResult,
  type CoexistenceSnapshot,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import BoundaryMatchPanel from "../components/explain/BoundaryMatchPanel.vue";
import ExplainResultPanel from "../components/explain/ExplainResultPanel.vue";
import StateMessage from "../components/StateMessage.vue";
import { consumerExplanation } from "../consumer/explanation";
import { createEpoch, currentQueryContext, snapshotFor } from "../consumer/repository";
import { divergenceLabel, FRESHNESS_LABELS, realityStateLabel } from "../reality";
import { presentDescription } from "../errors";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));
const resolved = ref<AccessAnswer | null>(null);
const coexistence = ref<CoexistenceSnapshot | null>(null);
const boundary = ref<BoundaryMatchResult | null>(null);
const error = ref("");
const note = ref("");
const busy = ref(false);
const resolveEpoch = createEpoch();
const boundaryEpoch = createEpoch();
const bootstrapEpoch = createEpoch();
const sessionReady = ref(false);

const steps = computed(() => (resolved.value ? consumerExplanation(resolved.value) : []));

const realityExplanation = computed(() => {
  const snapshot = coexistence.value;
  if (!snapshot) return [];
  const reality = snapshot.reality_answer;
  const evidence = snapshot.evidence_summary;
  const lines = [
    realityStateLabel(reality),
    evidence.reality_evidence_count
      ? `现场层共有 ${evidence.reality_evidence_count} 条经核验依据、${evidence.reality_distinct_source_count} 个来源锚点；其中动物出现、工作人员处理和设施事实分开记录。`
      : "当前没有足够的经核验现场依据；这不等于现场没有动物。",
  ];
  if (reality.last_seen_at) {
    lines.push(`最近一条动物出现记录：${reality.last_seen_at.slice(0, 10)}。`);
  }
  if (reality.freshness_state) {
    lines.push(`现场信息时效：${FRESHNESS_LABELS[reality.freshness_state] ?? "时效待核对"}。`);
  }
  lines.push(`规则与现场关系：${divergenceLabel(snapshot.divergence)}。`);
  lines.push("现场事实、工作人员处理和设施记录只描述实际发生的事，不会改写正式规则。");
  return lines;
});

async function resolveRules() {
  const epoch = resolveEpoch.begin();
  error.value = "";
  busy.value = true;
  try {
    const result = await snapshotFor(placeId.value);
    if (!resolveEpoch.isCurrent(epoch)) return;
    coexistence.value = result.snapshot;
    resolved.value = result.snapshot.rule_answer;
  } catch (e) {
    if (!resolveEpoch.isCurrent(epoch)) return;
    coexistence.value = null;
    resolved.value = null;
    error.value = presentDescription(e);
  } finally {
    if (resolveEpoch.isCurrent(epoch)) busy.value = false;
  }
}

async function loadBoundary() {
  const id = placeId.value;
  const epoch = boundaryEpoch.begin();
  note.value = "";
  if (!session.signedIn) {
    if (!boundaryEpoch.isCurrent(epoch) || placeId.value !== id) return;
    boundary.value = null;
    note.value = "登录并加载你的共处边界后，才会在这里逐项比对；公开规则与现场解释不受影响。";
    return;
  }
  try {
    const result = await client.boundaryMatch(id);
    if (!boundaryEpoch.isCurrent(epoch) || placeId.value !== id) return;
    boundary.value = result;
  } catch (e) {
    if (!boundaryEpoch.isCurrent(epoch) || placeId.value !== id) return;
    if (
      e instanceof ApiError &&
      (e as unknown as { code?: string }).code === "no_boundary_profile"
    ) {
      boundary.value = null;
      note.value = "尚未设置共处边界，设置后可在此逐项比对。";
      return;
    }
    boundary.value = null;
    note.value = presentDescription(e);
  }
}

async function bootstrap() {
  const id = placeId.value;
  if (!id) return;
  const epoch = bootstrapEpoch.begin();
  sessionReady.value = false;
  let privateContextAvailable = true;
  try {
    await session.restore();
  } catch {
    // Rule/Reality explanations are public. A failed account restore may
    // suppress the private boundary comparison, but must not blank the page.
    privateContextAvailable = false;
    boundary.value = null;
    note.value = "账号状态暂不可用；公开规则与现场解释仍可查看，共处边界暂未加载。";
  }
  if (!bootstrapEpoch.isCurrent(epoch) || placeId.value !== id) return;
  sessionReady.value = true;
  if (privateContextAvailable) {
    await Promise.all([resolveRules(), loadBoundary()]);
  } else {
    await resolveRules();
  }
}

watch(placeId, () => void bootstrap(), { immediate: true });

watch(currentQueryContext, () => {
  if (!placeId.value || !sessionReady.value) return;
  void resolveRules();
});
</script>

<template>
  <AppShell>
    <header class="explain-head">
      <div>
        <h1>为什么是这个结果</h1>
        <p class="muted">
          这里展示当前查询所依据的规则层级、适用条件和来源；不会用一次现场观察替代正式规则。
        </p>
      </div>
      <button
        type="button"
        class="explain-refresh"
        :disabled="busy"
        data-testid="re-resolve"
        @click="resolveRules"
      >
        {{ busy ? "更新中…" : "重新获取" }}
      </button>
    </header>

    <StateMessage v-if="error" kind="ERROR" :description="error" data-testid="match-error">
      <template #action>
        <button type="button" class="primary" @click="resolveRules">重试</button>
      </template>
    </StateMessage>

    <ExplainResultPanel v-if="resolved" :answer="resolved" :steps="steps" />

    <section v-if="coexistence" class="reality-explain" data-testid="reality-explanation">
      <h2>为什么现场摘要这样显示</h2>
      <ol>
        <li v-for="(line, index) in realityExplanation" :key="index">{{ line }}</li>
      </ol>
      <RouterLink class="btn-inline" :to="`/place/${placeId}/evidence`">
        查看现场证据与来源 →
      </RouterLink>
    </section>

    <BoundaryMatchPanel :boundary="boundary" :note="note" />
  </AppShell>
</template>

<style scoped>
.explain-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-5);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.reality-explain {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.reality-explain h2 {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.reality-explain ol {
  margin: var(--pa-space-3) 0;
  padding-left: var(--pa-space-5);
}

.reality-explain li {
  margin-bottom: var(--pa-space-2);
  line-height: var(--pa-line-height-23);
}

.explain-refresh {
  flex: 0 0 auto;
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  cursor: pointer;
}

@media (max-width: 767px) {
  .explain-head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }
}
</style>
