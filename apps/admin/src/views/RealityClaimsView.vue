<script setup lang="ts">
/**
 * Reality Claims Viewer (v0.9-R1 §7 / AC11).
 *
 * Read-only view of PUBLISHED, human-verified reality claims per place —
 * ObservedPresence / StaffResponseObservation / AnimalFacility. Supports the
 * Evidence Viewer surface; staff identity stays role-only here.
 */
import { onMounted, ref } from "vue";
import { errText, page } from "../api";

const placeId = ref("");
const tab = ref<"observed" | "staff" | "facility">("observed");
// Admin read-only viewer: the reality claim endpoints are not part of the
// generated client types yet, so rows are treated as an opaque key/value map
// rather than `any` (unjustified type escape stays out).
type ClaimRow = Record<string, unknown>;
const items = ref<ClaimRow[]>([]);
const total = ref(0);
const error = ref("");
const loaded = ref(false);

const TYPE_LABELS: Record<string, string> = {
  observed: "动物出现（ObservedPresence）",
  staff: "工作人员处理（StaffResponse）",
  facility: "动物设施（AnimalFacility）",
};

async function load() {
  if (!placeId.value.trim()) {
    error.value = "请先输入场所 ID";
    return;
  }
  error.value = "";
  loaded.value = false;
  try {
    const path =
      tab.value === "observed"
        ? `/admin/places/${placeId.value}/reality/observed`
        : tab.value === "staff"
          ? `/admin/places/${placeId.value}/reality/staff-responses`
          : `/admin/places/${placeId.value}/reality/facilities`;
    const res = await page<ClaimRow>(path, { limit: 100 });
    items.value = res.items;
    total.value = res.total;
    loaded.value = true;
  } catch (e) {
    error.value = errText(e);
  }
}

/** Keep the payload surface honest: show facts, never a score. */
const factRows = (row: ClaimRow) => {
  const skip = new Set(["id", "place_id", "candidate_id", "created_at", "updated_at"]);
  return Object.entries(row)
    .filter(([k, v]) => !skip.has(k) && v !== null && v !== undefined && v !== "")
    .map(([k, v]) => ({ k, v: typeof v === "object" ? JSON.stringify(v) : String(v) }));
};

onMounted(() => {
  if (placeId.value) load();
});
</script>

<template>
  <section>
    <h1>Reality Claims</h1>
    <p class="muted">已发布（人工核验）claim 查看 —— 员工身份只以角色呈现，不落库、不展示。</p>

    <div class="toolbar">
      <input v-model="placeId" placeholder="场所 ID" />
      <select v-model="tab" @change="load">
        <option v-for="(l, t) in TYPE_LABELS" :key="t" :value="t">{{ l }}</option>
      </select>
      <button @click="load">查询</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="loaded" class="muted">共 {{ total }} 条（{{ TYPE_LABELS[tab] }}）</div>

    <div v-for="row in items" :key="String(row.id)" class="card">
      <h3>{{ row.id }}</h3>
      <div class="grid">
        <div v-for="(r, i) in factRows(row)" :key="i" class="fact">
          <span class="k">{{ r.k }}</span>
          <span class="v">{{ r.v }}</span>
        </div>
      </div>
    </div>
    <div v-if="loaded && items.length === 0" class="muted">该场所暂无已发布 claim。</div>
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin: 12px 0;
  flex-wrap: wrap;
}
input {
  padding: 6px 8px;
  border: 1px solid var(--line);
  border-radius: 6px;
  min-width: 260px;
}
.card {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}
.card h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--text);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 6px 14px;
}
.fact {
  display: flex;
  gap: 8px;
  font-size: 13px;
}
.k {
  color: var(--muted);
  min-width: 120px;
}
.v {
  word-break: break-all;
}
.error {
  color: var(--danger);
  background: var(--pa-color-status-restricted-bg);
  padding: 8px 12px;
  border-radius: 6px;
  margin: 8px 0;
}
.muted {
  color: var(--muted);
}
</style>
