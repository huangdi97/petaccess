<script setup lang="ts">
import type { HomeCard } from "../../composables/useHomeLauncher";
import { placeTypeLabel } from "@petaccess/client-core";
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";
import StatusBadge from "../StatusBadge.vue";

defineProps<{ pending: HomeCard[] }>();
const emit = defineEmits<{ open: [id: string] }>();
</script>

<template>
  <template v-if="pending.length">
    <h2 class="home-section-title home-section-title--stacked">附近待补充</h2>
    <p class="muted">这些场所目前没有足够依据下结论，信息不足不等于允许或禁止。</p>
    <div
      v-for="card in pending.slice(0, 2)"
      :key="card.place.id"
      class="home-row"
      :data-testid="'pending-' + card.place.id"
      @click="emit('open', card.place.id)"
    >
      <div class="home-row__pending-identity">
        <PlaceTypeGlyph :place-type="card.place.place_type" />
        <div class="home-row__pending-copy">
          <div class="row home-row__head">
            <strong>{{ card.place.canonical_name }}</strong>
            <StatusBadge :semantic="card.status" />
          </div>
          <span class="muted">{{ placeTypeLabel(card.place.place_type) }}</span>
        </div>
      </div>
    </div>
  </template>
</template>

<style scoped>
.home-row {
  cursor: pointer;
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  transition: background-color var(--pa-motion-fast) var(--pa-motion-ease);
}
.home-row:hover {
  background: var(--pa-color-surface-interactive);
}
.home-row__head {
  justify-content: space-between;
}
.home-row__pending-identity {
  display: flex;
  align-items: flex-start;
  gap: var(--pa-space-3);
  min-width: 0;
}
.home-row__pending-copy {
  flex: 1 1 auto;
  min-width: 0;
}
.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.home-section-title--stacked {
  margin: var(--pa-space-5) 0 var(--pa-space-2);
}
</style>
