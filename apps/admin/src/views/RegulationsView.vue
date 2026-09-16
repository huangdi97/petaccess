<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, ApiError } from "../api";

interface Regulation {
  id: string;
  jurisdiction_level: string;
  jurisdiction_id: string;
  authority: string;
  document_name: string;
  clause_ref: string | null;
  animal_scope: string;
  venue_scope: string | null;
  action: string | null;
  effect: string | null;
  mandatory_level: string;
  review_status: string;
  effective_from: string | null;
}

const items = ref<Regulation[]>([]);
const error = ref("");
const reviewStatusFilter = ref("");

async function load() {
  error.value = "";
  try {
    items.value = (
      await page<Regulation>("/regulations", {
        review_status: reviewStatusFilter.value || undefined,
        limit: 100,
      })
    ).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function markReviewed(r: Regulation, status: string) {
  error.value = "";
  try {
    await post(`/regulations/${r.id}/review`, { review_status: status });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

onMounted(load);
</script>

<template>
  <h1>法规（Jurisdiction）</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <p class="muted">
    "没查"绝不显示为"法律没规定"：NOT_REVIEWED / NO_EXPLICIT_RULE_FOUND /
    EXPLICIT_OPERATOR_DISCRETION / REVIEWED_ACTIVE 严格区分（设计 #18）。
  </p>
  <div class="panel">
    <div class="row" style="align-items: end">
      <div>
        <label for="fld-reviewstatusfilter">审核状态</label>
        <select v-model="reviewStatusFilter" id="fld-reviewstatusfilter" @change="load">
          <option value="">全部</option>
          <option value="not_reviewed">not_reviewed</option>
          <option value="no_explicit_rule_found">no_explicit_rule_found</option>
          <option value="explicit_operator_discretion">explicit_operator_discretion</option>
          <option value="reviewed_active">reviewed_active</option>
        </select>
      </div>
    </div>
  </div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>文件</th>
          <th>条款</th>
          <th>层级</th>
          <th>动物</th>
          <th>效力</th>
          <th>审核状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in items" :key="r.id">
          <td>{{ r.document_name }}</td>
          <td>{{ r.clause_ref ?? "—" }}</td>
          <td>{{ r.jurisdiction_level }}</td>
          <td>{{ r.animal_scope }}</td>
          <td>
            {{ r.effect ?? "—"
            }}<span class="muted" v-if="r.mandatory_level"> · {{ r.mandatory_level }}</span>
          </td>
          <td>
            <span class="tag" :class="{ warn: r.review_status === 'not_reviewed' }">{{
              r.review_status
            }}</span>
          </td>
          <td>
            <button
              v-if="r.review_status === 'not_reviewed'"
              @click="markReviewed(r, 'no_explicit_rule_found')"
            >
              标记·无明文规则
            </button>
            <button
              v-if="r.review_status !== 'reviewed_active'"
              @click="markReviewed(r, 'reviewed_active')"
            >
              标记·现行有效
            </button>
          </td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="7" class="muted">暂无法规</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
