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
    error.value = e instanceof ApiError ? e.message : String(e);
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
    note.value = e instanceof ApiError ? e.message : String(e);
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
    <div v-if="error" class="panel" data-testid="match-error">{{ error }}</div>

    <div class="panel">
      <h1>为什么是这个结果</h1>
      <p class="muted" style="margin-top: 4px">
        按 法规 → 监管指引 → 经营方政策 → 场所/分区覆盖 → 临时政策 分层解析，
        并说明每一步如何得出当前结论。
      </p>
      <button class="primary block" :disabled="busy" data-testid="re-resolve" @click="resolveRules">
        {{ busy ? "解析中…" : "重新解析" }}
      </button>
    </div>

    <div v-if="resolved" class="panel" data-testid="effective-rules">
      <div class="muted">生效结论</div>
      <div style="font-size: 22px; font-weight: 700; margin: 4px 0" data-testid="effective-effect">
        {{ answerVerdictLabel(resolved) }}
      </div>
      <div class="muted">
        合规状态：{{
          COMPLIANCE_TEXT[resolved.normative_result.compliance_state] ??
          resolved.normative_result.compliance_state
        }}
        · 适用规则 {{ resolved.normative_result.governing_rule_ids.length }} 条 · 范围：{{
          resolved.scope_summary.scope_level === "zone"
            ? (resolved.scope_summary.zone?.name ?? "该区域")
            : resolved.scope_summary.scope_level === "none"
              ? "尚无规则覆盖"
              : "场所整体"
        }}
      </div>

      <template v-if="resolved.rights_information.operator_obligations.length">
        <h2>附加条件</h2>
        <div class="muted">
          {{ resolved.rights_information.operator_obligations.join(" · ") }}
        </div>
      </template>

      <template v-if="resolved.condition_evaluation.missing_inputs.length">
        <h2>还缺什么</h2>
        <div class="muted">
          补充{{
            resolved.condition_evaluation.missing_inputs
              .map((m) => MISSING_INPUT_TEXT[m] ?? m)
              .join("、")
          }}后可得到更确定的结论 —— 现在不是「允许」。
        </div>
      </template>

      <h2>推导过程</h2>
      <ol style="padding-left: 18px; margin: 6px 0">
        <li v-for="(s, i) in steps" :key="i" class="muted" style="margin-bottom: 4px">
          {{ s }}
        </li>
        <li v-if="!steps.length" class="muted">无解释步骤</li>
      </ol>

      <template v-if="resolved.evidence_state.rules.length">
        <h2>来源</h2>
        <div
          v-for="e in resolved.evidence_state.rules"
          :key="e.rule_id"
          class="muted"
          data-testid="trace-provenance"
        >
          · {{ e.provenance_statement }}
        </div>
      </template>

      <template v-if="resolved.conflict_state.suppressed.length">
        <h2>被抑制的规则</h2>
        <div v-for="s in resolved.conflict_state.suppressed" :key="s.rule" class="zone-row">
          <span class="muted">{{ s.rule.slice(0, 8) }}…</span>
          <span class="muted">{{ s.reason }}</span>
        </div>
      </template>

      <template v-if="resolved.conflict_state.unresolved_conflicts.length">
        <h2>未解冲突（需人工复核）</h2>
        <div
          v-for="(pair, i) in resolved.conflict_state.unresolved_conflicts"
          :key="i"
          class="zone-row"
        >
          <span class="muted">{{ pair[0]?.slice(0, 8) }}… ↔ {{ pair[1]?.slice(0, 8) }}…</span>
          <span class="muted">不做自动裁决</span>
        </div>
      </template>
    </div>

    <div class="panel" data-testid="boundary-section">
      <h2 style="margin-top: 0">与我的共处边界比对</h2>
      <div v-if="note" class="muted" data-testid="boundary-note">{{ note }}</div>
      <template v-if="boundary">
        <div class="muted" style="margin-bottom: 8px">
          共 {{ boundary.results.length }} 项 · 符合 {{ boundary.summary.match }} · 冲突
          {{ boundary.summary.conflict }} · 未知 {{ boundary.summary.unknown }}（{{
            boundary.summary.note
          }}）
        </div>
        <div
          v-for="r in boundary.results"
          :key="r.attribute"
          class="zone-row"
          data-testid="boundary-item"
        >
          <span>
            {{ r.attribute }}
            <span class="tag" style="margin-left: 6px">{{
              STANCE_TEXT[r.stance] ?? r.stance
            }}</span>
          </span>
          <span>
            <span
              class="tag tag--on-solid"
              :class="
                r.verdict === 'MATCH' ? 's-MATCH' : r.verdict === 'CONFLICT' ? 's-RESTRICTED' : ''
              "
              >{{ VERDICT_TEXT[r.verdict] ?? r.verdict }}</span
            >
          </span>
        </div>
      </template>
      <RouterLink to="/boundary" class="pill" style="display: inline-block; margin-top: 10px"
        >设置共处边界</RouterLink
      >
    </div>
  </AppShell>
</template>
