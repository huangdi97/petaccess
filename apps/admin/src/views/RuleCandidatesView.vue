<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";
import { CANDIDATE_STATUSES, CANDIDATE_TRANSITIONS, statusTone } from "../v05";

interface Candidate {
  id: string;
  source_id: string;
  place_id: string | null;
  zone_id: string | null;
  animal_scope: string | null;
  action: string | null;
  effect: string | null;
  proposed_conditions: unknown[] | null;
  extraction_method: string;
  extraction_provider: string | null;
  internal_confidence: number | null;
  raw_text: string | null;
  review_status: string;
  review_note: string | null;
  published_rule_id: string | null;
  created_at: string | null;
}

const items = ref<Candidate[]>([]);
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
    const res = await page<Candidate>("/admin/candidates", {
      limit,
      offset: offset.value,
      review_status: statusFilter.value || undefined,
    });
    items.value = res.items;
    total.value = res.total;
  } catch (e) {
    error.value = errText(e);
  }
}

/** Only the transitions the API will actually accept for this status. */
function nextStates(c: Candidate): string[] {
  return CANDIDATE_TRANSITIONS[c.review_status] ?? [];
}

async function move(c: Candidate, target: string) {
  error.value = "";
  busy.value = `${c.id}:${target}`;
  try {
    await post(`/admin/candidates/${c.id}/transition`, {
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

async function publish(c: Candidate) {
  error.value = "";
  busy.value = `${c.id}:PUBLISH`;
  try {
    await post(`/admin/candidates/${c.id}/publish`, {});
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / limit)));

onMounted(load);
</script>

<template>
  <h1>规则候选</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>

  <p class="muted">
    AI / OCR / 监控 / 导入 的产物一律先进候选，永不直接写规则。
    状态机 DISCOVERED → EXTRACTED → MATCH_PENDING → REVIEW_PENDING → APPROVED → PUBLISHED，
    只有 <span class="mono">APPROVED</span> 可经 <span class="mono">/publish</span> 落入规范性规则集（ADR-005）。
  </p>

  <div class="toolbar">
    <div class="field">
      <label>状态筛选</label>
      <select v-model="statusFilter" @change="load">
        <option value="">全部</option>
        <option v-for="s in CANDIDATE_STATUSES" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    <button @click="offset = 0; load()">刷新</button>
  </div>

  <div class="panel">
    <table class="compact">
      <thead>
        <tr>
          <th>候选</th><th>归属</th><th>作用域</th><th>动作 / 效果</th>
          <th>抽取</th><th>置信</th><th>状态</th><th>操作</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="c in items" :key="c.id">
          <tr>
            <td class="mono">{{ shortId(c.id) }}</td>
            <td class="mono">
              P: {{ shortId(c.place_id) }}<br />
              Z: {{ shortId(c.zone_id) }}
            </td>
            <td>{{ c.animal_scope ?? "—" }}</td>
            <td>{{ c.action ?? "—" }} / <span :class="{ muted: !c.effect }">{{ c.effect ?? "—" }}</span></td>
            <td class="mono">{{ c.extraction_method }}<span v-if="c.extraction_provider"> · {{ c.extraction_provider }}</span></td>
            <td class="mono">{{ c.internal_confidence ?? "—" }}</td>
            <td><span class="tag" :class="statusTone(c.review_status)">{{ c.review_status }}</span></td>
            <td>
              <div class="actions">
                <button @click="expanded = expanded === c.id ? '' : c.id">
                  {{ expanded === c.id ? "收起" : "详情" }}
                </button>
                <button
                  v-for="t in nextStates(c)"
                  :key="t"
                  :class="{ primary: t === 'APPROVED' || t === 'REVIEW_PENDING', danger: t === 'REJECTED' }"
                  :disabled="busy === `${c.id}:${t}`"
                  @click="move(c, t)"
                >→ {{ t }}</button>
                <button
                  v-if="c.review_status === 'APPROVED'"
                  class="primary"
                  :disabled="busy === `${c.id}:PUBLISH`"
                  @click="publish(c)"
                >发布为规则</button>
              </div>
            </td>
          </tr>
          <tr v-if="expanded === c.id">
            <td colspan="8">
              <div class="explain">
                <dl class="kv">
                  <dt>创建时间</dt><dd>{{ ts(c.created_at) }}</dd>
                  <dt>来源 ID</dt><dd class="mono">{{ c.source_id }}</dd>
                  <dt>候选条件</dt><dd class="mono">{{ c.proposed_conditions?.length ? JSON.stringify(c.proposed_conditions) : "—" }}</dd>
                  <dt>已发布规则</dt><dd class="mono">{{ c.published_rule_id ?? "未发布" }}</dd>
                  <dt>复核备注</dt><dd>{{ c.review_note || "—" }}</dd>
                </dl>
                <template v-if="c.raw_text">
                  <div style="margin-top: 8px" class="muted">抽取原文</div>
                  <div class="quote">{{ c.raw_text }}</div>
                </template>
                <label>迁移备注（可选，写入审计）</label>
                <input v-model="note[c.id]" placeholder="例如：现场牌面与官网冲突，按现场采信" />
              </div>
            </td>
          </tr>
        </template>
        <tr v-if="!items.length"><td colspan="8" class="muted">暂无候选</td></tr>
      </tbody>
    </table>

    <div class="pager">
      <button :disabled="offset === 0" @click="offset = Math.max(0, offset - limit); load()">上一页</button>
      <span class="muted">第 {{ offset / limit + 1 }} / {{ pageCount }} 页 · 共 {{ total }} 条</span>
      <button :disabled="offset + limit >= total" @click="offset += limit; load()">下一页</button>
    </div>
  </div>
</template>
