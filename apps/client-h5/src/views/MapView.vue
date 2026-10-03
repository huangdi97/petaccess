<script setup lang="ts">
/**
 * Map — Spatial Workspace (UI_RECONSTRUCTION_DESIGN_FREEZE §9).
 *
 * Desktop (≥768): rail + 400px result pane (MapResultPane) + FULL map canvas
 * as the dominant surface; the selected place shows ONE floating PlacePreview
 * (elevation, 10–12px radius, fixed bottom-right over the map). Mobile: full
 * map + bottom sheet; 地图/列表 toggle switches the single visible surface.
 * No `.panel` card walls.
 *
 * Data lives in useMapWorkspace — the ONLY consumer source is the repository
 * (CoexistenceSnapshot SSOT, bounded concurrency, cache). Markers = shape +
 * semantic status, never a ranking; map failure surfaces via StateMessage.
 */
import MapResultPane from "../components/domain/MapResultPane.vue";
import MockMap from "../components/MockMap.vue";
import MapSelectedSheet from "../components/map/MapSelectedSheet.vue";
import PlacePreview from "../components/domain/PlacePreview.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import StateMessage from "../components/StateMessage.vue";
import { useMapWorkspace } from "../composables/useMapWorkspace";
import { useRouter } from "vue-router";

const {
  camera,
  places,
  statuses,
  loading,
  error,
  locationState,
  view,
  selected,
  isDesktop,
  preview,
  activeFilters,
  clusters,
  coverage,
  visiblePlaces,
  locate,
  load,
  open,
  onSelectCluster,
  goSearch,
  syncRoutePlace,
} = useMapWorkspace();
const router = useRouter();

/** The pane's empty-state action leads back to the task launcher. */
function goHome() {
  void router.push({ name: "home" });
}
</script>

<template>
  <div
    class="map-workspace"
    data-testid="map-workspace"
    data-ui="map-shell"
    data-ui-page="map"
    data-ui-state="ready"
    data-ui-fixture="map-ready-v1"
  >
    <h1 class="visually-hidden">规则地图</h1>
    <QueryContextBar />

    <!-- v0.2.4 §32：desktop 没有「地图/列表」模式切换 —— desktop 恒为 List+Map。
         Mobile 保留 compact mode toggle（仅确有必要时）。 -->
    <div v-if="!isDesktop" class="map-viewbar" role="group" aria-label="视图切换">
      <div class="map-viewbar__segment">
        <button
          type="button"
          :class="{ active: view === 'map' }"
          data-testid="view-map"
          @click="view = 'map'"
        >
          地图
        </button>
        <button
          type="button"
          :class="{ active: view === 'list' }"
          data-testid="view-list"
          @click="view = 'list'"
        >
          列表
        </button>
      </div>
    </div>

    <div
      class="map-workspace__body"
      :class="{ 'map-workspace__body--split': isDesktop && view === 'map' }"
    >
      <!-- 左列结果窗格（桌面常驻；移动端在「列表」视图显示） -->
      <MapResultPane
        v-if="isDesktop || view === 'list'"
        :places="places"
        :statuses="statuses"
        :visible-places="visiblePlaces"
        :loading="loading"
        :error="error"
        :coverage-text="coverage.text"
        :location-state="locationState"
        :filters="activeFilters"
        @update:filters="activeFilters = $event"
        @locate="locate"
        @search="goSearch"
        @open="open"
        @retry="load"
        @clear-filters="activeFilters = []"
        @go-home="goHome"
      />

      <!-- 主画布：地图是页面的主导表面 -->
      <section
        v-if="view === 'map'"
        class="map-canvas"
        data-testid="map"
        data-ui="map-canvas"
        aria-label="规则地图"
      >
        <StateMessage
          v-if="error && !isDesktop"
          kind="ERROR"
          data-testid="map-provider-error"
          title="未能取得附近场所"
          :description="error"
        >
          <template #action>
            <button type="button" class="primary" @click="load">重试</button>
          </template>
        </StateMessage>
        <MockMap
          v-else
          :camera="camera"
          :clusters="clusters"
          :selected-id="selected?.id ?? null"
          @select="onSelectCluster"
        />
      </section>
    </div>

    <!-- 桌面浮动预览：覆盖在地图上的唯一卡片（radius 10–12px + elevation） -->
    <div v-if="isDesktop && view === 'map'" class="map-preview-float">
      <PlacePreview
        :place="selected"
        :status="selected ? (statuses[selected.id] ?? null) : null"
        :snapshot="preview.snapshot"
        :loading="preview.loading"
        :error="preview.error"
      />
    </div>
    <!-- 移动端：选中场所 = 真实 overlay bottom sheet（v0.2.5 §22–24）。 -->
    <MapSelectedSheet
      :open="Boolean(selected) && !isDesktop"
      :place="selected"
      :status="selected ? (statuses[selected.id] ?? null) : null"
      :snapshot="preview.snapshot"
      :loading="preview.loading"
      :error="preview.error"
      @close="
        selected = null;
        syncRoutePlace(null);
      "
    />
  </div>
</template>

<style scoped>
.map-workspace {
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

/* v0.2.5 §25：compact segmented control（非两个独立 pill）。 */
.map-viewbar {
  display: flex;
  justify-content: center;
  padding: var(--pa-space-2) var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}
.map-viewbar__segment {
  display: inline-flex;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  overflow: hidden;
}
.map-viewbar__segment button {
  border: none;
  background: transparent;
  min-height: var(--pa-size-control-md);
  padding: 0 var(--pa-space-4);
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
  cursor: pointer;
}
.map-viewbar__segment button.active {
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-600);
}
.map-viewbar__segment button:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -1px;
}

/* Mobile：body 占满 tabbar 上方视口；map 填充剩余高度（§22）。 */
.map-workspace__body {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-height: 0;
  gap: var(--pa-space-4);
  padding: var(--pa-space-3);
}

/* Desktop map mode: the workspace owns the viewport below the 60px query bar,
   so the spatial canvas remains dominant instead of ending halfway down page. */
.map-workspace__body--split {
  flex-direction: row;
  align-items: stretch;
  gap: 0;
}

.map-workspace__body--split .map-pane {
  flex: 0 0 var(--pa-layout-result-pane);
  border-right: var(--pa-border-width) solid var(--pa-color-border);
  padding-right: var(--pa-space-5);
}

.map-canvas {
  position: relative;
  overflow: hidden;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 320px;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  /* v0.2.7 §8/§9：画布基底退回极浅冷中性纯色 —— MockMap 的抽象城市
     SVG 在其上分层；不再叠加「灰网格+数字」式的 repeating grid。 */
  background: var(--pa-color-map-grid-a);
}

@media (min-width: 768px) {
  .map-workspace__body {
    height: calc(100vh - 60px);
    min-height: 560px;
    padding: var(--pa-space-3);
  }

  .map-workspace__body--split {
    padding: var(--pa-space-3);
  }

  .map-canvas {
    min-height: 0;
  }
}

/* 桌面浮动预览：唯一允许的浮动卡片（freeze §5：map preview 10–12px + light shadow）。 */
.map-preview-float {
  position: fixed;
  right: var(--pa-space-5);
  bottom: var(--pa-space-5);
  /* v0.2.3 §37：selected preview 只一个，w 280–320。 */
  width: min(300px, calc(100% - var(--pa-space-6)));
  max-height: calc(100vh - var(--pa-space-7));
  overflow-y: auto;
  border-radius: var(--pa-radius-md);
  box-shadow: var(--pa-elevation-3);
  z-index: var(--pa-z-sticky);
}
</style>
