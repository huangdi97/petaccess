<script setup lang="ts">
/**
 * Nearby places whose enrichment transport failed.
 *
 * This is deliberately not the "附近待补充" group: network/API failure is not
 * a domain UNKNOWN and must never be presented as missing Rule/Reality evidence.
 */
import type { HomeCard } from "../../composables/useHomeLauncher";
import type { ConsumerLens } from "../../consumer/rowView";
import PlaceResultRow from "./PlaceResultRow.vue";
import PlaceSceneFrame from "./PlaceSceneFrame.vue";

defineProps<{
  unavailable: HomeCard[];
  speciesLabel: string;
  conditionsLabel: Record<string, string>;
  interest: ConsumerLens;
}>();

const emit = defineEmits<{ open: [id: string] }>();
</script>

<template>
  <section v-if="unavailable.length" class="home-unavailable" data-ui="home-unavailable">
    <h2 class="home-section-title">附近暂时无法完整判断</h2>
    <p class="muted home-unavailable__note">
      这些场所已经收录，但部分规则或现场数据暂时无法取得；这不是“信息不足”的结论。
    </p>
    <button
      v-for="card in unavailable.slice(0, 2)"
      :key="card.place.id"
      type="button"
      class="home-unavailable__row"
      :data-testid="'unavailable-' + card.place.id"
      :aria-label="`查看场所 ${card.place.canonical_name}`"
      @click="emit('open', card.place.id)"
    >
      <PlaceSceneFrame
        class="home-unavailable__scene"
        :src="null"
        alt=""
        :place-type="card.place.place_type"
        variant="compact"
      />
      <PlaceResultRow
        :place="card.place"
        :show-identity-glyph="false"
        :answer="card.facts.answer"
        :answer-error="card.facts.answerError"
        :reality="card.facts.reality"
        :snapshot="card.facts.snapshot"
        :reality-error="card.facts.realityError"
        :species-label="speciesLabel"
        :conditions-label="conditionsLabel"
        :lens="interest"
      />
    </button>
  </section>
</template>

<style scoped>
.home-unavailable {
  margin-top: var(--pa-space-5);
}

.home-section-title {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.home-unavailable__note {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-md);
}

.home-unavailable__row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: var(--pa-space-4);
  width: 100%;
  padding: var(--pa-space-4) 0;
  border: 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.home-unavailable__row:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}

.home-unavailable__scene {
  --scene-frame-compact-width: 112px;
  --scene-frame-compact-height: 84px;
  --scene-frame-compact-empty-width: 112px;
  --scene-frame-compact-empty-height: 84px;
  --scene-frame-compact-mobile-width: 88px;
  --scene-frame-compact-mobile-height: 66px;
  --scene-frame-compact-empty-mobile-width: 88px;
  --scene-frame-compact-empty-mobile-height: 66px;
}

@media (max-width: 767px) {
  .home-unavailable__row {
    grid-template-columns: 88px minmax(0, 1fr);
    gap: var(--pa-space-3);
  }
}
</style>
