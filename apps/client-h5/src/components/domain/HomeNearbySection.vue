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

        <h2 class="home-section-title home-section-title--stacked">附近已有依据</h2>

        <p v-if="!verified.length" class="muted" data-testid="verified-empty">
          这一区域暂无有依据的场所。可看地图，或改用搜索指定场所名。
        </p>

        <!-- v0.2.4 §30：divider rows，非卡。 -->
        <div
          v-for="c in verified"
          :key="c.place.id"
          class="home-row"
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
          />
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
        <h2 class="home-section-title home-section-title--stacked">附近待补充</h2>
        <p class="muted">这些场所我们目前没有足够依据下结论，信息不足不等于允许或禁止。</p>
        <div
          v-for="c in pending"
          :key="c.place.id"
          class="home-row"
          :data-testid="'pending-' + c.place.id"
          @click="emit('open', c.place.id)"
        >
          <div class="row home-row__head">
            <strong>{{ c.place.canonical_name }}</strong>
          </div>
          <span class="muted">{{ placeTypeLabel(c.place.place_type) }}</span>
          <span class="home-row__pending-copy">信息不足</span>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
/* v0.2.4 §30：附近/待核实 = divider rows，非卡（无圆角/无阴影/无 surface 填充）。 */
.home-row {
  cursor: pointer;
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  margin-bottom: 0;
  transition: background-color var(--pa-motion-fast) var(--pa-motion-ease);
}

.home-row:hover {
  background: var(--pa-color-surface-interactive);
}

.home-row:last-child {
  border-bottom: none;
}

.home-row__head {
  justify-content: space-between;
}

.home-row__pending-copy {
  display: block;
  margin-top: var(--pa-space-1);
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-secondary);
}

.home-row__evidence-link {
  margin-top: var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
}

.home-section-title--stacked {
  margin: var(--pa-space-5) 0 var(--pa-space-2);
}

.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
</style>
