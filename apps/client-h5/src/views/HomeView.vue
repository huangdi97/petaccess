<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  client,
  session,
  synthDemoCamera,
  STATUS_GLYPHS,
  type PlaceSummary,
  type MapCamera,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import MockMap from "../components/MockMap.vue";

const router = useRouter();
const camera = ref<MapCamera>(synthDemoCamera());
const places = ref<PlaceSummary[]>([]);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  await session.restore();
  try {
    // demo city center; real device uses one-shot geolocation (ADR-012: no
    // continuous location history — one-shot nearby query only)
    places.value = await client.nearby(camera.value.lat, camera.value.lng, 3000);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
});

function open(id: string) {
  router.push({ name: "place", params: { id } });
}
</script>

<template>
  <AppShell>
    <div class="map-mock" data-testid="map">
      <MockMap :camera="camera" :places="places" @select="open" />
    </div>
    <p class="notice">
      Mock 地图 Provider（腾讯地图 Key 未配置时自动 Mock；接入 Key 仅切换
      MapProvider，业务逻辑不变）。不承诺“现场绝对无动物”；服务犬规则单独查询。
    </p>
    <h2>附近场所</h2>
    <div v-if="error" class="panel">{{ error }}</div>
    <div class="panel" v-for="p in places" :key="p.id" :data-testid="'place-' + p.id">
      <div class="row" style="justify-content: space-between; cursor: pointer" @click="open(p.id)">
        <div>
          <strong>{{ p.canonical_name }}</strong>
          <div class="muted">
            {{ p.place_type }}<span v-if="p.distance_m"> · {{ Math.round(p.distance_m) }}m</span>
          </div>
        </div>
        <span class="tag">{{ STATUS_GLYPHS.UNKNOWN }}</span>
      </div>
    </div>
    <div class="panel" v-if="!loading && !places.length && !error">
      <span class="muted">附近暂无已收录场所</span>
    </div>
  </AppShell>
</template>
