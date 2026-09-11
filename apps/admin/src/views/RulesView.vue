<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, get, ApiError } from "../api";

interface Rule {
  id: string; place_id: string | null; zone_id: string | null;
  animal_scope: string; action: string; effect: string; status: string;
  rule_origin: string; review_due_at: string | null;
}
interface Place { id: string; canonical_name: string }

const rules = ref<Rule[]>([]);
const places = ref<Place[]>([]);
const placeId = ref("");
const error = ref("");

async function load() {
  error.value = "";
  try {
    if (!places.value.length) {
      places.value = (await page<Place>("/places", { limit: 50 })).items;
    }
    const target = placeId.value || places.value[0]?.id;
    if (target) rules.value = (await get(`/places/${target}/rules`)) as unknown as Rule[];
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

onMounted(load);
</script>

<template>
  <h1>规则管理</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <div class="row" style="align-items: end">
      <div>
        <label>场所</label>
        <select v-model="placeId" @change="load">
          <option v-for="p in places" :key="p.id" :value="p.id">{{ p.canonical_name }}</option>
        </select>
      </div>
    </div>
  </div>
  <div class="panel">
    <table>
      <thead><tr><th>动物</th><th>动作</th><th>效果</th><th>状态</th><th>来源类型</th><th>复核到期</th></tr></thead>
      <tbody>
        <tr v-for="r in rules" :key="r.id">
          <td>{{ r.animal_scope }}</td><td>{{ r.action }}</td>
          <td><span class="tag" :class="{ restricted: r.effect === 'prohibited', ok: r.effect === 'allowed', warn: r.effect === 'conditional' }">{{ r.effect }}</span></td>
          <td>{{ r.status }}</td>
          <td class="muted">{{ r.rule_origin }}</td>
          <td class="muted">{{ r.review_due_at?.slice(0, 10) ?? "—" }}</td>
        </tr>
        <tr v-if="!rules.length"><td colspan="6" class="muted">暂无规则</td></tr>
      </tbody>
    </table>
  </div>
</template>
