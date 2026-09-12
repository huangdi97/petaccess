<script setup lang="ts">
import { ref } from "vue";
import { page, ApiError } from "../api";

interface Place {
  id: string;
  canonical_name: string;
  place_type: string;
  canonical_address: string | null;
  lifecycle_status: string;
}

const items = ref<Place[]>([]);
const q = ref("");
const error = ref("");
const busy = ref(false);

const form = ref({
  canonical_name: "",
  place_type: "cafe",
  canonical_address: "",
  location_wkt: "",
});
const creating = ref(false);

async function load() {
  error.value = "";
  busy.value = true;
  try {
    items.value = (await page<Place>("/places", { q: q.value || undefined, limit: 50 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function create() {
  error.value = "";
  try {
    const body: Record<string, string> = {
      canonical_name: form.value.canonical_name,
      place_type: form.value.place_type,
    };
    if (form.value.canonical_address) body.canonical_address = form.value.canonical_address;
    if (form.value.location_wkt) body.location_wkt = form.value.location_wkt;
    const res = await fetch("/api/v1/places", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("admin_token")}`,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error((await res.json()).error?.message ?? "创建失败");
    creating.value = false;
    form.value = {
      canonical_name: "",
      place_type: "cafe",
      canonical_address: "",
      location_wkt: "",
    };
    await load();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}
</script>

<template>
  <h1>场所管理</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <div class="row" style="align-items: end">
      <div style="flex: 2">
        <label>名称搜索（模糊）</label>
        <input v-model="q" placeholder="如：星河" @keydown.enter="load" />
      </div>
      <button style="flex: 0" @click="load">搜索</button>
      <button style="flex: 0" class="primary" @click="creating = !creating">
        {{ creating ? "取消" : "新建场所" }}
      </button>
    </div>
    <div v-if="creating" class="panel" style="margin-top: 12px; background: #fafbfc">
      <div class="row">
        <div><label>名称</label><input v-model="form.canonical_name" /></div>
        <div>
          <label>类型</label>
          <select v-model="form.place_type">
            <option value="cafe">cafe</option>
            <option value="restaurant">restaurant</option>
            <option value="mall">mall</option>
            <option value="park">park</option>
            <option value="residential_community">residential_community</option>
            <option value="other">other</option>
          </select>
        </div>
        <div><label>地址</label><input v-model="form.canonical_address" /></div>
        <div>
          <label>位置 WKT（POINT(lng lat)，可空）</label
          ><input v-model="form.location_wkt" placeholder="POINT(121.47 31.23)" />
        </div>
      </div>
      <button
        class="primary"
        style="margin-top: 10px"
        :disabled="!form.canonical_name"
        @click="create"
      >
        保存
      </button>
    </div>
  </div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>名称</th>
          <th>类型</th>
          <th>地址</th>
          <th>状态</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in items" :key="p.id">
          <td>{{ p.canonical_name }}</td>
          <td>
            <span class="tag">{{ p.place_type }}</span>
          </td>
          <td class="muted">{{ p.canonical_address ?? "—" }}</td>
          <td>{{ p.lifecycle_status }}</td>
          <td><RouterLink :to="`/places/${p.id}`">详情 →</RouterLink></td>
        </tr>
        <tr v-if="!items.length">
          <td colspan="5" class="muted">{{ busy ? "加载中…" : "暂无数据" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
