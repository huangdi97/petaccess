<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { client, type PlaceSummary } from "@petaccess/client-core";
import Shell from "../components/Shell.vue";

const router = useRouter();
const q = ref("");
const results = ref<PlaceSummary[]>([]);
const searched = ref(false);
const error = ref("");

async function search() {
  error.value = "";
  searched.value = true;
  try {
    results.value = await client.searchPlaces(q.value);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}
</script>

<template>
  <Shell>
    <div class="panel">
      <input v-model="q" placeholder="搜索场所名称，如：星河、公园、商场" data-testid="search-input"
             @keydown.enter="search" />
      <button class="primary block" style="margin-top: 8px" @click="search" data-testid="search-btn">搜索</button>
    </div>
    <div v-if="error" class="panel">{{ error }}</div>
    <div class="panel" v-for="p in results" :key="p.id" :data-testid="'result-' + p.canonical_name">
      <div style="cursor: pointer" @click="router.push({ name: 'place', params: { id: p.id } })">
        <strong>{{ p.canonical_name }}</strong>
        <div class="muted">{{ p.place_type }} · {{ p.canonical_address ?? "" }}</div>
      </div>
    </div>
    <div class="panel" v-if="searched && !results.length && !error">
      <span class="muted">没有匹配的场所 — 未收录不等于不存在规则</span>
    </div>
  </Shell>
</template>
