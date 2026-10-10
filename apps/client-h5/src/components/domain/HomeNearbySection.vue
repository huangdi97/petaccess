<script setup lang="ts">
/**
 * HomeNearbySection — the verified/pending nearby list (freeze §9).
 *
 * Pure presentation over the launcher's derived rows: divider-led rows via
 * PlaceResultRow plus scope / conditions / why — never cards. Loading,
 * transport error, empty and freshness (offline/stale) states are explicit.
 */
import { computed } from "vue";
import { type PlaceSummary } from "@petaccess/client-core";
import PlaceResultRow from "./PlaceResultRow.vue";
import PlaceSceneFrame from "./PlaceSceneFrame.vue";
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";
import SkeletonList from "../SkeletonList.vue";
import StateMessage from "../StateMessage.vue";
import { freshnessLineFor, type ConsumerLens } from "../../consumer/rowView";
import type { HomeCard } from "../../composables/useHomeLauncher";
import HomeDigestHighlights from "./HomeDigestHighlights.vue";
import HomePendingSection from "./HomePendingSection.vue";

const props = defineProps<{
  loading: boolean;
  error: string;
  places: PlaceSummary[];
  verified: HomeCard[];
  pending: HomeCard[];
  listStale: boolean;
  nearbyFetchedAtMs: number | null;
  online: boolean;
  speciesLabel: string;
  conditionsLabel: Record<string, string>;
  interest: ConsumerLens;
  featuredSceneMediaUrl?: string | null;
}>();

const emit = defineEmits<{
  open: [id: string];
  why: [id: string];
  retry: [];
}>();

const freshness = computed(() =>
  freshnessLineFor(props.listStale, props.nearbyFetchedAtMs, !props.online),
);
</script>

<template>
  <div data-ui="home-nearby">
    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" title="未能取得附近场所" :description="error">
      <template #action>
        <button class="primary" @click="emit('retry')">重试</button>
      </template>
    </StateMessage>

    <template v-else>
      <StateMessage
        v-if="!places.length"
        kind="EMPTY"
        data-testid="home-empty"
        title="当前还没有已发布的场所数据"
        description="你仍然可以通过地图或搜索确认是否有已收录场所。贡献规则、现场与纠错线索需要先绑定到一个已收录场所。"
      >
        <template #action>
          <RouterLink class="primary" to="/map" data-testid="home-empty-map">探索地图</RouterLink>
          <RouterLink class="secondary" to="/search" data-testid="home-empty-search">
            搜索场所
          </RouterLink>
        </template>
      </StateMessage>

      <template v-else>
        <p v-if="freshness" class="muted home-freshness" data-testid="home-freshness">
          {{ freshness }}
        </p>

        <HomeDigestHighlights
          section="recommend"
          :interest="interest"
          :verified="verified"
          :pending="pending"
          @open="emit('open', $event)"
        />

        <h2 class="home-section-title home-section-title--stacked">规则与现场速览</h2>

        <p v-if="!verified.length" class="muted" data-testid="verified-empty">
          这一区域暂无有依据的场所。可看地图，或改用搜索指定场所名。
        </p>

        <!-- v0.2.4 §30：divider rows，非卡。 -->
        <div
          v-for="(c, index) in verified.slice(0, 3)"
          :key="c.place.id"
          class="home-row"
          :data-testid="'verified-' + c.place.id"
        >
          <button
            type="button"
            class="home-row__open"
            :aria-label="`查看场所 ${c.place.canonical_name}`"
            @click="emit('open', c.place.id)"
          >
            <div
              class="home-row__content home-row__content--with-scene"
            >
              <PlaceSceneFrame
                v-if="index === 0 && featuredSceneMediaUrl"
                class="home-row__scene"
                :src="featuredSceneMediaUrl"
                :alt="`场所场景：${c.place.canonical_name}`"
                variant="compact"
                data-testid="home-scene-media"
              />
              <PlaceTypeGlyph
                v-else
                class="home-row__scene home-row__scene--glyph"
                :place-type="c.place.place_type"
                size="lg"
                data-testid="home-scene-fallback"
              />
              <PlaceResultRow
                :place="c.place"
                :show-identity-glyph="false"
                :answer="c.facts.answer"
                :answer-error="c.facts.answerError"
                :reality="c.facts.reality"
                :snapshot="c.facts.snapshot"
                :reality-error="c.facts.realityError"
                :species-label="speciesLabel"
                :conditions-label="conditionsLabel"
              />
            </div>
          </button>
          <div v-if="c.facts.answer" class="home-row__evidence-link">
            <RouterLink
              class="btn-inline"
              :to="`/place/${c.place.id}/why`"
              :data-testid="'why-' + c.place.id"
              @click.stop
            >
              查看依据 →
            </RouterLink>
          </div>
        </div>
        <HomePendingSection :pending="pending" @open="emit('open', $event)" />

        <RouterLink
          v-if="verified.length > 3 || pending.length > 2"
          class="home-more btn-inline"
          to="/map"
        >
          在地图查看全部附近场所 →
        </RouterLink>

        <HomeDigestHighlights
          section="divergence"
          :interest="interest"
          :verified="verified"
          :pending="pending"
          @open="emit('open', $event)"
        />
      </template>
    </template>
  </div>
</template>

<style scoped src="./HomeNearbySection.css"></style>
