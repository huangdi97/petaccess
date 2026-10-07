<script setup lang="ts">
/**
 * PlacePreview — selected place preview over the map (§32, v0.2.4).
 *
 * §32 selected preview 只显示：
 *   Place / Type·distance /
 *   Primary status + key condition /
 *   最近现场 /
 *   查看场所 →
 * rule count / reality count / evidence count / conflict-analysis paragraph
 * 一律不上浮（进 Place dossier 详情）。
 *
 * Data flows in as props from the map workspace (CoexistenceSnapshot SSOT).
 */
import { computed } from "vue";
import {
  placeTypeLabel,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../../answer";
import { coexistenceRealityLine } from "../../consumer/rowView";
import StatusBadge from "../StatusBadge.vue";
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";

const props = withDefaults(
  defineProps<{
    place: PlaceSummary | null;
    status?: string | null;
    snapshot?: CoexistenceSnapshot | null;
    loading?: boolean;
    error?: string;
    mapLensName?: string;
    mapLensLabel?: string;
  }>(),
  { status: null, snapshot: null, loading: false, error: "", mapLensName: "", mapLensLabel: "" },
);

const answer = computed(() => props.snapshot?.rule_answer ?? null);
const statusKey = computed(() => answerStatusKey(answer.value));
const keyCondition = computed(() => answerConditions(answer.value)[0] ?? "");
const realityLine = computed(() =>
  props.loading
    ? "加载现场摘要中…"
    : props.error
      ? "现场摘要暂时无法取得"
      : coexistenceRealityLine(props.snapshot, props.snapshot?.reality_answer),
);
const metaLine = computed(() => {
  const parts: string[] = [placeTypeLabel(props.place?.place_type ?? "")];
  if (props.place?.distance_m) parts.push(`${Math.round(props.place.distance_m)}m`);
  return parts.join(" · ");
});
</script>

<template>
  <section class="place-preview" data-testid="place-preview" :aria-busy="loading">
    <template v-if="place">
      <!-- §32：Place + Type·distance -->
      <header class="place-preview__head">
        <PlaceTypeGlyph :place-type="place.place_type" />
        <div class="place-preview__identity">
          <h2 class="place-preview__name">{{ place.canonical_name }}</h2>
          <p class="place-preview__muted">{{ metaLine }}</p>
        </div>
      </header>

      <div
        v-if="mapLensLabel"
        class="place-preview__lens place-preview__lens--primary"
        data-testid="preview-map-lens"
      >
        <span class="place-preview__label">当前地图 · {{ mapLensName }}</span>
        <strong>{{ mapLensLabel }}</strong>
      </div>

      <!-- Rule Lens: rule is primary. Other lenses: rule remains visible but
           secondary, so green/allowed semantics never become the visible
           meaning of a Reality/Facility/Divergence marker. -->
      <div
        class="place-preview__decision"
        :class="{ 'place-preview__decision--secondary': Boolean(mapLensLabel) }"
        data-testid="preview-verdict"
      >
        <span v-if="mapLensLabel" class="place-preview__label">规则</span>
        <StatusBadge v-if="!mapLensLabel" :semantic="statusKey" />
        <p class="place-preview__verdict-text" data-testid="preview-verdict-text">
          {{ answerVerdictLabel(answer) }}
        </p>
        <p v-if="keyCondition" class="place-preview__muted" data-testid="preview-condition">
          需满足：{{ keyCondition }}
        </p>
      </div>

      <!-- §32：最近现场 one line -->
      <div class="place-preview__row">
        <span class="place-preview__label">现场概览</span>
        <span class="place-preview__value" data-testid="preview-reality">{{ realityLine }}</span>
      </div>

      <!-- §32：查看场所 → -->
      <footer class="place-preview__foot">
        <RouterLink
          class="btn primary place-preview__cta"
          :to="`/place/${place.id}`"
          data-testid="preview-open"
        >
          查看场所 →
        </RouterLink>
      </footer>
    </template>

    <p v-else class="place-preview__hint" data-testid="preview-empty">
      选择地图上的一个场所，查看准入结论与最近现场。
    </p>
  </section>
</template>

<style scoped src="./PlacePreview.css"></style>
