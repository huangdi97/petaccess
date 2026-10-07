<script setup lang="ts">
import { computed } from "vue";
import type {
  FacilitySummaryItem,
  PlaceExtras,
  RealityEventView,
  Zone,
} from "@petaccess/client-core";
import {
  amenityLabel,
  animalFacilityLabel,
  coexistenceLabel,
  coexistenceValueLabel,
  entranceLabel,
  facilityAccessModeLabel,
  facilityPurposeIsConfirmed,
  facilityPurposeLabel,
  facilityStateLabel,
  verifiedBooleanLabel,
  zoneConsumerLine,
} from "../../consumer/labels";
import { displayRealityTime } from "../../consumer/realityEvent";

const props = defineProps<{
  zones: Zone[];
  extras: PlaceExtras | null;
  facilitySummary: FacilitySummaryItem[];
  events: RealityEventView[];
}>();

const facilityEvents = computed(() =>
  props.events.filter((event) => event.event_type === "animal_facility"),
);

function facilityZone(event: RealityEventView): string {
  if (!event.zone_id) return "场所范围";
  const zone = props.zones.find((item) => item.id === event.zone_id);
  return zone ? zoneConsumerLine(zone) : "分区待确认";
}
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

    <section
      class="place-section"
      data-testid="animal-facilities"
      data-ui="place-animal-facilities"
    >
      <h2 class="place-section__title">动物设施</h2>

      <template v-if="facilityEvents.length">
        <article
          v-for="event in facilityEvents"
          :key="event.id"
          class="facility-record"
          data-testid="animal-facility-record"
        >
          <header class="facility-record__head">
            <strong>
              {{
                facilityPurposeIsConfirmed(event.facility_purpose_state)
                  ? animalFacilityLabel(event.facility_type)
                  : "疑似动物相关设施"
              }}
            </strong>
            <span class="facility-record__where">{{ facilityZone(event) }}</span>
          </header>
          <dl class="facility-facts">
            <dt>用途依据</dt>
            <dd>{{ facilityPurposeLabel(event.facility_purpose_state) }}</dd>
            <dt>当前状态</dt>
            <dd>{{ facilityStateLabel(event.facility_state) }}</dd>
            <dt>使用方式</dt>
            <dd>{{ facilityAccessModeLabel(event.facility_access_mode) }}</dd>
            <template v-if="event.facility_capacity != null">
              <dt>容量</dt>
              <dd>{{ event.facility_capacity }}</dd>
            </template>
            <template v-if="event.facility_size_limit">
              <dt>体型限制</dt>
              <dd>{{ event.facility_size_limit }}</dd>
            </template>
            <dt>遮雨</dt>
            <dd>{{ verifiedBooleanLabel(event.facility_weather_protection) }}</dd>
            <dt>遮阳</dt>
            <dd>{{ verifiedBooleanLabel(event.facility_shade) }}</dd>
            <dt>通风</dt>
            <dd>{{ verifiedBooleanLabel(event.facility_ventilation) }}</dd>
            <dt>饮水</dt>
            <dd>{{ verifiedBooleanLabel(event.facility_water_available) }}</dd>
            <dt>看护</dt>
            <dd>{{ event.facility_supervision_state || "未确认" }}</dd>
            <dt>安全 / 锁闭</dt>
            <dd>{{ event.facility_security_or_lock_state || "未确认" }}</dd>
            <dt>最近核验</dt>
            <dd>
              {{ event.last_verified_at ? displayRealityTime(event.last_verified_at) : "未记录" }}
            </dd>
          </dl>
        </article>
      </template>

      <template v-else>
        <p v-if="!facilitySummary.length" class="muted">暂无经核验的动物设施记录。</p>
        <div
          v-for="item in facilitySummary"
          :key="`${item.facility_type}:${item.purpose_state}:${item.zone_id ?? 'place'}`"
          class="zone-row"
          data-testid="animal-facility-summary-row"
        >
          <span class="zone-row__name">
            {{
              facilityPurposeIsConfirmed(item.purpose_state)
                ? animalFacilityLabel(item.facility_type)
                : "疑似动物相关设施"
            }}
          </span>
          <span class="muted">
            <template v-if="item.zone_name">{{ item.zone_name }} · </template>
            {{
              facilityPurposeIsConfirmed(item.purpose_state)
                ? facilityStateLabel(item.operational_state)
                : "用途待核验"
            }}
            · {{ item.count }} 处
            <template v-if="item.last_verified_at">
              · 最近核验 {{ item.last_verified_at.slice(0, 10) }}
            </template>
          </span>
        </div>
      </template>

      <p class="facility-note">
        设施存在只说明这里观察到相关设施；不等于允许动物进入，也不构成安全或动物福利保证。
      </p>
    </section>

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
