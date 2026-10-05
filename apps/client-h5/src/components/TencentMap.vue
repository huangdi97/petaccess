<script setup lang="ts">
/**
 * TencentMap — optional real-tile renderer for the frozen Spatial Workspace.
 *
 * Product facts remain provider-neutral: Rule/Reality/Facility/Divergence,
 * selection, clustering and PlacePreview all stay outside this component.
 * This renderer only:
 *   1. loads Tencent JavaScript API GL with the browser-restricted client key;
 *   2. asks PetAccess API to convert governed EPSG:4326 display points to
 *      Tencent GCJ-02 (conversion never writes back to Place.location);
 *   3. projects our own accessible PetAccess markers on top of the real map.
 *
 * If SDK loading or translation fails the parent falls back to MockMap rather
 * than losing the list/detail information workspace.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { client, STATUS_GLYPHS, type MapCamera, type MapCluster, type MapMarker } from "@petaccess/client-core";

interface TencentLatLng {
  getLat?: () => number;
  getLng?: () => number;
}

interface TencentPoint {
  x: number;
  y: number;
}

interface TencentMapInstance {
  setCenter: (center: unknown) => unknown;
  setZoom: (zoom: number) => unknown;
  getZoom: () => number;
  projectToContainer: (latLng: unknown) => TencentPoint;
  on: (eventName: string, listener: () => void) => unknown;
  off: (eventName: string, listener: () => void) => unknown;
  destroy: () => void;
}

interface TencentApi {
  LatLng: new (lat: number, lng: number) => TencentLatLng;
  Map: new (
    container: HTMLElement,
    options: {
      center: TencentLatLng;
      zoom: number;
      pitch?: number;
      rotation?: number;
      viewMode?: string;
      minZoom?: number;
      maxZoom?: number;
    },
  ) => TencentMapInstance;
}

declare global {
  interface Window {
    TMap?: TencentApi;
    __petaccessTencentMapReady?: () => void;
  }
}

const props = withDefaults(
  defineProps<{
    clientKey: string;
    camera: MapCamera;
    clusters: MapCluster[];
    selectedId?: string | null;
    lens?: string;
    lensLabels?: Record<string, string>;
  }>(),
  { selectedId: null, lens: "rule", lensLabels: () => ({}) },
);

const emit = defineEmits<{
  select: [cluster: MapCluster];
  zoom: [delta: number];
  "zoom-absolute": [zoom: number];
  error: [message: string];
}>();

const host = ref<HTMLElement | null>(null);
const map = ref<TencentMapInstance | null>(null);
const ready = ref(false);

interface RenderCluster {
  cluster: MapCluster;
  lat: number;
  lng: number;
  left: number;
  top: number;
}
const rendered = ref<RenderCluster[]>([]);
const translationCache = new Map<string, { lat: number; lng: number }>();

let sdkPromise: Promise<TencentApi> | null = null;
function loadTencentSdk(key: string): Promise<TencentApi> {
  if (window.TMap) return Promise.resolve(window.TMap);
  if (sdkPromise) return sdkPromise;

  sdkPromise = new Promise<TencentApi>((resolve, reject) => {
    const callback = "__petaccessTencentMapReady";
    const existing = document.querySelector<HTMLScriptElement>('script[data-petaccess-tencent-map="1"]');

    const finish = () => {
      if (window.TMap) resolve(window.TMap);
      else reject(new Error("腾讯地图 SDK 已加载但未初始化"));
    };

    window[callback] = finish;
    if (existing) {
      existing.addEventListener("error", () => reject(new Error("腾讯地图 SDK 加载失败")), {
        once: true,
      });
      if (window.TMap) finish();
      return;
    }

    const script = document.createElement("script");
    script.charset = "utf-8";
    script.async = true;
    script.dataset.petaccessTencentMap = "1";
    script.src =
      `https://map.qq.com/api/gljs?v=1.exp&key=${encodeURIComponent(key)}&callback=${callback}`;
    script.addEventListener("error", () => reject(new Error("腾讯地图 SDK 加载失败")), {
      once: true,
    });
    document.head.appendChild(script);
  }).finally(() => {
    delete window.__petaccessTencentMapReady;
  });

  return sdkPromise;
}

function coordinateKey(lat: number, lng: number): string {
  return `${lat.toFixed(7)},${lng.toFixed(7)}`;
}

async function translate(
  points: { lat: number; lng: number }[],
): Promise<{ lat: number; lng: number }[]> {
  const missing: { lat: number; lng: number }[] = [];
  for (const point of points) {
    if (!translationCache.has(coordinateKey(point.lat, point.lng))) missing.push(point);
  }
  if (missing.length) {
    const response = await client.translateMapCoordinates(missing);
    if (response.provider !== "tencent" || response.coordinate_system !== "GCJ-02") {
      throw new Error("真实地图坐标转换未就绪");
    }
    response.coordinates.forEach((value, index) => {
      const source = missing[index];
      if (source) translationCache.set(coordinateKey(source.lat, source.lng), value);
    });
  }
  return points.map((point) => {
    const translated = translationCache.get(coordinateKey(point.lat, point.lng));
    if (!translated) throw new Error("地图坐标转换结果不完整");
    return translated;
  });
}

async function translatedCenter(): Promise<{ lat: number; lng: number }> {
  return (await translate([{ lat: props.camera.lat, lng: props.camera.lng }]))[0]!;
}

async function syncClusters() {
  const api = window.TMap;
  const instance = map.value;
  if (!api || !instance) return;

  const converted = await translate(props.clusters.map((cluster) => ({ lat: cluster.lat, lng: cluster.lng })));
  rendered.value = props.clusters.map((cluster, index) => ({
    cluster,
    lat: converted[index]!.lat,
    lng: converted[index]!.lng,
    left: 0,
    top: 0,
  }));
  await nextTick();
  projectMarkers();
}

function projectMarkers() {
  const api = window.TMap;
  const instance = map.value;
  if (!api || !instance) return;
  rendered.value = rendered.value.map((item) => {
    const pixel = instance.projectToContainer(new api.LatLng(item.lat, item.lng));
    return { ...item, left: pixel.x, top: pixel.y };
  });
}

function onMapIdle() {
  projectMarkers();
  const z = map.value?.getZoom();
  if (typeof z === "number" && Number.isFinite(z) && Math.abs(z - props.camera.zoom) > 0.01) {
    emit("zoom-absolute", z);
  }
}

const glyph = (status: MapMarker["status"]) => STATUS_GLYPHS[status] ?? STATUS_GLYPHS.UNKNOWN;
function markerLabel(cluster: MapCluster): string {
  if (cluster.count > 1) return `${cluster.count} 个场所`;
  const id = cluster.memberIds[0];
  return id ? (props.lensLabels[id] ?? glyph(cluster.status)) : glyph(cluster.status);
}

const providerLabel = computed(() => (ready.value ? "腾讯地图底图" : "正在加载真实地图…"));

async function boot() {
  if (!host.value || !props.clientKey) return;
  try {
    const api = await loadTencentSdk(props.clientKey);
    const center = await translatedCenter();
    map.value = new api.Map(host.value, {
      center: new api.LatLng(center.lat, center.lng),
      zoom: props.camera.zoom,
      pitch: 0,
      rotation: 0,
      viewMode: "2D",
      minZoom: 8,
      maxZoom: 18,
    });
    map.value.on("idle", onMapIdle);
    ready.value = true;
    await syncClusters();
  } catch (error) {
    emit("error", error instanceof Error ? error.message : "真实地图暂不可用");
  }
}

watch(
  () => [props.camera.lat, props.camera.lng] as const,
  async ([lat, lng]) => {
    if (!map.value || !window.TMap) return;
    try {
      const center = (await translate([{ lat, lng }]))[0]!;
      map.value.setCenter(new window.TMap.LatLng(center.lat, center.lng));
    } catch (error) {
      emit("error", error instanceof Error ? error.message : "地图中心转换失败");
    }
  },
);

watch(
  () => props.camera.zoom,
  (zoom) => {
    if (map.value && Math.abs(map.value.getZoom() - zoom) > 0.01) map.value.setZoom(zoom);
  },
);

watch(
  () => props.clusters,
  () => void syncClusters().catch((error) =>
    emit("error", error instanceof Error ? error.message : "地图点位转换失败"),
  ),
  { deep: true },
);

onMounted(() => void boot());
onBeforeUnmount(() => {
  if (map.value) {
    map.value.off("idle", onMapIdle);
    map.value.destroy();
    map.value = null;
  }
});
</script>

<template>
  <div
    class="tencent-map"
    :class="`tencent-map--${lens}`"
    data-testid="map-surface"
    data-ui="real-map"
  >
    <div ref="host" class="tencent-map__host" aria-hidden="true"></div>
    <div class="tencent-map__wash" aria-hidden="true"></div>

    <span class="tencent-map__provider muted">{{ providerLabel }}</span>

    <div class="map-zoom" role="group" aria-label="缩放">
      <button type="button" aria-label="放大" :disabled="camera.zoom >= 18" @click="emit('zoom', 1)">
        ＋
      </button>
      <button type="button" aria-label="缩小" :disabled="camera.zoom <= 8" @click="emit('zoom', -1)">
        －
      </button>
    </div>

    <button
      v-for="item in rendered"
      :key="item.cluster.id"
      type="button"
      class="real-pin"
      :class="[
        `s-${item.cluster.status}`,
        { 'real-pin--selected': selectedId === item.cluster.memberIds[0] },
      ]"
      :style="{ left: item.left + 'px', top: item.top + 'px' }"
      :aria-label="`${item.cluster.count} 个场所，${markerLabel(item.cluster)}`"
      :data-testid="
        item.cluster.count > 1
          ? 'cluster-' + item.cluster.id
          : 'pin-' + item.cluster.memberIds[0]
      "
      @click="emit('select', item.cluster)"
    >
      <span v-if="item.cluster.count > 1" class="real-pin__cluster">{{ item.cluster.count }}</span>
      <span v-else class="real-pin__dot"></span>
      <span
        v-if="selectedId === item.cluster.memberIds[0]"
        class="real-pin__label"
      >
        {{ markerLabel(item.cluster) }}
      </span>
    </button>
  </div>
</template>

<style scoped>
.tencent-map {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 480px;
  overflow: hidden;
  background: var(--pa-color-map-grid-a);
}

.tencent-map__host {
  position: absolute;
  inset: 0;
}

.tencent-map__wash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: rgba(248, 250, 250, 0.08);
  z-index: 1;
}

.tencent-map__provider {
  position: absolute;
  left: var(--pa-space-3);
  bottom: var(--pa-space-2);
  z-index: 4;
  padding: 2px var(--pa-space-1);
  border-radius: var(--pa-radius-sm);
  background: color-mix(in srgb, var(--pa-color-surface) 88%, transparent);
  font-size: var(--pa-font-size-xs);
}

.map-zoom {
  position: absolute;
  right: var(--pa-space-3);
  top: var(--pa-space-3);
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.map-zoom button {
  width: var(--pa-size-control-lg);
  height: var(--pa-size-control-lg);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-lg);
  cursor: pointer;
}

.map-zoom button:disabled {
  cursor: default;
  opacity: 0.45;
}

.real-pin {
  position: absolute;
  z-index: 3;
  transform: translate(-50%, -100%);
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  min-width: 36px;
  min-height: 44px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.real-pin__dot,
.real-pin__cluster {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--pa-color-map-pin-border);
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-status-unknown);
}

.real-pin__dot {
  width: 14px;
  height: 14px;
}

.real-pin__cluster {
  min-width: 26px;
  height: 26px;
  padding: 0 var(--pa-space-1);
  color: var(--pa-color-text-inverse);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-bold);
}

.real-pin__label {
  order: -1;
  max-width: 210px;
  padding: 1px var(--pa-space-1);
  overflow: hidden;
  border-radius: var(--pa-radius-sm);
  background: var(--pa-color-map-label-bg);
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
  box-shadow: var(--pa-elevation-1);
}

.real-pin--selected .real-pin__dot,
.real-pin--selected .real-pin__cluster {
  box-shadow: 0 0 0 4px var(--pa-color-accent-weak), var(--pa-elevation-2);
}

.s-ALLOWED .real-pin__dot,
.s-ALLOWED .real-pin__cluster {
  background: var(--pa-color-status-allowed);
}

.s-CONDITIONAL .real-pin__dot {
  background: var(--pa-color-surface);
  border: 3px solid var(--pa-color-status-conditional);
}

.s-CONDITIONAL .real-pin__cluster {
  background: var(--pa-color-status-conditional);
}

.s-RESTRICTED .real-pin__dot,
.s-RESTRICTED .real-pin__cluster {
  background: var(--pa-color-status-restricted);
}

.s-CONFLICT .real-pin__dot,
.s-CONFLICT .real-pin__cluster {
  background: var(--pa-color-status-conflict);
}

.s-STALE .real-pin__dot,
.s-STALE .real-pin__cluster {
  background: var(--pa-color-status-stale);
}

.tencent-map--reality .s-ALLOWED .real-pin__dot,
.tencent-map--reality .s-ALLOWED .real-pin__cluster {
  background: var(--pa-color-reality-observed);
}

.tencent-map--reality .s-UNKNOWN .real-pin__dot,
.tencent-map--reality .s-UNKNOWN .real-pin__cluster {
  background: var(--pa-color-reality-insufficient);
}

.tencent-map--reality .s-CONFLICT .real-pin__dot,
.tencent-map--reality .s-CONFLICT .real-pin__cluster {
  background: var(--pa-color-reality-disputed);
}

.tencent-map--facility .s-ALLOWED .real-pin__dot,
.tencent-map--facility .s-ALLOWED .real-pin__cluster {
  background: var(--pa-color-facility-confirmed);
}

.tencent-map--facility .s-UNKNOWN .real-pin__dot,
.tencent-map--facility .s-UNKNOWN .real-pin__cluster,
.tencent-map--facility .s-STALE .real-pin__dot,
.tencent-map--facility .s-STALE .real-pin__cluster {
  background: var(--pa-color-facility-unverified);
}

.tencent-map--divergence .s-ALLOWED .real-pin__dot,
.tencent-map--divergence .s-ALLOWED .real-pin__cluster {
  background: var(--pa-color-reality-observed);
}

@media (max-width: 767px) {
  .tencent-map {
    min-height: 360px;
  }
}
</style>
