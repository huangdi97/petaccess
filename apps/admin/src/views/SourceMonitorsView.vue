<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, errText, shortId, ts } from "../api";

interface Monitor {
  id: string;
  source_id: string;
  url: string;
  status: string;
  failure_count: number;
  content_hash: string;
  last_checked_at: string | null;
  last_changed_at: string | null;
  place_id: string | null;
}

interface CheckResult {
  outcome: string;
  artifact_id?: string | null;
  evidence_bundle_id?: string | null;
  candidate_id?: string | null;
}

const items = ref<Monitor[]>([]);
const total = ref(0);
const error = ref("");
const info = ref("");
const busy = ref("");

const form = ref({ source_id: "", url: "", schedule_minutes: 1440, place_id: "" });

async function load() {
  error.value = "";
  try {
    const res = await page<Monitor>("/admin/monitors", { limit: 100 });
    items.value = res.items;
    total.value = res.total;
  } catch (e) {
    error.value = errText(e);
  }
}

async function createMonitor() {
  error.value = "";
  info.value = "";
  busy.value = "create";
  try {
    const payload: Record<string, unknown> = {
      source_id: form.value.source_id,
      url: form.value.url,
      schedule_minutes: Number(form.value.schedule_minutes) || 1440,
    };
    if (form.value.place_id) payload.place_id = form.value.place_id;
    const created = await post<{ id: string }>("/admin/monitors", payload);
    info.value = `已创建监控 ${created.id.slice(0, 8)}…`;
    form.value.url = "";
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

async function sweep(m: Monitor) {
  error.value = "";
  info.value = "";
  busy.value = m.id;
  try {
    const res = await post<CheckResult>(`/admin/monitors/${m.id}/check`, {});
    const parts = [`结果：${res.outcome}`];
    if (res.artifact_id) parts.push(`原件 ${res.artifact_id.slice(0, 8)}…`);
    if (res.evidence_bundle_id) parts.push(`证据包 ${res.evidence_bundle_id.slice(0, 8)}…`);
    if (res.candidate_id) parts.push(`候选 ${res.candidate_id.slice(0, 8)}…`);
    if (res.outcome === "changed" && !res.candidate_id) {
      parts.push("（内容已变化但未产生候选，请检查来源绑定）");
    }
    info.value = parts.join(" · ");
    await load();
  } catch (e) {
    error.value = errText(e);
  } finally {
    busy.value = "";
  }
}

onMounted(load);
</script>

<template>
  <h1>来源监控</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div v-if="info" class="ok-banner">{{ info }}</div>

  <p class="muted">
    定时抓取来源页面并按内容哈希比对。检测到变化时，抓取内容会先冻结为证据原件与证据包，再生成规则候选取人复核
    —— 监控本身不写规则。
  </p>

  <div class="panel">
    <h2>新建监控</h2>
    <div class="row">
      <div class="field">
        <label>来源 ID</label>
        <input v-model="form.source_id" class="mono" placeholder="source uuid" />
      </div>
      <div class="field">
        <label>监控 URL</label>
        <input v-model="form.url" placeholder="https://…" />
      </div>
      <div class="field">
        <label>周期（分钟）</label>
        <input v-model.number="form.schedule_minutes" type="number" min="5" />
      </div>
      <div class="field">
        <label>关联场所（可选）</label>
        <input v-model="form.place_id" class="mono" placeholder="place uuid" />
      </div>
    </div>
    <button
      class="primary"
      style="margin-top: 10px"
      :disabled="busy === 'create' || !form.source_id || !form.url"
      @click="createMonitor"
    >
      创建监控
    </button>
  </div>

  <div class="panel">
    <h2>监控列表（{{ total }}）</h2>
    <table class="compact">
      <thead>
        <tr>
          <th>ID</th>
          <th>URL</th>
          <th>来源</th>
          <th>状态</th>
          <th>失败</th>
          <th>哈希</th>
          <th>最近检查</th>
          <th>最近变化</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in items" :key="m.id">
          <td class="mono">{{ shortId(m.id) }}</td>
          <td class="mono" style="max-width: 260px; overflow: hidden; text-overflow: ellipsis">
            {{ m.url }}
          </td>
          <td class="mono">{{ shortId(m.source_id) }}</td>
          <td>
            <span
              class="tag"
              :class="m.status === 'active' ? 'ok' : m.status === 'failing' ? 'restricted' : 'warn'"
              >{{ m.status }}</span
            >
          </td>
          <td class="mono">{{ m.failure_count }}</td>
          <td class="mono">{{ m.content_hash || "—" }}</td>
          <td class="muted">{{ ts(m.last_checked_at) }}</td>
          <td class="muted">{{ ts(m.last_changed_at) }}</td>
          <td>
            <button class="primary" :disabled="busy === m.id" @click="sweep(m)">
              {{ busy === m.id ? "检查中…" : "立即检查" }}
            </button>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="9" class="muted">暂无监控</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
