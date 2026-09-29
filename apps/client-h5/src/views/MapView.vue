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
import BottomSheet from "../components/BottomSheet.vue";
import MapResultPane from "../components/domain/MapResultPane.vue";
import MockMap from "../components/MockMap.vue";
import PlacePreview from "../components/domain/PlacePreview.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import StatusBadge from "../components/StatusBadge.vue";
import StateMessage from "../components/StateMessage.vue";
import { placeTypeLabel } from "@petaccess/client-core";
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
  <div class="map-workspace" data-testid="map-workspace" data-ui="map-shell">
    <h1 class="visually-hidden">规则地图</h1>
    <QueryContextBar />

    <div class="map-viewbar" role="group" aria-label="视图切换">
      <button type="button" class="pill" data-testid="view-map" @click="view = 'map'">地图</button>
      <button
        type="button"
        class="pill"
        :class="{ active: view === 'list' }"
        data-testid="view-list"
        @click="view = 'list'"
      >
        列表
      </button>
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

    <!-- 移动端：选中场所的底部面板 -->
    <BottomSheet
      :open="Boolean(selected) && !isDesktop"
      :title="selected?.canonical_name ?? null"
      @close="
        selected = null;
        syncRoutePlace(null);
      "
    >
      <template v-if="selected">
        <div class="muted">
          {{ placeTypeLabel(selected.place_type) }} ·
          {{ selected.canonical_address ?? "地址未收录" }}
        </div>
        <div style="margin: 8px 0">
          <StatusBadge :semantic="statuses[selected.id] ?? 'UNKNOWN'" block />
        </div>
        <div class="row">
          <button class="primary" data-testid="sheet-open-detail" @click="open(selected.id)">
            查看场所详情
          </button>
          <button
            @click="
              selected = null;
              syncRoutePlace(null);
            "
          >
            返回地图
          </button>
        </div>
      </template>
    </BottomSheet>
  </div>
</template>

<style scoped>
.map-workspace {
  min-height: 100%;
}

.map-viewbar {
  display: flex;
  gap: var(--pa-space-2);
  padding: var(--pa-space-2) var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
}

.map-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-4);
  padding: var(--pa-space-4);
}

/* Desktop map mode: 400px result pane + the map canvas taking the rest. */
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

/* 地图画布：主导表面。flex:1 占用剩余宽度，min-height 480px 保证高。 */
.map-canvas {
  position: relative;
  overflow: hidden;
  flex: 1;
  min-width: 0;
  min-height: 480px;
  border: var(--pa-border-width) solid var(--pa-color-border);
  background:
    repeating-linear-gradient(
      0deg,
      var(--pa-color-map-grid-a) 0 24px,
      var(--pa-color-map-grid-b) 24px 25px
    ),
    repeating-linear-gradient(
      90deg,
      var(--pa-color-map-grid-a) 0 24px,
      var(--pa-color-map-grid-b) 24px 25px
    );
}

/* 桌面浮动预览：唯一允许的浮动卡片（freeze §5：map preview 10–12px + light shadow）。 */
.map-preview-float {
  position: fixed;
  right: var(--pa-space-5);
  bottom: var(--pa-space-5);
  width: min(360px, calc(100% - var(--pa-space-6)));
  max-height: calc(100vh - var(--pa-space-7));
  overflow-y: auto;
  border-radius: var(--pa-radius-md);
  box-shadow: var(--pa-elevation-3);
  z-index: var(--pa-z-sticky);
}
</style>
