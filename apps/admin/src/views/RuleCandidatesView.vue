<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";
import { CANDIDATE_STATUSES, CANDIDATE_TRANSITIONS, statusTone } from "../v05";
import {
  ANIMAL_SCOPE_LABELS,
  CANDIDATE_STATUS_LABELS,
  EXTRACTION_METHOD_LABELS,
  RULE_ACTION_LABELS,
  RULE_EFFECT_LABELS,
  label,
} from "../labels";

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

/**
 * Publishing is irreversible in product terms — it writes a normative rule that
 * real users will be told to rely on. Two clicks instead of one, with the second
 * click restyled and relabelled, so it can never be triggered by a stray tap on
 * a row of otherwise-ordinary buttons.
 */
const pending = ref("");

function guard(key: string): boolean {
  if (pending.value !== key) {
    pending.value = key;
    return false;
  }
  pending.value = "";
  return true;
}

async function publish(c: Candidate) {
  if (!guard(`${c.id}:PUBLISH`)) return;
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

/** Rejecting discards human review work, so it gets the same two-click guard. */
async function reject(c: Candidate) {
  if (!guard(`${c.id}:REJECTED`)) return;
  await move(c, "REJECTED");
}

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / limit)));

/**
 * Place names for the queue, loaded once.
 *
 * Deliberately non-fatal: if this call fails the queue still renders with short
 * ids rather than erroring, because reviewability matters more than the label.
 */
const placeNames = ref<Record<string, string>>({});

async function loadPlaces() {
  try {
    const res = await page<{ id: string; canonical_name: string }>("/places", { limit: 100 });
    const map: Record<string, string> = {};
    for (const p of res.items) map[p.id] = p.canonical_name;
    placeNames.value = map;
  } catch {
    placeNames.value = {};
  }
}

function placeName(id: string | null): string {
  if (!id) return "未归属具体场所（属地规则）";
  return placeNames.value[id] ?? `未知场所 ${shortId(id)}`;
}

onMounted(() => {
  void loadPlaces();
  void load();
});
</script>

<template>
  <h1>规则候选</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>

  <p class="muted">
    AI / OCR / 监控 / 导入 的产物一律先进候选，永不直接写规则。 状态机 DISCOVERED → EXTRACTED →
    MATCH_PENDING → REVIEW_PENDING → APPROVED → PUBLISHED， 只有
    <span class="mono">APPROVED</span> 可经
    <span class="mono">/publish</span> 落入规范性规则集（ADR-005）。
  </p>

  <div class="toolbar">
    <div class="field">
      <label for="fld-statusfilter">状态筛选</label>
      <select v-model="statusFilter" id="fld-statusfilter" @change="load">
        <option value="">全部</option>
        <option v-for="s in CANDIDATE_STATUSES" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    <button
      @click="
        offset = 0;
        load();
      "
    >
      刷新
    </button>
  </div>

  <div class="panel">
    <table class="compact">
      <thead>
        <tr>
          <th>候选</th>
          <th>归属</th>
          <th>作用域</th>
          <th>动作 / 效果</th>
          <th>抽取</th>
          <th>置信</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="c in items" :key="c.id">
          <tr>
            <td class="mono">{{ shortId(c.id) }}</td>
            <!-- Name, not an opaque id: "P: 89bd859e…" told a reviewer nothing,
                 and a null zone rendered a bare "Z:" with no value at all. -->
            <td>
              <div>{{ placeName(c.place_id) }}</div>
              <div v-if="c.zone_id" class="muted">分区 {{ shortId(c.zone_id) }}</div>
            </td>
            <td>{{ label(ANIMAL_SCOPE_LABELS, c.animal_scope) }}</td>
            <td>
              {{ label(RULE_ACTION_LABELS, c.action) }} /
              <span :class="{ muted: !c.effect }">{{ label(RULE_EFFECT_LABELS, c.effect) }}</span>
            </td>
            <td class="mono">
              {{ label(EXTRACTION_METHOD_LABELS, c.extraction_method)
              }}<span v-if="c.extraction_provider"> · {{ c.extraction_provider }}</span>
            </td>
            <td class="mono">{{ c.internal_confidence ?? "—" }}</td>
            <td>
              <span class="tag" :class="statusTone(c.review_status)">
                {{ label(CANDIDATE_STATUS_LABELS, c.review_status) }}
              </span>
            </td>
            <td>
              <div class="actions">
                <button @click="expanded = expanded === c.id ? '' : c.id">
                  {{ expanded === c.id ? "收起" : "详情" }}
                </button>
                <template v-for="t in nextStates(c)" :key="t">
                  <button
                    v-if="t === 'REJECTED'"
                    :class="pending === `${c.id}:REJECTED` ? 'danger' : ''"
                    :disabled="busy === `${c.id}:${t}`"
                    @click="reject(c)"
                  >
                    {{ pending === `${c.id}:REJECTED` ? "再点一次确认驳回" : "→ REJECTED" }}
                  </button>
                  <button
                    v-else
                    :class="{
                      primary: t === 'APPROVED' || t === 'REVIEW_PENDING',
                    }"
                    :disabled="busy === `${c.id}:${t}`"
                    @click="move(c, t)"
                  >
                    → {{ t }}
                  </button>
                </template>
                <button
                  v-if="c.review_status === 'APPROVED'"
                  :class="pending === `${c.id}:PUBLISH` ? 'danger' : 'primary'"
                  :disabled="busy === `${c.id}:PUBLISH`"
                  @click="publish(c)"
                >
                  {{ pending === `${c.id}:PUBLISH` ? "再点一次确认发布" : "发布为规则" }}
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="expanded === c.id">
            <td colspan="8">
              <div class="explain">
                <dl class="kv">
                  <dt>创建时间</dt>
                  <dd>{{ ts(c.created_at) }}</dd>
                  <dt>来源 ID</dt>
                  <dd class="mono">{{ c.source_id }}</dd>
                  <dt>候选条件</dt>
                  <dd class="mono">
                    {{
                      c.proposed_conditions?.length ? JSON.stringify(c.proposed_conditions) : "—"
                    }}
                  </dd>
                  <dt>已发布规则</dt>
                  <dd class="mono">{{ c.published_rule_id ?? "未发布" }}</dd>
                  <dt>复核备注</dt>
                  <dd>{{ c.review_note || "—" }}</dd>
                </dl>
                <template v-if="c.raw_text">
                  <div style="margin-top: 8px" class="muted">抽取原文</div>
                  <div class="quote">{{ c.raw_text }}</div>
                </template>
                <label for="fld-note-c-id">迁移备注（可选，写入审计）</label>
                <input
                  v-model="note[c.id]"
                  id="fld-note-c-id"
                  placeholder="例如：现场牌面与官网冲突，按现场采信"
                />
              </div>
            </td>
          </tr>
        </template>
        <tr v-if="!items.length">
          <td colspan="8" class="muted">暂无候选</td>
        </tr>
      </tbody>
    </table>

    <div class="pager">
      <button
        :disabled="offset === 0"
        @click="
          offset = Math.max(0, offset - limit);
          load();
        "
      >
        上一页
      </button>
      <span class="muted"
        >第 {{ offset / limit + 1 }} / {{ pageCount }} 页 · 共 {{ total }} 条</span
      >
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
  </div>
</template>
