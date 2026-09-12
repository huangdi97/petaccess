<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import {
  client,
  ApiError,
  session,
  type BoundaryMatchResult,
  type EffectiveRuleSet,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";

/**
 * 可解释解析：为什么是「允许 / 有条件 / 禁止 / 未知」。
 *
 * 展示分层解析结果与逐步解释，并叠加使用者自己的共处边界（逐项判定）。
 * 不给总分，不猜测：证据不足时明确显示「未知」。
 */

const route = useRoute();
const placeId = route.params.id as string;

const resolved = ref<EffectiveRuleSet | null>(null);
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

async function resolveRules() {
  error.value = "";
  busy.value = true;
  try {
    const animal = session.activePet
      ? {
          animal: session.activePet.species,
          service_role: session.activePet.service_role ?? "none",
        }
      : { animal: "dog", service_role: session.mode === "service_dog" ? "service_dog" : "none" };
    resolved.value = await client.effectiveRules(placeId, { ...animal, action: "enter" });
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function loadBoundary() {
  note.value = "";
  try {
    boundary.value = await client.boundaryMatch(placeId);
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

onMounted(async () => {
  await Promise.all([resolveRules(), loadBoundary()]);
});
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
        {{
          resolved.effect === "allowed"
            ? "可进入"
            : resolved.effect === "prohibited"
              ? "不可进入"
              : resolved.effect === "conditional"
                ? "有条件可进入"
                : "信息不足"
        }}
      </div>
      <div class="muted">
        合规状态：{{ COMPLIANCE_TEXT[resolved.compliance_state] ?? resolved.compliance_state }} ·
        适用规则 {{ resolved.applicable_rules.length }} 条
      </div>

      <template v-if="resolved.obligations.length">
        <h2>附加条件</h2>
        <div class="muted">{{ resolved.obligations.join(" · ") }}</div>
      </template>

      <h2>推导过程</h2>
      <ol style="padding-left: 18px; margin: 6px 0">
        <li
          v-for="(s, i) in resolved.explanation_steps"
          :key="i"
          class="muted"
          style="margin-bottom: 4px"
        >
          {{ s }}
        </li>
        <li v-if="!resolved.explanation_steps.length" class="muted">无解释步骤</li>
      </ol>

      <template v-if="resolved.suppressed.length">
        <h2>被抑制的规则</h2>
        <div v-for="s in resolved.suppressed" :key="s.rule" class="zone-row">
          <span class="muted">{{ s.rule.slice(0, 8) }}…</span>
          <span class="muted">{{ s.reason }}</span>
        </div>
      </template>

      <template v-if="resolved.unresolved_conflicts.length">
        <h2>未解冲突（需人工复核）</h2>
        <div v-for="(pair, i) in resolved.unresolved_conflicts" :key="i" class="zone-row">
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
              class="tag"
              :class="
                r.verdict === 'MATCH' ? 's-MATCH' : r.verdict === 'CONFLICT' ? 's-RESTRICTED' : ''
              "
              style="color: #fff; border: none"
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
