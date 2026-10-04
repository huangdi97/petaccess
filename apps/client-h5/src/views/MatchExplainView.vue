<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  client,
  ApiError,
  session,
  type AccessAnswer,
  type BoundaryMatchResult,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import { answerExplanation, answerVerdictLabel } from "../answer";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

/**
 * 可解释解析：为什么是「允许 / 有条件 / 禁止 / 未知」。
 *
 * 展示统一答案模型的推导过程与来源，并叠加使用者自己的共处边界（逐项判定）。
 * 不给总分，不猜测：证据不足时明确显示「未知」，并说明还缺什么才能判定。
 */

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const resolved = ref<AccessAnswer | null>(null);
const boundary = ref<BoundaryMatchResult | null>(null);
const error = ref("");
const note = ref("");
const busy = ref(false);

const COMPLIANCE_TEXT: Record<string, string> = {
  CONSISTENT: "各层一致",
  POTENTIAL_CONFLICT: "存在潜在冲突",
  REVIEW_REQUIRED: "需人工复核",
  UNKNOWN: "信息不足",
};

/** §19 — 「为什么」的真实内容来自 resolver 的解释步骤，不在这里重算。 */
const steps = computed(() => answerExplanation(resolved.value));

const VERDICT_TEXT: Record<string, string> = {
  MATCH: "符合",
  CONFLICT: "冲突",
  UNKNOWN: "未知",
};

const STANCE_TEXT: Record<string, string> = {
  accept: "可接受",
  avoid: "希望没有",
  require_prohibited: "必须禁止",
  prefer: "希望提供",
};

const ATTRIBUTE_TEXT: Record<string, string> = {
  off_leash: "脱绳活动",
  designated_area: "指定活动区",
  indoor_access: "室内进入",
  carrier_required: "要求装载",
  muzzle_required: "要求嘴套",
  size_limit: "体型限制",
  breed_limit: "品种限制",
  peak_hours_restriction: "高峰时段限制",
  dining_together: "同桌就餐",
  waiting_area: "等候区",
};

const MISSING_INPUT_TEXT: Record<string, string> = {
  holder_scope: "同行人身份（是否为残障人士）",
  service_role: "动物角色（导盲犬 / 助听犬 / 其他服务犬）",
};

async function resolveRules() {
  error.value = "";
  busy.value = true;
  try {
    const animal = session.activePet
      ? {
          animal: session.activePet.species,
          service_role: session.activePet.service_role ?? "none",
          declared_role: session.activePet.declared_role ?? null,
        }
      : { animal: "dog", service_role: session.mode === "service_dog" ? "service_dog" : "none" };
    resolved.value = await client.accessAnswer(placeId.value, { ...animal, action: "enter" });
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}

async function loadBoundary() {
  note.value = "";
  // Signed-out visitors have no boundary and cannot fetch one — that is a
  // neutral state, not an error banner. The server answers 401 here, which the
  // old `no_boundary_profile` branch below never matched, so it leaked an auth
  // message into the page.
  if (!session.signedIn) {
    boundary.value = null;
    note.value = "尚未设置共处边界，设置后可在此逐项比对。";
    return;
  }
  try {
    boundary.value = await client.boundaryMatch(placeId.value);
  } catch (e) {
    // No profile is a normal state, not an error worth a red banner.
    if (
      e instanceof ApiError &&
      (e as unknown as { code?: string }).code === "no_boundary_profile"
    ) {
      boundary.value = null;
      note.value = "尚未设置共处边界，设置后可在此逐项比对。";
      return;
    }
    note.value = presentDescription(e);
  }
}

// Reactive param, and `immediate` in place of `onMounted`: Vue Router reuses
// this component across `/place/:id/why` changes, so with a one-shot read of
// `route.params.id` the page kept explaining the previous place — reachable via
// the browser's back button between two places' "why" pages. Same defect as
// PlaceView.
watch(
  placeId,
  () => {
    if (!placeId.value) return;
    void Promise.all([resolveRules(), loadBoundary()]);
  },
  { immediate: true },
);
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

    <template v-if="resolved">
      <section class="explain-decision" data-testid="effective-rules">
        <span class="explain-label">当前结论</span>
        <strong class="explain-verdict" data-testid="effective-effect">
          {{ answerVerdictLabel(resolved) }}
        </strong>
        <p class="muted explain-meta">
          {{
            COMPLIANCE_TEXT[resolved.normative_result.compliance_state] ??
            "部分信息仍需核对"
          }}
          ·
          {{
            resolved.scope_summary.scope_level === "zone"
              ? (resolved.scope_summary.zone?.name ?? "当前区域")
              : resolved.scope_summary.scope_level === "none"
                ? "尚无可靠规则覆盖"
                : "场所整体"
          }}
        </p>
      </section>

      <section
        v-if="resolved.rights_information.operator_obligations.length"
        class="explain-section"
      >
        <h2>需要满足</h2>
        <p>{{ resolved.rights_information.operator_obligations.join("、") }}</p>
      </section>

      <section v-if="resolved.condition_evaluation.missing_inputs.length" class="explain-section">
        <h2>还需要哪些信息</h2>
        <p class="muted">
          补充{{
            resolved.condition_evaluation.missing_inputs
              .map((m) => MISSING_INPUT_TEXT[m] ?? "相关条件")
              .join("、")
          }}后，才能得到更确定的结论。当前信息不足不代表允许。
        </p>
      </section>

      <section class="explain-section">
        <h2>推导过程</h2>
        <ol class="explain-steps">
          <li v-for="(s, i) in steps" :key="i">{{ s }}</li>
          <li v-if="!steps.length" class="muted">暂无可展示的解释步骤。</li>
        </ol>
      </section>

      <section v-if="resolved.evidence_state.rules.length" class="explain-section">
        <h2>来源</h2>
        <div
          v-for="(e, i) in resolved.evidence_state.rules"
          :key="i"
          class="explain-source"
          data-testid="trace-provenance"
        >
          {{ e.provenance_statement }}
        </div>
      </section>

      <section
        v-if="
          resolved.conflict_state.suppressed.length ||
          resolved.conflict_state.unresolved_conflicts.length
        "
        class="explain-section explain-review"
      >
        <h2>仍需人工复核</h2>
        <p v-if="resolved.conflict_state.suppressed.length" class="muted">
          有 {{ resolved.conflict_state.suppressed.length }} 条较低优先级信息没有作为当前结论依据。
        </p>
        <p v-if="resolved.conflict_state.unresolved_conflicts.length" class="muted">
          另有 {{ resolved.conflict_state.unresolved_conflicts.length }} 组来源仍存在冲突；系统不会自动裁决。
        </p>
      </section>
    </template>

    <section class="explain-section explain-boundary" data-testid="boundary-section">
      <div class="explain-section__head">
        <div>
          <h2>与我的共处边界比对</h2>
          <p class="muted">这是个人偏好的逐项比对，不是场所评分。</p>
        </div>
        <RouterLink class="btn-inline" to="/boundary">设置边界 →</RouterLink>
      </div>

      <p v-if="note" class="muted" data-testid="boundary-note">{{ note }}</p>

      <template v-if="boundary">
        <p class="explain-boundary__summary muted">
          共 {{ boundary.results.length }} 项 · 符合 {{ boundary.summary.match }} · 不符合
          {{ boundary.summary.conflict }} · 信息不足 {{ boundary.summary.unknown }}
        </p>

        <div
          v-for="r in boundary.results"
          :key="r.attribute"
          class="explain-boundary__row"
          data-testid="boundary-item"
        >
          <div>
            <strong>{{ ATTRIBUTE_TEXT[r.attribute] ?? "共处条件" }}</strong>
            <span class="muted"> · {{ STANCE_TEXT[r.stance] ?? "个人偏好" }}</span>
          </div>
          <span class="explain-boundary__verdict">
            {{ VERDICT_TEXT[r.verdict] ?? "信息不足" }}
          </span>
        </div>
      </template>
    </section>
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

.explain-refresh {
  flex: 0 0 auto;
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  cursor: pointer;
}

.explain-decision {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin-top: var(--pa-space-5);
  padding: var(--pa-space-2) 0 var(--pa-space-2) var(--pa-space-4);
  border-left: var(--pa-border-width-strong) solid var(--pa-color-accent);
}

.explain-label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}

.explain-verdict {
  font-size: var(--pa-font-size-28);
  line-height: var(--pa-line-height-36);
  font-weight: var(--pa-font-weight-650);
}

.explain-meta {
  margin: 0;
}

.explain-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-section h2 {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.explain-section > p {
  max-width: 680px;
  margin: 0;
  line-height: var(--pa-line-height-23);
}

.explain-steps {
  margin: var(--pa-space-3) 0 0;
  padding-left: var(--pa-space-5);
}

.explain-steps li {
  margin-bottom: var(--pa-space-2);
  line-height: var(--pa-line-height-23);
}

.explain-source {
  padding: var(--pa-space-2) 0;
  color: var(--pa-color-text-secondary);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-review {
  border-left: var(--pa-border-width-strong) solid var(--pa-color-warning);
  padding-left: var(--pa-space-4);
}

.explain-review p + p {
  margin-top: var(--pa-space-2);
}

.explain-section__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
  margin-bottom: var(--pa-space-3);
}

.explain-section__head p {
  margin: var(--pa-space-1) 0 0;
}

.explain-boundary__summary {
  margin-bottom: var(--pa-space-2) !important;
}

.explain-boundary__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--pa-space-4);
  min-height: 48px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-boundary__verdict {
  flex: 0 0 auto;
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .explain-head,
  .explain-section__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .explain-boundary__row {
    align-items: flex-start;
  }
}
</style>
