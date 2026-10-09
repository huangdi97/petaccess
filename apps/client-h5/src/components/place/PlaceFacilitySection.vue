<script setup lang="ts">
import { computed } from "vue";
import type { FacilitySummaryItem, RealityEventView, Zone } from "@petaccess/client-core";
import {
  animalFacilityLabel,
  facilityAccessModeLabel,
  facilityPurposeIsConfirmed,
  facilityPurposeLabel,
  facilitySecurityLabel,
  facilityStateLabel,
  facilitySupervisionLabel,
  verifiedBooleanLabel,
  zoneConsumerLine,
} from "../../consumer/labels";
import { displayRealityTime } from "../../consumer/realityEvent";

const props = defineProps<{
  zones: Zone[];
  facilitySummary: FacilitySummaryItem[];
  events: RealityEventView[];
}>();

const facilityEvents = computed(() =>
  props.events.filter(
    (event) =>
      event.event_type === "animal_facility" &&
      event.time_evidence_state !== "publication_time_only",
  ),
);

function facilityZone(event: RealityEventView): string {
  if (!event.zone_id) return "场所范围";
  const zone = props.zones.find((item) => item.id === event.zone_id);
  return zone ? zoneConsumerLine(zone) : "分区待确认";
}
</script>

<template>
  <section class="place-section" data-testid="animal-facilities" data-ui="place-animal-facilities">
    <h2 class="place-section__title">动物设施</h2>

    <template v-if="facilityEvents.length">
      <article
        v-for="event in facilityEvents"
        :key="event.id"
        class="facility-record"
        :class="{ 'facility-record--disputed': event.dispute_open }"
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
          <dt>记录时状态</dt>
          <dd>{{ facilityStateLabel(event.facility_state) }}</dd>
          <dt>记录所述日期</dt>
          <dd>{{ displayRealityTime(event.event_at) }}</dd>
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
          <dd>{{ facilitySupervisionLabel(event.facility_supervision_state) }}</dd>
          <dt>安全 / 锁闭</dt>
          <dd>{{ facilitySecurityLabel(event.facility_security_or_lock_state) }}</dd>
          <dt>最近核验</dt>
          <dd>
            {{ event.last_verified_at ? displayRealityTime(event.last_verified_at) : "未记录" }}
          </dd>
          <template v-if="event.dispute_open">
            <dt>争议状态</dt>
            <dd>异议处理中 · 原记录保留等待复核</dd>
          </template>
        </dl>
      </article>
    </template>

    <template v-else>
      <p v-if="!facilitySummary.length" class="muted">暂无经核验的动物设施记录。</p>
      <div
        v-for="item in facilitySummary"
        :key="`${item.facility_type}:${item.purpose_state}:${item.zone_id ?? 'place'}`"
        class="facility-summary-row"
        data-testid="animal-facility-summary-row"
      >
        <strong>
          {{
            facilityPurposeIsConfirmed(item.purpose_state)
              ? animalFacilityLabel(item.facility_type)
              : "疑似动物相关设施"
          }}
        </strong>
        <span class="muted">
          <template v-if="item.zone_name">{{ item.zone_name }} · </template>
          {{
            facilityPurposeIsConfirmed(item.purpose_state)
              ? `记录状态：${facilityStateLabel(item.operational_state)}`
              : "用途待核验"
          }}
          · {{ item.count }} 处
          <template v-if="item.disputed_count"> · {{ item.disputed_count }} 条异议处理中</template>
          <template v-if="item.last_verified_at">
            · 最近核验 {{ item.last_verified_at.slice(0, 10) }}</template
          >
        </span>
      </div>
    </template>

    <p class="facility-note">
      设施记录只说明有来源报告过相关设施，记录时状态不保证当前仍可用；不等于允许动物进入，也不构成安全或动物福利保证。
    </p>
  </section>
</template>

<style scoped src="./PlaceFacilitySection.css"></style>
