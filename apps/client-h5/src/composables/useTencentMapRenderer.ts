import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";
import { client, type MapCamera, type MapCluster, type MapMarker } from "@petaccess/client-core";

interface TencentLatLng {
  getLat?: () => number;
  getLng?: () => number;
}
interface TencentMapInstance {
  setCenter: (center: unknown) => unknown;
  setZoom: (zoom: number) => unknown;
  getZoom: () => number;
  on: (eventName: string, listener: () => void) => unknown;
  off: (eventName: string, listener: () => void) => unknown;
  destroy: () => void;
}
interface TencentMarkerEvent {
  geometry?: { id?: string };
}
interface TencentMarkerLayer {
  on: (eventName: string, listener: (event: TencentMarkerEvent) => void) => unknown;
  off: (eventName: string, listener: (event: TencentMarkerEvent) => void) => unknown;
  setMap: (map: TencentMapInstance | null) => unknown;
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
  MarkerStyle: new (options: { width: number; height: number; src: string }) => unknown;
  MultiMarker: new (options: {
    map: TencentMapInstance;
    styles: Record<string, unknown>;
    geometries: { id: string; styleId: string; position: TencentLatLng }[];
  }) => TencentMarkerLayer;
}
declare global {
  interface Window {
    TMap?: TencentApi;
    __petaccessTencentMapReady?: () => void;
  }
}

export interface TencentRendererOptions {
  clientKey: () => string;
  camera: () => MapCamera;
  clusters: () => MapCluster[];
  selectedId: () => string | null;
  lens: () => string;
  onSelect: (cluster: MapCluster) => void;
  onZoom: (zoom: number) => void;
  onError: (message: string) => void;
}

const translationCache = new Map<string, { lat: number; lng: number }>();
let sdkPromise: Promise<TencentApi> | null = null;

function coordinateKey(lat: number, lng: number): string {
  return `${lat.toFixed(7)},${lng.toFixed(7)}`;
}

function failMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function loadTencentSdk(key: string): Promise<TencentApi> {
  if (window.TMap) return Promise.resolve(window.TMap);
  if (sdkPromise) return sdkPromise;

  sdkPromise = new Promise<TencentApi>((resolve, reject) => {
    const callback = "__petaccessTencentMapReady";
    document.querySelector<HTMLScriptElement>('script[data-petaccess-tencent-map="1"]')?.remove();

    const script = document.createElement("script");
    const timeout = window.setTimeout(() => reject(new Error("腾讯地图 SDK 加载超时")), 12000);
    const finish = () => {
      window.clearTimeout(timeout);
      if (window.TMap) resolve(window.TMap);
      else reject(new Error("腾讯地图 SDK 已加载但未初始化"));
    };

    window[callback] = finish;
    script.charset = "utf-8";
    script.async = true;
    script.dataset.petaccessTencentMap = "1";
    script.src = `https://map.qq.com/api/gljs?v=1.exp&key=${encodeURIComponent(key)}&callback=${callback}`;
    script.addEventListener(
      "error",
      () => {
        window.clearTimeout(timeout);
        reject(new Error("腾讯地图 SDK 加载失败"));
      },
      { once: true },
    );
    document.head.appendChild(script);
  })
    .catch((error) => {
      sdkPromise = null;
      throw error;
    })
    .finally(() => {
      delete window.__petaccessTencentMapReady;
    });

  return sdkPromise;
}

async function translate(points: { lat: number; lng: number }[]) {
  const missing = points.filter(
    (point) => !translationCache.has(coordinateKey(point.lat, point.lng)),
  );
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
    const value = translationCache.get(coordinateKey(point.lat, point.lng));
    if (!value) throw new Error("地图坐标转换结果不完整");
    return value;
  });
}

function tokenColor(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "currentColor";
}

function markerColor(lens: string, status: MapMarker["status"]): string {
  if (lens === "reality") {
    if (status === "ALLOWED") return tokenColor("--pa-color-reality-observed");
    if (status === "CONFLICT") return tokenColor("--pa-color-reality-disputed");
    return tokenColor("--pa-color-reality-insufficient");
  }
  if (lens === "facility") {
    return status === "ALLOWED"
      ? tokenColor("--pa-color-facility-confirmed")
      : tokenColor("--pa-color-facility-unverified");
  }
  if (lens === "divergence") {
    if (status === "CONFLICT") return tokenColor("--pa-color-status-conflict");
    if (status === "ALLOWED") return tokenColor("--pa-color-reality-observed");
    return tokenColor("--pa-color-reality-insufficient");
  }
  const tokenByStatus: Record<string, string> = {
    ALLOWED: "--pa-color-status-allowed",
    CONDITIONAL: "--pa-color-status-conditional",
    RESTRICTED: "--pa-color-status-restricted",
    CONFLICT: "--pa-color-status-conflict",
    STALE: "--pa-color-status-stale",
    UNKNOWN: "--pa-color-status-unknown",
  };
  return tokenColor(tokenByStatus[status] ?? "--pa-color-status-unknown");
}

function markerSvg(color: string, count: number, selected: boolean): string {
  const accent = tokenColor("--pa-color-accent");
  const surface = tokenColor("--pa-color-surface");
  const ring = selected
    ? `<circle cx="18" cy="18" r="15" fill="none" stroke="${accent}" stroke-width="3"/>`
    : "";
  const text =
    count > 1
      ? `<text x="18" y="22" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" font-weight="700" fill="${surface}">${Math.min(count, 99)}</text>`
      : "";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">${ring}<circle cx="18" cy="18" r="${selected ? 10 : 9}" fill="${color}" stroke="${surface}" stroke-width="2"/>${text}</svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

export function useTencentMapRenderer(options: TencentRendererOptions) {
  const host = ref<HTMLElement | null>(null);
  const ready = ref(false);
  const map = shallowRef<TencentMapInstance | null>(null);
  const markerLayer = shallowRef<TencentMarkerLayer | null>(null);
  const providerLabel = computed(() => (ready.value ? "腾讯地图底图" : "正在加载真实地图…"));

  function onMapIdle() {
    const zoom = map.value?.getZoom();
    if (typeof zoom === "number" && Number.isFinite(zoom)) options.onZoom(zoom);
  }

  function onMarkerClick(event: TencentMarkerEvent) {
    const id = event.geometry?.id;
    const cluster = options.clusters().find((item) => item.id === id);
    if (cluster) options.onSelect(cluster);
  }

  function clearMarkers() {
    if (!markerLayer.value) return;
    markerLayer.value.off("click", onMarkerClick);
    markerLayer.value.setMap(null);
    markerLayer.value = null;
  }

  async function syncMarkers() {
    const api = window.TMap;
    const instance = map.value;
    if (!api || !instance) return;

    const clusters = options.clusters();
    const converted = await translate(
      clusters.map((cluster) => ({ lat: cluster.lat, lng: cluster.lng })),
    );
    const styles: Record<string, unknown> = {};
    const geometries = clusters.map((cluster, index) => {
      const selected = Boolean(options.selectedId() && cluster.memberIds.includes(options.selectedId()!));
      const styleId = `${options.lens()}-${cluster.status}-${cluster.count}-${selected ? "selected" : "plain"}`;
      if (!styles[styleId]) {
        styles[styleId] = new api.MarkerStyle({
          width: 36,
          height: 36,
          src: markerSvg(markerColor(options.lens(), cluster.status), cluster.count, selected),
        });
      }
      const point = converted[index]!;
      return { id: cluster.id, styleId, position: new api.LatLng(point.lat, point.lng) };
    });

    clearMarkers();
    markerLayer.value = new api.MultiMarker({ map: instance, styles, geometries });
    markerLayer.value.on("click", onMarkerClick);
  }

  async function syncCenter() {
    if (!map.value || !window.TMap) return;
    const camera = options.camera();
    const center = (await translate([{ lat: camera.lat, lng: camera.lng }]))[0]!;
    map.value.setCenter(new window.TMap.LatLng(center.lat, center.lng));
  }

  async function boot() {
    if (!host.value || !options.clientKey()) return;
    try {
      const api = await loadTencentSdk(options.clientKey());
      const camera = options.camera();
      const center = (await translate([{ lat: camera.lat, lng: camera.lng }]))[0]!;
      map.value = new api.Map(host.value, {
        center: new api.LatLng(center.lat, center.lng),
        zoom: camera.zoom,
        pitch: 0,
        rotation: 0,
        viewMode: "2D",
        minZoom: 8,
        maxZoom: 18,
      });
      map.value.on("idle", onMapIdle);
      ready.value = true;
      await nextTick();
      await syncMarkers();
    } catch (error) {
      options.onError(failMessage(error, "真实地图暂不可用"));
    }
  }

  watch(
    () => [options.camera().lat, options.camera().lng] as const,
    () =>
      void syncCenter().catch((error) => options.onError(failMessage(error, "地图中心转换失败"))),
  );
  watch(
    () => options.camera().zoom,
    (zoom) => {
      if (map.value && Math.abs(map.value.getZoom() - zoom) > 0.01) map.value.setZoom(zoom);
    },
  );
  watch(
    () => [options.clusters(), options.selectedId(), options.lens()] as const,
    () =>
      void syncMarkers().catch((error) => options.onError(failMessage(error, "地图点位转换失败"))),
    { deep: true },
  );

  onMounted(() => void boot());
  onBeforeUnmount(() => {
    clearMarkers();
    if (map.value) {
      map.value.off("idle", onMapIdle);
      map.value.destroy();
      map.value = null;
    }
  });

  return { host, ready, providerLabel };
}
