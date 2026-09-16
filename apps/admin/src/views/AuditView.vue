<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, ApiError } from "../api";

interface Audit {
  id: string;
  actor_user_id: string | null;
  actor_role: string | null;
  action: string;
  target_type: string;
  target_id: string;
  before_state: unknown;
  after_state: unknown;
  request_id: string | null;
  created_at: string;
}

const items = ref<Audit[]>([]);
const error = ref("");
const targetType = ref("");

async function load() {
  error.value = "";
  try {
    items.value = (
      await page<Audit>("/admin/audit", {
        target_type: targetType.value || undefined,
        limit: 100,
      })
    ).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

onMounted(load);
</script>

<template>
  <h1>审计日志</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <div class="row" style="align-items: end">
      <div>
        <label for="fld-targettype">目标类型</label>
        <select v-model="targetType" id="fld-targettype" @change="load">
          <option value="">全部</option>
          <option value="place">place</option>
          <option value="zone">zone</option>
          <option value="access_rule">access_rule</option>
          <option value="operator_claim">operator_claim</option>
          <option value="dispute_case">dispute_case</option>
          <option value="jurisdiction_rule">jurisdiction_rule</option>
          <option value="source">source</option>
        </select>
      </div>
    </div>
  </div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>时间</th>
          <th>操作</th>
          <th>角色</th>
          <th>目标</th>
          <th>变更</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in items" :key="a.id">
          <td class="muted">{{ a.created_at.slice(0, 19).replace("T", " ") }}</td>
          <td>
            <span class="tag">{{ a.action }}</span>
          </td>
          <td>{{ a.actor_role ?? "—" }}</td>
          <td class="muted">{{ a.target_type }}:{{ a.target_id.slice(0, 8) }}</td>
          <td class="muted" style="max-width: 380px; overflow-wrap: anywhere">
            {{ JSON.stringify({ before: a.before_state, after: a.after_state }) }}
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="5" class="muted">暂无审计记录</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
