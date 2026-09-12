<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";
import { OBSERVATION_STATUSES, OBSERVATION_TRANSITIONS, statusTone } from "../v05";

interface ObsCandidate {
  id: string;
  evidence_bundle_id: string;
  source_id: string;
  place_id: string | null;
  zone_id: string | null;
  animal_scope: string | null;
  observed_action: string | null;
  spatial_context: string | null;
  occurred_at: string | null;
  extraction_method: string | null;
  raw_text: string | null;
  review_status: string;
  review_note: string | null;
  published_claim_id: string | null;
  derivation_confidence: number | null;
}

const items = ref<ObsCandidate[]>([]);
const total = ref(0);
const limit = 50;
const offset = ref(0);
const statusFilter = ref("");
const error = ref("");
const busy = ref("");
const note = ref<Record<string, string>>({});
const expanded = ref("");

async function load() {
  error.value = "";
  try {
    const res = await page<ObsCandidate>("/admin/observation-candidates", {
      limit,
      offset: offset.value,
    });
    items.value = res.items;
    total.value = res.total;
  } catch (e) {
    error.value = errText(e);
  }
}

function nextStates(c: ObsCandidate): string[] {
  return OBSERVATION_TRANSITIONS[c.review_status] ?? [];
}

async function move(c: ObsCandidate, target: string) {
  error.value = "";
  busy.value = `${c.id}:${target}`;
  try {
    await post(`/admin/observation-candidates/${c.id}/transition`, {
      target,
      note: note.value[c.id] || undefined,
    });
    note.value[c.id] = "";
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

/** Client-side filter by status; the API currently lists without a filter arg. */
const filtered = () =>
  statusFilter.value ? items.value.filter((i) => i.review_status === statusFilter.value) : items.value;

onMounted(load);
</script>

<template>
  <h1>观察候选</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>

  <p class="muted">
    观察是独立泳道：<span class="mono">ObservationCandidate</span> 与
    <span class="mono">RuleCandidate</span> 分表、分状态机。
    观察即使走到 <span class="mono">APPROVED / PUBLISHED</span>，也 <strong>绝不</strong> 写入 <span class="mono">AccessRule</span>
    —— 观察不能变成规则（Observation ≠ Rule）。
  </p>

  <div class="toolbar">
    <div class="field">
      <label>状态筛选</label>
      <select v-model="statusFilter">
        <option value="">全部</option>
        <option v-for="s in OBSERVATION_STATUSES" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    <button @click="offset = 0; load()">刷新</button>
  </div>

  <div class="panel">
    <table class="compact">
      <thead>
        <tr><th>候选</th><th>证据包</th><th>场所 / 分区</th><th>动物</th><th>观察行为</th><th>状态</th><th>操作</th></tr>
      </thead>
      <tbody>
        <template v-for="c in filtered()" :key="c.id">
          <tr>
            <td class="mono">{{ shortId(c.id) }}</td>
            <td class="mono">{{ shortId(c.evidence_bundle_id) }}</td>
            <td class="mono">P: {{ shortId(c.place_id) }}<br />Z: {{ shortId(c.zone_id) }}</td>
            <td>{{ c.animal_scope ?? "—" }}</td>
            <td>{{ c.observed_action ?? "—" }}</td>
            <td><span class="tag" :class="statusTone(c.review_status)">{{ c.review_status }}</span></td>
            <td>
              <div class="actions">
                <button @click="expanded = expanded === c.id ? '' : c.id">
                  {{ expanded === c.id ? "收起" : "详情" }}
                </button>
                <button
                  v-for="t in nextStates(c)"
                  :key="t"
                  :class="{ primary: t === 'REVIEW_PENDING' || t === 'APPROVED', danger: t === 'REJECTED' }"
                  :disabled="busy === `${c.id}:${t}`"
                  @click="move(c, t)"
                >→ {{ t }}</button>
              </div>
            </td>
          </tr>
          <tr v-if="expanded === c.id">
            <td colspan="7">
              <div class="explain">
                <dl class="kv">
                  <dt>来源 ID</dt><dd class="mono">{{ c.source_id }}</dd>
                  <dt>空间语境</dt><dd>{{ c.spatial_context || "—" }}</dd>
                  <dt>发生时间</dt><dd>{{ ts(c.occurred_at) }}</dd>
                  <dt>抽取方式</dt><dd class="mono">{{ c.extraction_method ?? "—" }}</dd>
                  <dt>推导置信</dt><dd class="mono">{{ c.derivation_confidence ?? "—" }}</dd>
                  <dt>已发布主张</dt><dd class="mono">{{ c.published_claim_id ?? "—" }}</dd>
                  <dt>复核备注</dt><dd>{{ c.review_note || "—" }}</dd>
                </dl>
                <template v-if="c.raw_text">
                  <div class="muted" style="margin-top: 8px">抽取原文</div>
                  <div class="quote">{{ c.raw_text }}</div>
                </template>
                <label>迁移备注（可选，写入审计）</label>
                <input v-model="note[c.id]" placeholder="例如：与同一场所三周内三次目击一致" />
                <p class="hint">审批后仅形成「观察主张」，不会生成准入规则。</p>
              </div>
            </td>
          </tr>
        </template>
        <tr v-if="!filtered().length"><td colspan="7" class="muted">暂无观察候选</td></tr>
      </tbody>
    </table>

    <div class="pager">
      <button :disabled="offset === 0" @click="offset = Math.max(0, offset - limit); load()">上一页</button>
      <span class="muted">第 {{ offset / limit + 1 }} 页 · 共 {{ total }} 条</span>
      <button :disabled="offset + limit >= total" @click="offset += limit; load()">下一页</button>
    </div>
  </div>
</template>
