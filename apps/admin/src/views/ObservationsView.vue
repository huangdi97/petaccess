<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, ApiError } from "../api";

interface Observation {
  id: string; place_id: string; occurred_at: string; animal_scope: string;
  observed_action: string; staff_action: string; place_confidence: string;
  dispute_status: string; withdrawn_at: string | null; note: string | null;
  proximity_verified: boolean;
}

const items = ref<Observation[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    items.value = (await page<Observation>("/admin/observations", { limit: 100 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
});
</script>

<template>
  <h1>观察记录（贡献队列）</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <p class="muted">
      观察（Observation）与规则（Rule）并存，但永不自动变成规则（ADR-004）；
      "没人阻止"不会被解释为"允许"。管理方对观察有异议必须走「异议」流程。
    </p>
    <table>
      <thead><tr><th>时间</th><th>动物</th><th>行为</th><th>员工动作</th><th>置信</th><th>现场核验</th><th>争议</th><th>说明</th></tr></thead>
      <tbody>
        <tr v-for="o in items" :key="o.id">
          <td class="muted">{{ o.occurred_at.slice(0, 10) }}</td>
          <td>{{ o.animal_scope }}</td>
          <td>{{ o.observed_action }}</td>
          <td>{{ o.staff_action }}</td>
          <td>{{ o.place_confidence }}</td>
          <td>{{ o.proximity_verified ? "✓" : "—" }}</td>
          <td>
            <span class="tag" :class="{ warn: o.dispute_status !== 'none' }">{{ o.dispute_status }}</span>
            <span v-if="o.withdrawn_at" class="muted">（已撤回）</span>
          </td>
          <td class="muted">{{ o.note ?? "—" }}</td>
        </tr>
        <tr v-if="!items.length"><td colspan="8" class="muted">暂无观察记录</td></tr>
      </tbody>
    </table>
  </div>
</template>
