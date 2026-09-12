<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, ApiError } from "../api";

interface QueueItem {
  id: string;
  place_id: string;
  reported_at: string;
  evidence_support: unknown;
  state: string;
}

const items = ref<QueueItem[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    items.value = (await page<QueueItem>("/admin/ai-queue", { limit: 100 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
});
</script>

<template>
  <h1>AI 抽取队列</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <p class="muted">
      携带证据（如告示照片）的观察记录进入 OCR/结构化人工复核队列； AI
      抽取结果仅供参考，规则生效必须经过人工结构化（设计 #20/#21）。
    </p>
    <table>
      <thead>
        <tr>
          <th>观察</th>
          <th>场所</th>
          <th>报告时间</th>
          <th>状态</th>
          <th>证据</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="q in items" :key="q.id">
          <td class="muted">{{ q.id.slice(0, 8) }}…</td>
          <td class="muted">{{ q.place_id.slice(0, 8) }}…</td>
          <td>{{ q.reported_at.slice(0, 10) }}</td>
          <td>
            <span class="tag warn">{{ q.state }}</span>
          </td>
          <td class="muted">{{ JSON.stringify(q.evidence_support).slice(0, 60) }}</td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="5" class="muted">队列为空</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
