<script setup lang="ts">
import { computed } from "vue";
import type { HomeCard } from "../../composables/useHomeLauncher";
import type { ConsumerLens } from "../../consumer/rowView";
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";
import {
  compareHomeDigest,
  homeDigestDivergence,
  homeDigestHasUsefulFact,
  homeDigestHeadline,
  homeDigestMeta,
} from "../../consumer/homeDigest";

const props = withDefaults(
  defineProps<{
    verified: HomeCard[];
    pending: HomeCard[];
    interest?: ConsumerLens;
    section?: "recommend" | "divergence";
  }>(),
  { interest: "", section: "recommend" },
);

const emit = defineEmits<{ open: [id: string] }>();
const cards = computed(() => [...props.verified, ...props.pending]);
const recommendationTitle = computed(() => (props.interest ? "按你的关注推荐" : "近期值得先看"));
const recommendationNote = computed(() =>
  props.interest
    ? "先显示与你当前关注更相关的事实；不代表场所好坏。"
    : "先显示最近有现场事实或较完整依据的场所；不代表场所好坏。",
);
const recommended = computed(() =>
  [...cards.value]
    .filter(homeDigestHasUsefulFact)
    .sort((a, b) => compareHomeDigest(a, b, props.interest))
    .slice(0, 1),
);
const divergences = computed(() =>
  cards.value
    .filter((card) => {
      const state = card.facts.snapshot?.divergence?.state;
      return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
    })
    .slice(0, 3),
);
</script>

<template>
  <section
    v-if="section === 'recommend' && recommended.length"
    class="home-recommend"
    data-ui="home-recommend"
  >
    <div class="home-digest-head">
      <h2 class="home-digest-title">{{ recommendationTitle }}</h2>
      <p class="home-digest-note muted">{{ recommendationNote }}</p>
    </div>
    <button
      v-for="card in recommended"
      :key="'recommend-' + card.place.id"
      type="button"
      class="home-recommend__row"
      :data-testid="'recommend-' + card.place.id"
      @click="emit('open', card.place.id)"
    >
      <PlaceTypeGlyph :place-type="card.place.place_type" size="sm" />
      <strong class="home-recommend__name">{{ card.place.canonical_name }}</strong>
      <span class="home-recommend__headline">{{ homeDigestHeadline(card, interest) }}</span>
      <span v-if="homeDigestMeta(card)" class="muted home-recommend__meta">
        {{ homeDigestMeta(card) }}
      </span>
    </button>
  </section>

  <section
    v-if="section === 'divergence' && divergences.length"
    class="home-divergence"
    data-ui="home-divergence"
  >
    <h2 class="home-digest-title">规则与现场不一致</h2>
    <button
      v-for="card in divergences"
      :key="'divergence-' + card.place.id"
      type="button"
      class="home-divergence__row"
      :data-testid="'divergence-' + card.place.id"
      @click="emit('open', card.place.id)"
    >
      <strong>{{ card.place.canonical_name }}</strong>
      <span>{{ homeDigestDivergence(card) }}</span>
    </button>
  </section>
</template>

<style scoped src="./HomeDigestHighlights.css"></style>
