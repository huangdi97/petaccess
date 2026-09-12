<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, patch, ApiError } from "../api";

interface Conflict {
  rule_id: string;
  place_id: string | null;
  zone_id: string | null;
  effect: string;
  status: string;
  source_id: string;
}

const items = ref<Conflict[]>([]);
const error = ref("");

async function load() {
  error.value = "";
  try {
    items.value = (await page<Conflict>("/admin/conflicts", { limit: 100 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function restore(c: Conflict) {
  error.value = "";
  try {
    await patch(`/rules/${c.rule_id}`, { status: "current" });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function archive(c: Conflict) {
  error.value = "";
  try {
    await patch(`/rules/${c.rule_id}`, { status: "archived" });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

onMounted(load);
</script>

<template>
  <h1>冲突复核</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <p class="muted">
    争议中的规则在此复核。恢复或归档操作写入审计日志； 允许/禁止同时存在的 CONFLICT 由确定性
    evaluator 返回，不自动裁决（ADR-005）。
  </p>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>规则</th>
          <th>场所</th>
          <th>效果</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in items" :key="c.rule_id">
          <td class="muted">{{ c.rule_id.slice(0, 8) }}…</td>
          <td class="muted">{{ c.place_id?.slice(0, 8) ?? "—" }}</td>
          <td>
            <span
              class="tag"
              :class="{ restricted: c.effect === 'prohibited', ok: c.effect === 'allowed' }"
              >{{ c.effect }}</span
            >
          </td>
          <td>
            <span class="tag warn">{{ c.status }}</span>
          </td>
          <td>
            <button class="primary" @click="restore(c)">恢复 current</button>
            <button style="margin-left: 6px" @click="archive(c)">归档</button>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="5" class="muted">当前无争议规则</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
