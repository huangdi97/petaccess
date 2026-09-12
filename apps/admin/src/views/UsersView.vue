<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, ApiError } from "../api";

interface UserRow {
  id: string;
  display_name: string;
  email: string | null;
  role: string;
  status: string;
  created_at: string;
}

const items = ref<UserRow[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    items.value = (await page<UserRow>("/admin/users", { limit: 100 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
});
</script>

<template>
  <h1>用户</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>名称</th>
          <th>邮箱</th>
          <th>角色</th>
          <th>状态</th>
          <th>注册时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in items" :key="u.id">
          <td>{{ u.display_name }}</td>
          <td class="muted">{{ u.email ?? "—" }}</td>
          <td>
            <span class="tag" :class="{ ok: u.role === 'admin' }">{{ u.role }}</span>
          </td>
          <td>{{ u.status }}</td>
          <td class="muted">{{ u.created_at.slice(0, 10) }}</td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="5" class="muted">暂无用户</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
