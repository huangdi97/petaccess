<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { client, type PlaceSummary } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { useOnline } from "../composables/useOnline";

const router = useRouter();
const { online } = useOnline();
const q = ref("");
const results = ref<PlaceSummary[]>([]);
const searched = ref(false);
const loading = ref(false);
const error = ref("");

async function search() {
  if (!online.value) {
    error.value = "当前无网络连接，搜索需要联网。";
    return;
  }
  error.value = "";
  loading.value = true;
  searched.value = true;
  try {
    results.value = await client.searchPlaces(q.value);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：搜索需要联网，提交类操作已暂停。</span>
    </div>
    <div class="panel">
      <input
        v-model="q"
        placeholder="搜索场所名称，如：星河、公园、商场"
        data-testid="search-input"
        @keydown.enter="search"
      />
      <button
        class="primary block"
        style="margin-top: 8px"
        :disabled="loading"
        @click="search"
        data-testid="search-btn"
      >
        {{ loading ? "搜索中…" : "搜索" }}
      </button>
    </div>
    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" :description="error">
      <template #action>
        <button class="primary" @click="search">重试</button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="searched && !results.length"
      kind="EMPTY"
      description="没有匹配的场所。未收录不代表该场所没有规则。"
    />
    <template v-else>
      <div class="panel" v-for="p in results" :key="p.id" :data-testid="'result-' + p.canonical_name">
        <div style="cursor: pointer" @click="router.push({ name: 'place', params: { id: p.id } })">
          <div class="row" style="justify-content: space-between">
            <strong>{{ p.canonical_name }}</strong>
            <StatusBadge semantic="UNKNOWN" />
          </div>
          <div class="muted">{{ p.place_type }} · {{ p.canonical_address ?? "" }}</div>
        </div>
      </div>
    </template>
  </AppShell>
</template>
