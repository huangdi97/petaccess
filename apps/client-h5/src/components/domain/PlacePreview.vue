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
import { realityStateLabel } from "../../reality";
import StatusBadge from "../StatusBadge.vue";

const props = withDefaults(
  defineProps<{
    place: PlaceSummary | null;
    status?: string | null;
    snapshot?: CoexistenceSnapshot | null;
    loading?: boolean;
    error?: string;
  }>(),
  { status: null, snapshot: null, loading: false, error: "" },
);

const answer = computed(() => props.snapshot?.rule_answer ?? null);
const statusKey = computed(() => answerStatusKey(answer.value));
const keyCondition = computed(() => answerConditions(answer.value)[0] ?? "");
const realityLine = computed(() =>
  props.loading
    ? "加载现场摘要中…"
    : props.error
      ? "现场摘要暂时无法取得"
      : props.snapshot?.reality_answer
        ? realityStateLabel(props.snapshot.reality_answer)
        : "暂无足够现场记录",
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
        <h2 class="place-preview__name">{{ place.canonical_name }}</h2>
        <p class="place-preview__muted">{{ metaLine }}</p>
      </header>

      <!-- §32：Primary status + key condition -->
      <div class="place-preview__decision" data-testid="preview-verdict">
        <StatusBadge :semantic="statusKey" />
        <p class="place-preview__verdict-text" data-testid="preview-verdict-text">
          {{ answerVerdictLabel(answer) }}
        </p>
        <p v-if="keyCondition" class="place-preview__muted" data-testid="preview-condition">
          需满足：{{ keyCondition }}
        </p>
      </div>

      <!-- §32：最近现场 one line -->
      <div class="place-preview__row">
        <span class="place-preview__label">最近现场</span>
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

<style scoped>
/* §10：map selected preview = 允许的 floating card；半径 10–12 + elevation。 */
.place-preview {
  border: 1px solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
  padding: var(--pa-space-5);
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
  min-width: 0;
}
.place-preview__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.place-preview__name {
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
  margin: 0;
}
.place-preview__muted {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
  line-height: var(--pa-line-height-base);
}
.place-preview__decision {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--pa-space-1);
}
.place-preview__verdict-text {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  color: var(--pa-color-text-primary);
}
.place-preview__row {
  display: flex;
  gap: var(--pa-space-3);
  align-items: baseline;
}
.place-preview__label {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
  flex-shrink: 0;
}
.place-preview__value {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
  line-height: var(--pa-line-height-base);
  min-width: 0;
}
.place-preview__foot {
  margin-top: var(--pa-space-1);
  padding-top: var(--pa-space-2);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.place-preview__cta {
  align-self: flex-start;
}
.place-preview__hint {
  margin: 0;
  padding: var(--pa-space-6) var(--pa-space-4);
  text-align: center;
  color: var(--pa-color-text-muted);
}
</style>
