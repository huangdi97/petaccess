<script setup lang="ts">
/**
 * PlaceRealityPane — Place Dossier 现场 view（v0.2.4 §24）。
 * 不做第二套 Reality UI：复用 RealityEventLog（可内嵌前几条 + link full route）。
 */
import type { ObservationView, Zone } from "@petaccess/client-core";
import RealityEventLog from "../domain/RealityEventLog.vue";

defineProps<{
  observations: ObservationView[];
  zones: Zone[];
  placeId: string;
}>();
</script>

<template>
  <div data-ui="place-reality-view" data-testid="place-reality-view">
    <RealityEventLog :observations="observations" :zones="zones" :place-id="placeId" />
    <RouterLink
      class="btn-inline"
      :to="`/place/${placeId}/reality`"
      data-testid="place-reality-full-link"
    >
      查看全部现场记录 →
    </RouterLink>
  </div>
</template>
