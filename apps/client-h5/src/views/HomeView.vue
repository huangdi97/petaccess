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
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { useOnline } from "../composables/useOnline";

const router = useRouter();
const { online } = useOnline();
const camera = ref<MapCamera>(synthDemoCamera());
const places = ref<PlaceSummary[]>([]);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    // demo city center; real device uses one-shot geolocation (ADR-012: no
    // continuous location history — one-shot nearby query only)
    places.value = await client.nearby(camera.value.lat, camera.value.lng, 3000);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await session.restore();
  await load();
});

function open(id: string) {
  router.push({ name: "place", params: { id } });
}
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：已加载内容仍可查看，提交类操作已暂停。</span>
    </div>
    <div class="map-mock" data-testid="map">
      <MockMap :camera="camera" :places="places" @select="open" />
    </div>
    <p class="notice">
      Mock 地图 Provider（腾讯地图 Key 未配置时自动 Mock；接入 Key 仅切换
      MapProvider，业务逻辑不变）。不承诺“现场绝对无动物”；服务犬规则单独查询。
    </p>
    <h2>附近场所</h2>
    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage
      v-else-if="error"
      kind="ERROR"
      :description="`未能取得附近场所：${error}`"
    >
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>
    <StateMessage v-else-if="!places.length" kind="EMPTY" />
    <template v-else>
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
    </template>
  </AppShell>
</template>
