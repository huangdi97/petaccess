<script setup lang="ts">
/**
 * PlacePreview — first-round place summary pane (M3 D1, V020 goal §33).
 * Data flows IN as props (SearchView fetches CoexistenceSnapshot via the generated
 * model itself, it presents values through the shared vocabularies.
 */
import { computed } from "vue";
import {
  placeTypeLabel,
  ruleSummaryLabel,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import StatusBadge from "../StatusBadge.vue";
import PaDivider from "../ui/PaDivider.vue";
import {
  divergenceLabel,
  realityStateLabel,
  staffResponseLines,
  facilityLines,
} from "../../reality";

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

const evidenceLine = computed(() => {
  const s = props.snapshot?.evidence_summary;
  if (!s) return "";
  return `规则依据 ${s.rule_evidence.length} 条 · 现场依据 ${s.reality_evidence_count} 条（${s.reality_distinct_source_count} 个来源）`;
});
const staffLines = computed(() => staffResponseLines(props.snapshot?.staff_response_summary ?? []));
const facilityLinesOut = computed(() => facilityLines(props.snapshot?.facility_summary ?? []));
</script>

<template>
  <section class="place-preview" data-testid="place-preview" :aria-busy="loading">
    <template v-if="place">
      <header class="place-preview__head">
        <div class="place-preview__title-row">
          <h2 class="place-preview__name">{{ place.canonical_name }}</h2>
          <StatusBadge :status="status ?? 'UNKNOWN'" />
        </div>
        <p v-if="place.parent_place_name" class="place-preview__muted">
          所属 {{ place.parent_place_name }}
        </p>
        <p class="place-preview__muted">
          {{ placeTypeLabel(place.place_type) }} · {{ place.canonical_address ?? "地址待补充" }}
        </p>
      </header>

      <PaDivider />

      <div class="place-preview__row">
        <span class="place-preview__label">规则</span>
        <span class="place-preview__value">{{ ruleSummaryLabel(place) }}</span>
      </div>

      <div class="place-preview__row">
        <span class="place-preview__label">近期现场</span>
        <div class="place-preview__value" data-testid="preview-reality">
          <p v-if="loading" class="place-preview__muted">正在加载现场摘要…</p>
          <p v-else-if="error" class="place-preview__error">{{ error }}</p>
          <template v-else-if="snapshot">
            <p>{{ realityStateLabel(snapshot.reality_answer) }}</p>
            <p
              v-if="snapshot.reality_answer.days_since_last_seen != null"
              class="place-preview__muted"
            >
              {{ snapshot.reality_answer.days_since_last_seen }} 天前最近一次记录
            </p>
            <p v-if="snapshot.reality_answer.note" class="place-preview__muted">
              {{ snapshot.reality_answer.note }}
            </p>
          </template>
          <p v-else class="place-preview__muted">
            {{ EMPTY_STATE_COPY.REALITY.title }} — 暂无记录不代表现实中没有动物。
          </p>
        </div>
      </div>

      <div v-if="snapshot" class="place-preview__row">
        <span class="place-preview__label">差异</span>
        <div class="place-preview__value">
          <p>{{ divergenceLabel(snapshot.divergence) }}</p>
          <p v-if="snapshot.divergence.note" class="place-preview__muted">
            {{ snapshot.divergence.note }}
          </p>
        </div>
      </div>

      <div v-if="snapshot" class="place-preview__row">
        <span class="place-preview__label">依据</span>
        <div class="place-preview__value">
          <p>{{ evidenceLine }}</p>
          <ul v-if="staffLines.length" class="place-preview__facts">
            <li v-for="(l, i) in staffLines" :key="`s-${i}`">{{ l }}</li>
          </ul>
          <ul v-if="facilityLinesOut.length" class="place-preview__facts">
            <li v-for="(l, i) in facilityLinesOut" :key="`f-${i}`">{{ l }}</li>
          </ul>
        </div>
      </div>

      <footer class="place-preview__foot">
        <RouterLink class="btn primary" :to="`/place/${place.id}`" data-testid="preview-open">
          查看完整场所
        </RouterLink>
      </footer>
    </template>

    <p v-else class="place-preview__hint" data-testid="preview-empty">
      从左侧选择一条结果，查看规则与现场摘要。
    </p>
  </section>
</template>

<style scoped>
.place-preview {
  border: 1px solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
  padding: var(--pa-space-4);
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
.place-preview__title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
}
.place-preview__name {
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-semibold);
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
.place-preview__error {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
  line-height: var(--pa-line-height-base);
}
.place-preview__row {
  display: grid;
  grid-template-columns: 5rem 1fr;
  gap: var(--pa-space-3);
  align-items: start;
}
.place-preview__label {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}
.place-preview__value {
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-primary);
  line-height: var(--pa-line-height-base);
}
.place-preview__value p {
  margin: 0 0 var(--pa-space-1);
}
.place-preview__facts {
  margin: var(--pa-space-1) 0 0;
  padding-left: var(--pa-space-4);
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
}
.place-preview__foot {
  margin-top: var(--pa-space-1);
}
.place-preview__hint {
  margin: 0;
  padding: var(--pa-space-6) var(--pa-space-4);
  text-align: center;
  color: var(--pa-color-text-muted);
}
</style>
