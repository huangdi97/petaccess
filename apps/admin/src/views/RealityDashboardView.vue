<script setup lang="ts">
/**
 * Reality Dashboard (v0.9-R1 §13 / AC11).
 *
 * The reality layer's operating picture: candidate queue volume by state and
 * type, published claim counts, and per-type review surfaces. All numbers come
 * from the real admin APIs — no fabricated "evidence" is ever displayed.
 */
import { onMounted, ref } from "vue";
import { errText, page, ts } from "../api";

interface RealityCandidate {
  id: string;
  candidate_type: string;
  place_id: string;
  zone_id: string | null;
  animal_scope: string | null;
  observed_at: string | null;
  review_status: string;
  reality_decision: string | null;
  reviewer: string | null;
  decided_at: string | null;
  freshness_state: string | null;
  verification_status: string;
  published_claim_id: string | null;
  created_at: string;
}

const candidates = ref<RealityCandidate[]>([]);
const total = ref(0);
const error = ref("");
const loading = ref(true);

const TYPE_LABELS: Record<string, string> = {
  observed_presence: "动物出现观察",
  staff_response: "工作人员处理",
  animal_facility: "动物设施",
};

const STATUS_LABELS: Record<string, string> = {
  REVIEW_PENDING: "待审核",
  REVIEWED: "已审核",
};

const DECISION_LABELS: Record<string, string> = {
  VERIFIED: "已核实",
  VERIFIED_WITH_NOTE: "已核实（附注）",
  HOLD: "挂起",
  REJECTED: "拒绝",
};

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const res = await page<RealityCandidate>("/admin/reality/candidates", { limit: 100 });
    candidates.value = res.items;
    total.value = res.total;
  } catch (e) {
    error.value = errText(e);
  } finally {
    loading.value = false;
  }
}

const byType = (t: string) => candidates.value.filter((c) => c.candidate_type === t).length;
const pending = () => candidates.value.filter((c) => c.review_status === "REVIEW_PENDING").length;
const verified = () =>
  candidates.value.filter(
    (c) => c.reality_decision === "VERIFIED" || c.reality_decision === "VERIFIED_WITH_NOTE",
  ).length;
const published = () =>
  candidates.value.filter((c) => c.published_claim_id != null && c.published_claim_id !== "").length;

onMounted(load);
</script>

<template>
  <section class="stack">
    <h1>Reality Dashboard</h1>
    <p class="muted">
      现实层（现场观察）运营总览 —— 人工审核队列与已发布 claim。所有数据来自真实 API；
      没有任何“证据”是自动生成的。
    </p>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="loading" class="muted">加载中…</div>

    <template v-else>
      <div class="cards">
        <div class="card">
          <div class="num">{{ total }}</div>
          <div class="lbl">候选总数</div>
        </div>
        <div class="card">
          <div class="num">{{ pending() }}</div>
          <div class="lbl">待审核（REVIEW_PENDING）</div>
        </div>
        <div class="card">
          <div class="num">{{ verified() }}</div>
          <div class="lbl">已核实（VERIFIED*）</div>
        </div>
        <div class="card">
          <div class="num">{{ published() }}</div>
          <div class="lbl">已发布 claim</div>
        </div>
      </div>

      <h2>按类型分布</h2>
      <table>
        <thead>
          <tr>
            <th>候选类型</th>
            <th>数量</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(t, i) in Object.keys(TYPE_LABELS)" :key="i">
            <td>{{ TYPE_LABELS[t] }}</td>
            <td>{{ byType(t) }}</td>
          </tr>
        </tbody>
      </table>

      <h2>最近候选（前 20）</h2>
      <table>
        <thead>
          <tr>
            <th>类型</th>
            <th>场所</th>
            <th>动物范围</th>
            <th>观察时间</th>
            <th>状态</th>
            <th>裁决</th>
            <th>审核人</th>
            <th>freshness</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in candidates.slice(0, 20)" :key="c.id">
            <td>{{ TYPE_LABELS[c.candidate_type] ?? c.candidate_type }}</td>
            <td>{{ c.place_id }}</td>
            <td>{{ c.animal_scope ?? "—" }}</td>
            <td>{{ ts(c.observed_at) }}</td>
            <td>{{ STATUS_LABELS[c.review_status] ?? c.review_status }}</td>
            <td>{{ c.reality_decision ? (DECISION_LABELS[c.reality_decision] ?? c.reality_decision) : "—" }}</td>
            <td>{{ c.reviewer ?? "—" }}</td>
            <td>{{ c.freshness_state ?? "—" }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<style scoped>
.stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}
.num {
  font-size: 28px;
  font-weight: 700;
}
.lbl {
  font-size: 13px;
  color: var(--muted);
  margin-top: 4px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th,
td {
  border: 1px solid var(--line);
  padding: 6px 8px;
  text-align: left;
}
.muted {
  color: var(--muted);
}
.error {
  color: var(--danger);
  background: var(--pa-color-status-restricted-bg);
  padding: 8px 12px;
  border-radius: 6px;
}
</style>
