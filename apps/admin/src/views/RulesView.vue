<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { page, get, ApiError } from "../api";
import StatusBadge from "../components/StatusBadge.vue";

interface Rule {
  id: string;
  place_id: string | null;
  zone_id: string | null;
  animal_scope: string;
  action: string;
  effect: string;
  status: string;
  rule_origin: string;
  review_due_at: string | null;
}
interface Place {
  id: string;
  canonical_name: string;
}

const rules = ref<Rule[]>([]);
const places = ref<Place[]>([]);
const placeId = ref("");
const error = ref("");
const loading = ref(true);

/** A rule past its review date is "需要复核" — shown as a status, not a colour. */
function isOverdue(r: Rule): boolean {
  if (!r.review_due_at || r.status !== "current") return false;
  const due = new Date(r.review_due_at);
  return !Number.isNaN(due.getTime()) && due.getTime() < Date.now();
}

const selectedPlaceName = computed(
  () => places.value.find((p) => p.id === placeId.value)?.canonical_name ?? "—",
);

async function load() {
  error.value = "";
  loading.value = true;
  try {
    if (!places.value.length) {
      places.value = (await page<Place>("/places", { limit: 50 })).items;
    }
    const target = placeId.value || places.value[0]?.id;
    if (target) {
      placeId.value = target;
      rules.value = (await get(`/places/${target}/rules`)) as unknown as Rule[];
    } else {
      rules.value = [];
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
    rules.value = [];
  } finally {
    loading.value = false;
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
        <label for="rule-place">场所</label>
        <select id="rule-place" v-model="placeId" @change="load">
          <option v-for="p in places" :key="p.id" :value="p.id">{{ p.canonical_name }}</option>
        </select>
      </div>
    </div>
  </div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>动物</th>
          <th>动作</th>
          <th>效果</th>
          <th>状态</th>
          <th>来源类型</th>
          <th>复核到期</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="6">
            <div class="skeleton-table">
              <div v-for="i in 5" :key="i" class="skeleton" style="height: 18px"></div>
            </div>
          </td>
        </tr>
        <template v-else>
          <tr v-for="r in rules" :key="r.id">
            <td>{{ r.animal_scope }}</td>
            <td>{{ r.action }}</td>
            <td><StatusBadge :effect="r.effect" /></td>
            <td>
              <span>{{ r.status }}</span>
              <StatusBadge v-if="isOverdue(r)" semantic="STALE" />
            </td>
            <td class="muted">{{ r.rule_origin }}</td>
            <td class="muted">{{ r.review_due_at?.slice(0, 10) ?? "—" }}</td>
          </tr>
        </template>
      </tbody>
    </table>
    <div v-if="!loading && !rules.length && !error" class="empty-state">
      <div class="empty-state__title">该场所暂无已发布规则</div>
      <div>{{ selectedPlaceName }} 尚未有通过发布闸门的规则。规则必须先经候选评审与来源核验。</div>
    </div>
  </div>
</template>
