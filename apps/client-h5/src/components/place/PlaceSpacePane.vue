<script setup lang="ts">
import type {
  FacilitySummaryItem,
  PlaceExtras,
  RealityEventView,
  Zone,
} from "@petaccess/client-core";
import {
  amenityLabel,
  coexistenceLabel,
  coexistenceValueLabel,
  entranceLabel,
  facilityStateLabel,
  zoneConsumerLine,
} from "../../consumer/labels";
import PlaceFacilitySection from "./PlaceFacilitySection.vue";

const props = defineProps<{
  zones: Zone[];
  extras: PlaceExtras | null;
  facilitySummary: FacilitySummaryItem[];
  events: RealityEventView[];
}>();
</script>

<template>
  <div data-ui="place-space-view" data-testid="place-space-view">
    <section class="place-section" data-testid="space-zones" data-ui="place-zones">
      <h2 class="place-section__title">空间与区域</h2>
      <p v-if="!zones.length" class="muted">暂无分区域信息。信息不足不代表允许或禁止。</p>
      <div v-for="zone in zones" :key="zone.id" class="zone-row" data-ui="zone-row">
        <span class="zone-row__name">{{ zoneConsumerLine(zone) }}</span>
        <RouterLink class="btn-inline" :to="`/place/${zone.place_id}/reality`">
          查看现场 →
        </RouterLink>
      </div>
    </section>

    <section class="place-section" data-testid="entrances">
      <h2 class="place-section__title">怎么进入</h2>
      <p v-if="!extras?.entrances.length && !extras?.access_paths.length" class="muted">
        暂无入口 / 路径信息。
      </p>
      <div v-for="entrance in extras?.entrances ?? []" :key="entrance.id" class="zone-row">
        <span class="zone-row__name">
          {{ entrance.name }}
          <span class="muted zone-row__meta">· {{ entranceLabel(entrance.entrance_type) }}</span>
        </span>
        <span class="muted">{{ entrance.access_notes ?? "" }}</span>
      </div>
      <div v-for="path in extras?.access_paths ?? []" :key="path.id" class="zone-row">
        <span>{{ path.from_node }} → {{ path.to_node }}</span>
        <span class="muted">{{ path.name }}</span>
      </div>
    </section>

    <PlaceFacilitySection :zones="zones" :facility-summary="facilitySummary" :events="events" />

    <section class="place-section" data-testid="amenities">
      <h2 class="place-section__title">其他场所设施</h2>
      <p v-if="!extras?.amenities.length" class="muted">暂无其他设施记录。</p>
      <div v-for="amenity in extras?.amenities ?? []" :key="amenity.id" class="zone-row">
        <span class="zone-row__name">{{ amenityLabel(amenity.amenity_type) }}</span>
        <span class="muted">{{ facilityStateLabel(amenity.status) }}</span>
      </div>
    </section>

    <section class="place-section" data-testid="coexistence-location-facts">
      <h2 class="place-section__title">空间事实</h2>
      <p v-if="!extras?.coexistence.length" class="muted">暂无共处边界结构化记录。</p>
      <div v-for="item in extras?.coexistence ?? []" :key="item.id" class="zone-row">
        <span>{{ coexistenceLabel(item.attribute) }}</span>
        <span class="muted">
          {{ coexistenceValueLabel(item.value) }}
          <template v-if="item.verified_at"> · {{ item.verified_at.slice(0, 10) }}</template>
        </span>
      </div>
      <p class="space-note">这些信息描述场所空间本身，不代表正式准入规则。</p>
    </section>
  </div>
</template>

<style scoped src="./PlaceSpacePane.css"></style>
