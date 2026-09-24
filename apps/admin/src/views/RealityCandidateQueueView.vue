<script setup lang="ts">
/**
 * RealityCandidateQueue (v0.9-R1 §7.4 / AC11).
 *
 * The human-only reality review surface. `reality_decision` is written by a
 * human here — the AI layer never calls this endpoint. VERIFIED /
 * VERIFIED_WITH_NOTE publish the claim; HOLD / REJECTED keep it unpublished.
 */
import { onMounted, ref } from "vue";
import { errText, page, post, ts } from "../api";

interface RealityCandidate {
  id: string;
  candidate_type: string;
  place_id: string;
  zone_id: string | null;
  source_id: string | null;
  evidence_bundle_id: string | null;
  animal_scope: string | null;
  observed_at: string | null;
  captured_at: string | null;
  review_status: string;
  reality_decision: string | null;
  reviewer: string | null;
  decided_at: string | null;
  decision_note: string | null;
  freshness_state: string | null;
  verification_status: string;
  payload: Record<string, unknown> | null;
  published_claim_id: string | null;
  published_at: string | null;
  created_at: string;
}

const TYPE_LABELS: Record<string, string> = {
  observed_presence: "动物出现观察",
  staff_response: "工作人员处理",
  animal_facility: "动物设施",
};

const DECISIONS = [
  { value: "VERIFIED", label: "已核实（发布）" },
  { value: "VERIFIED_WITH_NOTE", label: "已核实（附注，发布）" },
  { value: "HOLD", label: "挂起（不发布）" },
  { value: "REJECTED", label: "拒绝（不发布）" },
];

const items = ref<RealityCandidate[]>([]);
const total = ref(0);
const limit = 50;
const offset = ref(0);
const typeFilter = ref("");
const statusFilter = ref("");
const error = ref("");
const busy = ref("");
const notes = ref<Record<string, string>>({});
const expanded = ref("");
const flash = ref("");

async function load() {
  error.value = "";
  try {
    const res = await page<RealityCandidate>("/admin/reality/candidates", {
      limit,
      offset: offset.value,
      candidate_type: typeFilter.value || undefined,
      review_status: statusFilter.value || undefined,
    });
    items.value = res.items;
    total.value = res.total;
  } catch (e) {
    error.value = errText(e);
  }
}

/** The human-only decision endpoint. AI never calls it. */
async function decide(c: RealityCandidate, decision: string) {
  error.value = "";
  busy.value = `${c.id}:${decision}`;
  try {
    await post(`/admin/reality/candidates/${c.id}/decision`, {
      reality_decision: decision,
      decision_note: notes.value[c.id] || undefined,
    });
    flash.value = `${TYPE_LABELS[c.candidate_type] ?? c.candidate_type} 已按 ${decision} 处理`;
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

const payloadLines = (c: RealityCandidate) => {
  const p = c.payload ?? {};
  return Object.entries(p)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`);
};

onMounted(load);
</script>

<template>
  <section>
    <h1>Reality Candidate Queue</h1>
    <p class="muted">
      人工审核队列 —— 裁决仅由具名人类评审员做出（AI 永不写 reality_decision）。 VERIFIED /
      VERIFIED_WITH_NOTE 发布 claim；HOLD / REJECTED 不发布。
    </p>

    <div class="toolbar">
      <select v-model="typeFilter" @change="load">
        <option value="">全部类型</option>
        <option v-for="(l, t) in TYPE_LABELS" :key="t" :value="t">{{ l }}</option>
      </select>
      <select v-model="statusFilter" @change="load">
        <option value="">全部状态</option>
        <option value="REVIEW_PENDING">待审核</option>
        <option value="REVIEWED">已审核</option>
      </select>
      <span class="muted">共 {{ total }} 条</span>
    </div>

    <div v-if="flash" class="ok">{{ flash }}</div>
    <div v-if="error" class="error">{{ error }}</div>

    <table>
      <thead>
        <tr>
          <th></th>
          <th>类型</th>
          <th>场所</th>
          <th>范围/时间</th>
          <th>状态</th>
          <th>裁决</th>
          <th>审核人</th>
          <th>payload 摘要</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in items" :key="c.id">
          <td>
            <button class="link" @click="expanded = expanded === c.id ? '' : c.id">
              {{ expanded === c.id ? "▾" : "▸" }}
            </button>
          </td>
          <td>{{ TYPE_LABELS[c.candidate_type] ?? c.candidate_type }}</td>
          <td>{{ c.place_id }}</td>
          <td>
            <div>{{ c.animal_scope ?? "—" }}</div>
            <div class="muted">{{ ts(c.observed_at) }}</div>
          </td>
          <td>{{ c.review_status }}</td>
          <td>{{ c.reality_decision ?? "—" }}</td>
          <td>{{ c.reviewer ?? "—" }}</td>
          <td>
            <div v-for="(line, i) in payloadLines(c).slice(0, 3)" :key="i" class="muted small">
              {{ line }}
            </div>
          </td>
          <td>
            <div v-if="c.review_status !== 'REVIEWED'" class="row">
              <select
                :value="''"
                @change="(e) => e.target && decide(c, (e.target as HTMLSelectElement).value)"
              >
                <option value="" disabled>选择裁决…</option>
                <option v-for="d in DECISIONS" :key="d.value" :value="d.value">
                  {{ d.label }}
                </option>
              </select>
            </div>
            <span v-else class="muted">已处理</span>
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="9" class="muted">队列为空（当前筛选条件下）</td>
        </tr>
      </tbody>
    </table>

    <div v-if="expanded" class="detail">
      <h3>
        候选详情（{{ (items.find((i) => i.id === expanded) as RealityCandidate | undefined)?.id }}）
      </h3>
      <template v-if="items.find((i) => i.id === expanded)">
        <div class="grid">
          <div><b>review_status</b>: {{ items.find((i) => i.id === expanded)!.review_status }}</div>
          <div>
            <b>verification_status</b>:
            {{ items.find((i) => i.id === expanded)!.verification_status }}
          </div>
          <div>
            <b>freshness_state</b>:
            {{ items.find((i) => i.id === expanded)!.freshness_state ?? "—" }}
          </div>
          <div><b>zone_id</b>: {{ items.find((i) => i.id === expanded)!.zone_id ?? "—" }}</div>
          <div><b>source_id</b>: {{ items.find((i) => i.id === expanded)!.source_id ?? "—" }}</div>
          <div>
            <b>evidence_bundle_id</b>:
            {{ items.find((i) => i.id === expanded)!.evidence_bundle_id ?? "—" }}
          </div>
          <div>
            <b>published_claim_id</b>:
            {{ items.find((i) => i.id === expanded)!.published_claim_id ?? "—" }}
          </div>
          <div>
            <b>published_at</b>: {{ ts(items.find((i) => i.id === expanded)!.published_at) }}
          </div>
          <div>
            <b>decision_note</b>: {{ items.find((i) => i.id === expanded)!.decision_note ?? "—" }}
          </div>
        </div>
        <h4>Payload</h4>
        <pre class="code">{{
          JSON.stringify(items.find((i) => i.id === expanded)!.payload ?? {}, null, 2)
        }}</pre>
        <h4>审核备注</h4>
        <input v-model="notes[expanded]" placeholder="决策附注（VERIFIED_WITH_NOTE 必填理由）" />
      </template>
    </div>

    <div class="pager">
      <button
        :disabled="offset === 0"
        @click="
          offset -= limit;
          load();
        "
      >
        上一页
      </button>
      <button
        :disabled="offset + limit >= total"
        @click="
          offset += limit;
          load();
        "
      >
        下一页
      </button>
    </div>
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 12px 0;
}
.row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.small {
  font-size: 12px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}
.code {
  background: var(--pa-color-bg-app);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 10px;
  overflow-x: auto;
  font-size: 12px;
}
.detail {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
}
input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
}
.pager {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
.ok {
  color: var(--ok);
  background: var(--pa-color-status-allowed-bg);
  padding: 8px 12px;
  border-radius: 6px;
}
.error {
  color: var(--danger);
  background: var(--pa-color-status-restricted-bg);
  padding: 8px 12px;
  border-radius: 6px;
}
.muted {
  color: var(--muted);
}
button.link {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
}
</style>
