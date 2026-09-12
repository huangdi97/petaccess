<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, post, ApiError } from "../api";

interface Dispute {
  id: string;
  target_type: string;
  target_id: string;
  reason_code: string;
  notice_text: string;
  counter_statement: string | null;
  status: string;
  temporary_action: string;
  resolution: string | null;
  resolution_note: string | null;
  created_at: string;
}

const items = ref<Dispute[]>([]);
const error = ref("");
const busyId = ref("");
const resolutionNote = ref("人工复核完成");

const RESOLUTIONS = [
  { value: "rule_restored", label: "恢复规则" },
  { value: "rule_corrected", label: "更正规则" },
  { value: "content_archived", label: "归档内容" },
  { value: "content_deleted", label: "删除内容" },
  { value: "observation_upheld", label: "维持观察" },
  { value: "no_change", label: "维持原状" },
];

async function load() {
  error.value = "";
  try {
    items.value = (await page<Dispute>("/disputes", { limit: 100 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
}

async function temporaryAction(d: Dispute, action: string) {
  error.value = "";
  busyId.value = d.id;
  try {
    await post(`/disputes/${d.id}/review`, { action });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busyId.value = "";
  }
}

async function resolve(d: Dispute, resolution: string) {
  error.value = "";
  busyId.value = d.id;
  try {
    await post(`/disputes/${d.id}/resolve`, { resolution, resolution_note: resolutionNote.value });
    await load();
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busyId.value = "";
  }
}

onMounted(load);
</script>

<template>
  <h1>异议处理</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <p class="muted">
    流程：提交 → 临时措施/转送 → 反声明 → 人工复核 → 恢复/更正/归档/删除 → 审计（设计 #26）。
    管理方不能直接删除用户 Observation，必须走此流程。
  </p>
  <div class="panel" v-for="d in items" :key="d.id">
    <div class="row">
      <div style="flex: 2">
        <strong>{{ d.reason_code }}</strong>
        <span class="tag" :class="{ warn: d.status !== 'resolved' }" style="margin-left: 8px">{{
          d.status
        }}</span>
        <span class="tag" style="margin-left: 4px">{{ d.target_type }}</span>
      </div>
      <div class="muted">{{ d.created_at.slice(0, 10) }}</div>
    </div>
    <p style="margin: 8px 0 4px">{{ d.notice_text }}</p>
    <p class="muted" v-if="d.counter_statement" style="margin: 4px 0">
      反声明：{{ d.counter_statement }}
    </p>
    <div class="row" style="margin-top: 8px; align-items: end" v-if="d.status !== 'resolved'">
      <div style="flex: 0">
        <label>临时措施</label><br />
        <button :disabled="busyId === d.id" @click="temporaryAction(d, 'mark_unverified')">
          标记未核验
        </button>
        <button
          :disabled="busyId === d.id"
          style="margin-left: 6px"
          @click="temporaryAction(d, 'mark_disputed')"
        >
          标记争议中
        </button>
      </div>
      <div style="flex: 0">
        <label>办结</label><br />
        <button
          v-for="r in RESOLUTIONS"
          :key="r.value"
          class="primary"
          :disabled="busyId === d.id"
          style="margin-right: 6px; margin-top: 4px"
          @click="resolve(d, r.value)"
        >
          {{ r.label }}
        </button>
      </div>
    </div>
    <p class="muted" v-else style="margin: 4px 0">
      办结：{{ d.resolution }} · {{ d.resolution_note }}
    </p>
  </div>
  <div class="panel" v-if="!items.length"><span class="muted">暂无异议</span></div>
</template>
