<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, ApiError } from "../api";

interface Claim {
  id: string;
  place_id: string;
  operator_id: string;
  claimant_user_id: string;
  status: string;
  verification_method: string | null;
  evidence_refs: Record<string, unknown> | null;
  rejection_reason: string | null;
  created_at: string;
}

const items = ref<Claim[]>([]);
const error = ref("");
const statusFilter = ref("");

async function load() {
  error.value = "";
  try {
    items.value = (
      await page<Claim>("/operator-claims", {
        status: statusFilter.value || undefined,
        limit: 100,
      })
    ).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function review(c: Claim, approve: boolean) {
  error.value = "";
  try {
    await post(`/operator-claims/${c.id}/review`, {
      approve,
      rejection_reason: approve ? null : "演示：证明材料不足",
    });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

onMounted(load);
</script>

<template>
  <h1>管理方认领审核</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <div class="row" style="align-items: end">
      <div>
        <label>状态</label>
        <select v-model="statusFilter" @change="load">
          <option value="">全部</option>
          <option value="submitted">submitted</option>
          <option value="verifying">verifying</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="revoked">revoked</option>
        </select>
      </div>
    </div>
  </div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>场所</th>
          <th>管理方</th>
          <th>认证方式</th>
          <th>材料</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in items" :key="c.id">
          <td class="muted">{{ c.place_id.slice(0, 8) }}…</td>
          <td class="muted">{{ c.operator_id.slice(0, 8) }}…</td>
          <td>{{ c.verification_method ?? "—" }}</td>
          <td class="muted">
            {{ c.evidence_refs ? JSON.stringify(c.evidence_refs).slice(0, 40) : "—" }}
          </td>
          <td>
            <span
              class="tag"
              :class="{ ok: c.status === 'approved', warn: c.status === 'submitted' }"
              >{{ c.status }}</span
            >
          </td>
          <td>
            <template v-if="c.status === 'submitted' || c.status === 'verifying'">
              <button class="primary" @click="review(c, true)">批准</button>
              <button class="danger" style="margin-left: 6px" @click="review(c, false)">
                驳回
              </button>
            </template>
            <span v-else class="muted">{{ c.rejection_reason ?? "已办结" }}</span>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="6" class="muted">暂无认领</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
