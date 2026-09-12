<script setup lang="ts">
import { ref } from "vue";
import { get, post, errText, shortId } from "../api";
import { ANIMAL_SCOPES } from "../v05";

interface Explanation {
  effect: string;
  compliance_state: string;
  applicable_rules: string[];
  suppressed: { rule: string; reason: string }[];
  unresolved_conflicts: string[][];
  explanation_steps: string[];
  obligations: string[];
}

interface AnswerCell {
  question: string;
  state: string;
  detail: string;
}

const placeId = ref("");
const animal = ref("dog");
const serviceRole = ref("none");
const action = ref("enter");
const zoneId = ref("");

const result = ref<Explanation | null>(null);
const cells = ref<AnswerCell[]>([]);
const error = ref("");
const busy = ref("");

async function resolveRules() {
  error.value = "";
  result.value = null;
  busy.value = "resolve";
  try {
    result.value = await post<Explanation>(`/places/${placeId.value}/effective-rules`, {
      animal: animal.value,
      service_role: serviceRole.value,
      action: action.value,
      zone_id: zoneId.value || null,
    });
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

async function loadAnswerability() {
  error.value = "";
  cells.value = [];
  busy.value = "answer";
  try {
    const res = await get<{ place_id: string; cells: AnswerCell[] }>(`/places/${placeId.value}/answerability`);
    cells.value = res.cells;
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

function stateTone(state: string): string {
  switch (state) {
    case "ANSWERABLE":
      return "ok";
    case "PARTIAL":
      return "warn";
    case "UNANSWERABLE":
      return "restricted";
    default:
      return "unknown";
  }
}
</script>

<template>
  <h1>解析调试 · 可答性</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>

  <p class="muted">
    分层解析：法规 → 监管指引 → 模板 → 场所/分区覆盖 → 临时政策。
    输出 <span class="mono">compliance_state</span> ∈
    CONSISTENT / POTENTIAL_CONFLICT / REVIEW_REQUIRED / UNKNOWN，并给出逐步解释
    —— 不做「最后写入者获胜」。未知一律保持 UNKNOWN，不折算为允许或禁止。
  </p>

  <div class="panel">
    <h2>输入</h2>
    <div class="row">
      <div class="field"><label>场所 ID</label><input v-model="placeId" class="mono" placeholder="place uuid" /></div>
      <div class="field">
        <label>动物</label>
        <select v-model="animal">
          <option v-for="a in ANIMAL_SCOPES" :key="a" :value="a">{{ a }}</option>
        </select>
      </div>
      <div class="field">
        <label>服务角色</label>
        <select v-model="serviceRole">
          <option value="none">none（普通宠物）</option>
          <option value="service_dog">service_dog（服务犬，独立判定）</option>
        </select>
      </div>
      <div class="field"><label>动作</label><input v-model="action" placeholder="enter" /></div>
      <div class="field"><label>分区 ID（可选）</label><input v-model="zoneId" class="mono" placeholder="zone uuid" /></div>
    </div>
    <div class="actions" style="margin-top: 10px">
      <button class="primary" :disabled="busy === 'resolve' || !placeId" @click="resolveRules">解析生效规则</button>
      <button :disabled="busy === 'answer' || !placeId" @click="loadAnswerability">查询可答性</button>
    </div>
  </div>

  <div v-if="result" class="panel">
    <h2>解析结果</h2>
    <div class="stat-grid">
      <div class="stat"><div class="num">{{ result.effect }}</div><div class="label">生效效果</div></div>
      <div class="stat"><div class="num" style="font-size: 18px">{{ result.compliance_state }}</div><div class="label">合规状态</div></div>
      <div class="stat"><div class="num">{{ result.applicable_rules.length }}</div><div class="label">适用规则</div></div>
      <div class="stat"><div class="num">{{ result.unresolved_conflicts.length }}</div><div class="label">未解冲突</div></div>
    </div>

    <h2>逐步解释</h2>
    <div class="explain">
      <ol>
        <li v-for="(s, i) in result.explanation_steps" :key="i">{{ s }}</li>
        <li v-if="!result.explanation_steps.length" class="muted">无解释步骤</li>
      </ol>
    </div>

    <template v-if="result.suppressed.length">
      <h2>被抑制的规则</h2>
      <table class="compact">
        <thead><tr><th>规则</th><th>抑制原因</th></tr></thead>
        <tbody>
          <tr v-for="s in result.suppressed" :key="s.rule">
            <td class="mono">{{ shortId(s.rule) }}</td>
            <td>{{ s.reason }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template v-if="result.unresolved_conflicts.length">
      <h2>未解冲突（需人工复核）</h2>
      <table class="compact">
        <thead><tr><th>规则 A</th><th>规则 B</th></tr></thead>
        <tbody>
          <tr v-for="(pair, i) in result.unresolved_conflicts" :key="i">
            <td class="mono">{{ shortId(pair[0]) }}</td>
            <td class="mono">{{ shortId(pair[1]) }}</td>
          </tr>
        </tbody>
      </table>
    </template>

    <template v-if="result.obligations.length">
      <h2>附加义务</h2>
      <ul>
        <li v-for="(o, i) in result.obligations" :key="i">{{ o }}</li>
      </ul>
    </template>
  </div>

  <div v-if="cells.length" class="panel">
    <h2>可答性（Answerability）</h2>
    <p class="muted">每个问题给出状态与依据，明示「不可答」而非猜测。</p>
    <table class="compact">
      <thead><tr><th>问题</th><th>状态</th><th>依据</th></tr></thead>
      <tbody>
        <tr v-for="c in cells" :key="c.question">
          <td>{{ c.question }}</td>
          <td><span class="tag" :class="stateTone(c.state)">{{ c.state }}</span></td>
          <td class="muted">{{ c.detail }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
