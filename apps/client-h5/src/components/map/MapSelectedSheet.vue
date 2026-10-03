<script setup lang="ts">
/**
 * MapSelectedSheet — mobile selected-place bottom sheet（v0.2.5 §22–24/§49）。
 *
 * 真实 overlay bottom sheet：
 * - `position: fixed`，bottom = tabbar + safe area（不与 tabbar 重叠）；
 * - 白色 surface、top radius 16、small drag handle、elevation、touch scroll；
 * - 三态：closed（56–64px peek）/ half（~280–340px）/ expanded（max 70–78vh）；
 * - 内容 = drag handle + Place name + Status（紧凑，非全宽 outline 条）+
 *   Type·distance + Key condition + 最近现场 + 查看场所 →；close 右上 icon。
 * - `role="dialog"` + Escape 关闭（键盘可达）；reduced-motion 降级。
 */
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import {
  placeTypeLabel,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../../answer";
import { realityStateLabel } from "../../reality";
import { sourceLabel } from "../../consumer/labels";
import StatusBadge from "../StatusBadge.vue";
import PaIcon from "../ui/PaIcon.vue";

const props = withDefaults(
  defineProps<{
    open: boolean;
    place: PlaceSummary | null;
    status?: string | null;
    snapshot?: CoexistenceSnapshot | null;
    loading?: boolean;
    error?: string;
  }>(),
  { status: null, snapshot: null, loading: false, error: "" },
);

const emit = defineEmits<{ close: [] }>();

/** sheet 展示状态：half（默认选中态）/ expanded（可手动展开）/ closed（peek）。 */
type SheetPhase = "closed" | "half" | "expanded";
const phase = ref<SheetPhase>("half");

const TABBAR = "var(--pa-safe-total-bottom)";
const HALF_H = "min(288px, 32vh)";
const EXPANDED_MAX_H = "min(78vh, 680px)";
const EXPANDED_MIN_H = "min(420px, 55vh)";
const CLOSED_H = "60px";

/** §23 geometry：phase → 高度；bottom 固定在 tabbar 上方。 */
const sheetStyle = computed(() => {
  if (phase.value === "expanded") {
    return {
      height: "auto",
      minHeight: EXPANDED_MIN_H,
      maxHeight: EXPANDED_MAX_H,
      bottom: TABBAR,
    };
  }
  return {
    height: phase.value === "closed" ? CLOSED_H : HALF_H,
    bottom: TABBAR,
  };
});

const answer = computed(() => props.snapshot?.rule_answer ?? null);
const statusKey = computed<import("@petaccess/design-tokens").StatusKey>(() =>
  answer.value
    ? answerStatusKey(answer.value)
    : ((props.status ?? "UNKNOWN") as import("@petaccess/design-tokens").StatusKey),
);
const keyCondition = computed(() => answerConditions(answer.value)[0] ?? "");
const realityLine = computed(() =>
  props.snapshot?.reality_answer
    ? realityStateLabel(props.snapshot.reality_answer)
    : "暂无足够记录",
);
/** §13 expanded：Current Decision —— 真实 verdict（不伪造）。 */
const verdictText = computed(() => (props.loading ? "加载中…" : answerVerdictLabel(answer.value)));
/** §13 expanded：Evidence/Freshness —— 真实来源 issuer + snapshot 生成时间。 */
const evidenceLine = computed(() => {
  const ev = answer.value?.evidence_state.rules[0] ?? null;
  const issuer = sourceLabel(ev?.issuer ?? null, Boolean(ev));
  const gen = props.snapshot?.generated_at?.slice(0, 10);
  return gen ? `${issuer} · 更新于 ${gen}` : issuer;
});

function onKey(e: KeyboardEvent) {
  if (props.open && e.key === "Escape") emit("close");
}

function cyclePhase() {
  phase.value = phase.value === "expanded" ? "half" : "expanded";
}

onMounted(() => window.addEventListener("keydown", onKey));
onBeforeUnmount(() => window.removeEventListener("keydown", onKey));
</script>

<template>
  <div
    v-if="open && place"
    class="sheet-overlay"
    data-testid="map-sheet-overlay"
    data-ui="map-sheet"
  >
    <section
      class="sheet"
      role="dialog"
      aria-modal="false"
      :aria-label="`${place.canonical_name} 场所信息`"
      :style="sheetStyle"
      :data-phase="phase"
      data-testid="map-mobile-sheet"
      data-ui="map-mobile-sheet"
    >
      <button
        class="sheet__handle"
        data-testid="sheet-handle"
        aria-label="调整面板"
        @click="cyclePhase"
      >
        <span class="sheet__handle-bar" aria-hidden="true" />
      </button>

      <div class="sheet__body">
        <div class="sheet__head">
          <div class="sheet__title-row">
            <h2 class="sheet__name">{{ place.canonical_name }}</h2>
            <StatusBadge :semantic="statusKey" />
            <button
              class="sheet__close"
              data-testid="sheet-close"
              aria-label="关闭"
              @click="emit('close')"
            >
              <PaIcon name="close" size="sm" label="关闭" />
            </button>
          </div>
          <p class="muted sheet__meta">
            {{ placeTypeLabel(place.place_type) }}
            <template v-if="place.distance_m"> · {{ Math.round(place.distance_m) }}m</template>
          </p>
        </div>

        <!-- §13 expanded：Current Decision（真实 verdict，无数据则保持留白不伪造）。 -->
        <div
          v-if="phase === 'expanded'"
          class="sheet__block"
          data-testid="sheet-verdict"
          data-ui="sheet-verdict"
        >
          <span class="sheet__block-label">结论</span>
          <p class="sheet__verdict" data-testid="sheet-verdict-text">{{ verdictText }}</p>
        </div>

        <p v-if="keyCondition" class="sheet__condition" data-testid="sheet-condition">
          {{ keyCondition }}
        </p>

        <div class="sheet__reality">
          <span class="muted sheet__reality-label">最近现场</span>
          <span class="sheet__reality-line">
            {{ loading ? "加载中…" : error ? "暂时无法取得" : realityLine }}
          </span>
        </div>

        <!-- §13 expanded：Evidence/Freshness（真实来源 + 快照更新时间，不伪造）。 -->
        <div
          v-if="phase === 'expanded'"
          class="sheet__block"
          data-testid="sheet-evidence"
          data-ui="sheet-evidence"
        >
          <span class="sheet__block-label">证据与来源</span>
          <p class="sheet__evidence-line">{{ evidenceLine }}</p>
        </div>

        <div class="sheet__actions">
          <RouterLink
            class="btn-inline sheet__cta"
            :to="`/place/${place.id}`"
            data-testid="sheet-open-detail"
          >
            查看场所 →
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.sheet-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--pa-z-sheet);
  pointer-events: none; /* 透传给 map；sheet 本身可交互。 */
}
.sheet {
  position: absolute;
  left: 0;
  right: 0;
  margin: 0 auto;
  max-width: 480px;
  background: var(--pa-color-surface);
  border-radius: var(--pa-radius-sheet) var(--pa-radius-sheet) 0 0;
  box-shadow: var(--pa-elevation-3);
  display: flex;
  flex-direction: column;
  pointer-events: auto;
  transition: height 200ms ease;
  overflow: hidden;
  will-change: height;
}
.sheet__handle {
  flex: 0 0 auto;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 20px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
}
.sheet__handle-bar {
  width: 36px;
  height: 4px;
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-border-strong);
}
.sheet__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 0 var(--pa-space-5) var(--pa-space-4);
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
}
.sheet__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.sheet__title-row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  min-height: 36px;
}
.sheet__name {
  flex: 1 1 auto;
  min-width: 0;
  margin: 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.sheet__meta {
  margin: 0;
  font-size: var(--pa-font-size-md);
}
.sheet__condition {
  margin: 0;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
/* §13 expanded blocks：真实信息块，label 弱化、value 为主内容。 */
.sheet__block {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.sheet__block-label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}
.sheet__verdict {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.sheet__evidence-line {
  margin: 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-primary);
  overflow-wrap: anywhere;
}
.sheet__reality {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.sheet__reality-label {
  font-size: var(--pa-font-size-sm);
}
.sheet__reality-line {
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-primary);
}
.sheet__actions {
  margin-top: auto;
  padding-top: var(--pa-space-2);
}
.sheet__close {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-size-control-md);
  height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-text-secondary);
  border-radius: var(--pa-radius-control);
  cursor: pointer;
}
.sheet__close:hover,
.sheet__close:focus-visible {
  background: var(--pa-color-surface-muted);
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -1px;
}

/* reduced motion：无高度动画。 */
@media (prefers-reduced-motion: reduce) {
  .sheet {
    transition: none;
  }
}
</style>
