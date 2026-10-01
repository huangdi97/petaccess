<script setup lang="ts">
/**
 * PlaceSpacePane — Place Dossier 空间 view（v0.2.4 §22）。
 * zones / entrances / paths / facilities / staff-response location facts。
 * 不放 Rule History（那属于 规则 view）。
 */
import type { PlaceExtras, Zone } from "@petaccess/client-core";
import {
  amenityLabel,
  coexistenceLabel,
  coexistenceValueLabel,
  entranceLabel,
  facilityStateLabel,
  zoneConsumerLine,
} from "../../consumer/labels";

defineProps<{
  zones: Zone[];
  extras: PlaceExtras | null;
}>();
</script>

<template>
  <div data-ui="place-space-view" data-testid="place-space-view">
    <section class="place-section" data-testid="space-zones" data-ui="place-zones">
      <h2 class="place-section__title">空间与区域</h2>
      <p v-if="!zones.length" class="muted">暂无分区域信息。信息不足不代表允许或禁止。</p>
      <div v-for="z in zones" :key="z.id" class="zone-row" data-ui="zone-row">
        <span class="zone-row__name">{{ zoneConsumerLine(z) }}</span>
        <RouterLink
          class="btn-inline"
          :to="`/place/${z.place_id}/reality`"
          data-testid="zone-reality-link"
        >
          查看现场 →
        </RouterLink>
      </div>
    </section>

    <section class="place-section" data-testid="entrances">
      <h2 class="place-section__title">怎么进入</h2>
      <div v-if="!extras?.entrances.length && !extras?.access_paths.length" class="muted">
        暂无入口 / 路径信息
      </div>
      <div v-for="e in extras?.entrances ?? []" :key="e.id" class="zone-row">
        <span class="zone-row__name">
          {{ e.name
          }}<span class="tag" style="margin-left: 6px">{{ entranceLabel(e.entrance_type) }}</span>
        </span>
        <span class="muted">{{ e.access_notes ?? "" }}</span>
      </div>
      <div v-for="p in extras?.access_paths ?? []" :key="p.id" class="zone-row">
        <span>{{ p.from_node }} → {{ p.to_node }}</span>
        <span class="muted">{{ p.name }}</span>
      </div>
    </section>

    <section class="place-section" data-testid="amenities">
      <h2 class="place-section__title">设施</h2>
      <div v-if="!extras?.amenities.length" class="muted">暂无设施记录</div>
      <div class="row">
        <span v-for="a in extras?.amenities ?? []" :key="a.id" class="tag">
          {{ amenityLabel(a.amenity_type) }} · {{ facilityStateLabel(a.status) }}
        </span>
      </div>
    </section>

    <section class="place-section" data-testid="coexistence-location-facts">
      <h2 class="place-section__title">共处边界（空间事实）</h2>
      <div v-if="!extras?.coexistence.length" class="muted">暂无共处边界结构化记录</div>
      <div v-for="c in extras?.coexistence ?? []" :key="c.id" class="zone-row">
        <span>{{ coexistenceLabel(c.attribute) }}</span>
        <span class="muted">
          {{ coexistenceValueLabel(c.value)
          }}<span v-if="c.verified_at"> · {{ c.verified_at.slice(0, 10) }}</span>
        </span>
      </div>
      <div class="notice">共处边界是来自来源的空间事实，不对人作评价。</div>
    </section>
  </div>
</template>

<style scoped>
.place-section {
  margin-bottom: var(--pa-space-5);
}
.place-section__title {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.zone-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: 48px;
  max-height: 64px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.zone-row:last-child {
  border-bottom: none;
}
.zone-row__name {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-1);
  font-size: var(--pa-font-size-base);
}
.tag {
  display: inline-block;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-sm);
  padding: 1px var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}
.notice {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
  background: var(--pa-color-bg-sunken);
  border-radius: var(--pa-radius-control);
  padding: var(--pa-space-2) var(--pa-space-3);
  margin-top: var(--pa-space-2);
}
</style>
