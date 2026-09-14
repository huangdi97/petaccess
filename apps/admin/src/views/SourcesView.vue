<script setup lang="ts">
import { onMounted, ref } from "vue";
import { page, ApiError } from "../api";
import SourceBadge from "../components/SourceBadge.vue";

interface Source {
  id: string;
  source_type: string;
  issuer: string;
  issuer_verification: string;
  source_url: string | null;
  collected_at: string;
  directness: string;
  source_availability: string;
}

const items = ref<Source[]>([]);
const error = ref("");
const loading = ref(true);

onMounted(async () => {
  try {
    items.value = (await page<Source>("/sources", { limit: 100 })).items;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <h1>来源（Provenance）</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>类型</th>
          <th>签发方</th>
          <th>核验</th>
          <th>直接性</th>
          <th>采集时间</th>
          <th>链接</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="6">
            <div class="skeleton-table">
              <div v-for="i in 6" :key="i" class="skeleton" style="height: 18px"></div>
            </div>
          </td>
        </tr>
        <template v-else>
          <tr v-for="s in items" :key="s.id">
            <td>
              <SourceBadge :source-type="s.source_type" :label="s.source_type" />
            </td>
            <td>{{ s.issuer }}</td>
            <td>{{ s.issuer_verification }}</td>
            <td>{{ s.directness }}</td>
            <td class="muted">{{ s.collected_at.slice(0, 10) }}</td>
            <td>
              <a v-if="s.source_url" :href="s.source_url" target="_blank" rel="noopener">查看</a
              ><span v-else class="muted">—</span>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <div v-if="!loading && !items.length && !error" class="empty-state">
      <div class="empty-state__title">暂无来源</div>
      <div>尚未登记任何来源。规则必须可追溯到已登记来源才能进入发布流程。</div>
    </div>
  </div>
</template>
