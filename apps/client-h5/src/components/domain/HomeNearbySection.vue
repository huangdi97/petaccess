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
import SkeletonList from "../SkeletonList.vue";
import StateMessage from "../StateMessage.vue";
import StatusBadge from "../StatusBadge.vue";
import { placeTypeLabel } from "@petaccess/client-core";
import { freshnessLineFor } from "../../consumer/rowView";
import type { HomeCard } from "../../composables/useHomeLauncher";

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
  <div>
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
        description="你仍然可以了解 PetAccess 如何区分规则与现场，或者提交第一条线索。"
      >
        <template #action>
          <RouterLink class="primary" to="/map" data-testid="home-empty-map">探索地图</RouterLink>
          <RouterLink class="secondary" to="/contribute" data-testid="home-empty-contribute"
            >贡献线索</RouterLink
          >
        </template>
      </StateMessage>

      <template v-else>
        <p
          v-if="freshness"
          class="muted"
          data-testid="home-freshness"
          style="margin: 0 0 var(--pa-space-2)"
        >
          {{ freshness }}
        </p>

        <h2 class="home-section-title home-section-title--stacked">附近已核验</h2>
        <p class="muted">
          已核验 = 有规则依据。核验范围写清楚（动物 · 区域），不写成对整个场所的结论。
        </p>

        <StateMessage
          v-if="!verified.length"
          kind="PARTIAL"
          data-testid="verified-empty"
          description="这一区域暂无已核验场所。可切换类别、看地图，或改用搜索指定场所名。"
        />

        <div
          v-for="c in verified"
          :key="c.place.id"
          class="home-card"
          :data-testid="'verified-' + c.place.id"
          @click="emit('open', c.place.id)"
        >
          <PlaceResultRow
            :place="c.place"
            :answer="c.facts.answer"
            :answer-error="c.facts.answerError"
            :reality="c.facts.reality"
            :reality-error="c.facts.realityError"
            :species-label="speciesLabel"
            :conditions-label="conditionsLabel"
            class="home-card__row"
          />
          <div class="row home-card__head">
            <div class="muted" :data-testid="'scope-' + c.place.id">已核验：{{ c.scope }}</div>
            <StatusBadge :semantic="c.status" />
          </div>
          <p v-if="c.conditions.length" class="notice" :data-testid="'conditions-' + c.place.id">
            进入前需满足：{{ c.conditions.join("、") }}
          </p>
          <button
            class="pill"
            :data-testid="'why-' + c.place.id"
            @click.stop="emit('why', c.place.id)"
          >
            为什么？
          </button>
        </div>

        <h2 class="home-section-title home-section-title--stacked">规则待核实</h2>
        <p class="muted">尚未核验 ≠ 允许或禁止。这些场所我们目前没有足够依据下结论。</p>
        <div
          v-for="c in pending"
          :key="c.place.id"
          class="home-card"
          :data-testid="'pending-' + c.place.id"
          @click="emit('open', c.place.id)"
        >
          <div class="row home-card__head">
            <div class="home-card__main">
              <strong>{{ c.place.canonical_name }}</strong>
              <div class="muted">{{ placeTypeLabel(c.place.place_type) }}</div>
            </div>
            <StatusBadge :semantic="c.status" />
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
/* Nearby rows — divider-based (PlaceResultRow + subtle separators), NOT cards. */
.home-card {
  cursor: pointer;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-card:last-child {
  border-bottom: none;
}

.home-card__head {
  justify-content: space-between;
}

.home-card__row {
  margin-bottom: var(--pa-space-2);
}

.home-section-title--stacked {
  margin: var(--pa-space-5) 0 var(--pa-space-2);
}

.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}
</style>
