<script setup lang="ts">
/**
 * MapSelectedSheet — mobile selected-place bottom sheet（v0.2.5 §22–24/§49）。
 *
 * 真实 overlay bottom sheet：
 * - `position: fixed`，bottom = tabbar + safe area（不与 tabbar 重叠）；
 * - 白色 surface、top radius 16、small drag handle、elevation、touch scroll；
 * - 三态：closed（56–64px peek）/ half（~328–352px）/ expanded（max 70–78vh）；
 * - 内容 = drag handle + Place name + Type·distance + active lens +
 *   separately-labelled Rule + cross-dimension recent Reality + 查看地点 →；close 右上 icon。
 * - `role="dialog"` + Escape 关闭（键盘可达）；reduced-motion 降级。
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  placeTypeLabel,
  type CoexistenceSnapshot,
  type PlaceSummary,
} from "@petaccess/client-core";
import { answerConditions, answerVerdictLabel } from "../../answer";
import { coexistenceRealityLine } from "../../consumer/rowView";
import { publicSourceIssuer } from "../../consumer/sourcePrivacy";
import PaIcon from "../ui/PaIcon.vue";
import PlaceTypeGlyph from "../domain/PlaceTypeGlyph.vue";

const props = withDefaults(
  defineProps<{
    open: boolean;
    place: PlaceSummary | null;
    status?: string | null;
    snapshot?: CoexistenceSnapshot | null;
    loading?: boolean;
    error?: string;
    mapLensName?: string;
    mapLensLabel?: string;
    sceneMediaUrl?: string | null;
  }>(),
  {
    status: null,
    snapshot: null,
    loading: false,
    error: "",
    mapLensName: "",
    mapLensLabel: "",
    sceneMediaUrl: null,
  },
);

const emit = defineEmits<{ close: [] }>();

/** sheet 展示状态：half（默认选中态）/ expanded（可手动展开）/ closed（peek）。 */
type SheetPhase = "closed" | "half" | "expanded";
const phase = ref<SheetPhase>("half");

const TABBAR = "var(--pa-safe-total-bottom)";
const HALF_H = "clamp(252px, 29vh, 276px)";
const EXPANDED_MAX_H = "min(72vh, 640px)";
const EXPANDED_MIN_H = "min(348px, 44vh)";
const CLOSED_H = "104px";

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
const keyCondition = computed(() => answerConditions(answer.value)[0] ?? "");
const realityLine = computed(() =>
  coexistenceRealityLine(props.snapshot, props.snapshot?.reality_answer),
);
/** §13 expanded：Current Decision —— 真实 verdict（不伪造）。 */
const verdictText = computed(() =>
  props.loading
    ? "正在加载规则结论…"
    : props.error
      ? "规则结论暂时无法取得"
      : answerVerdictLabel(answer.value),
);

const primaryLabel = computed(() =>
  props.mapLensLabel ? props.mapLensName || "当前地图" : "规则",
);
const primaryText = computed(() => props.mapLensLabel || verdictText.value);
/** When Reality is already the active lens, repeating the same Reality summary
 * below it turns the bridge into a card stack. Other lenses keep Reality as a
 * genuinely different secondary fact. */
const showRealitySupplement = computed(() => props.mapLensName !== "现场");
const secondaryRuleLine = computed(() => {
  if (!props.mapLensLabel) return "";
  if (props.loading || props.error) return verdictText.value;
  return keyCondition.value
    ? `${verdictText.value} · 需满足：${keyCondition.value}`
    : verdictText.value;
});
/** Evidence/Freshness must describe evidence, not the time this snapshot was assembled. */
const evidenceLine = computed(() => {
  if (props.loading) return "正在加载证据与来源…";
  if (props.error) return "证据与来源暂时无法取得";
  const ev = answer.value?.evidence_state.rules[0] ?? null;
  const parts: string[] = [];
  if (ev) {
    parts.push(publicSourceIssuer(ev.source_type, ev.issuer));
    parts.push(
      props.place?.last_verified_at
        ? `规则核验 ${props.place.last_verified_at.slice(0, 10)}`
        : "规则核验时间待补充",
    );
  } else {
    parts.push("规则依据待补充");
  }

  const evidence = props.snapshot?.evidence_summary;
  if ((evidence?.reality_evidence_count ?? 0) > 0) {
    parts.push(
      `现场 ${evidence?.reality_evidence_count ?? 0} 条证据 · ${evidence?.reality_distinct_source_count ?? 0} 个来源`,
    );
  }
  return parts.join(" · ");
});

function onKey(e: KeyboardEvent) {
  if (props.open && e.key === "Escape") emit("close");
}

function cyclePhase() {
  phase.value =
    phase.value === "half" ? "expanded" : phase.value === "expanded" ? "closed" : "half";
}

let dragStartY: number | null = null;
let suppressNextHandleClick = false;

function onHandlePointerDown(event: PointerEvent) {
  dragStartY = event.clientY;
  suppressNextHandleClick = false;

  // Pointer capture is valuable for a real finger/mouse drag that leaves the
  // 28px handle, but synthetic PointerEvents (including Playwright
  // dispatchEvent) are not active browser pointers and can throw here. Keep
  // real interaction robust without letting an unsupported capture abort the
  // sheet gesture lifecycle.
  if (event.isPrimary) {
    try {
      (event.currentTarget as HTMLElement | null)?.setPointerCapture?.(event.pointerId);
    } catch {
      // The drag still works when pointerup lands on the handle.
    }
  }
}

function onHandlePointerUp(event: PointerEvent) {
  if (dragStartY == null) return;
  const delta = event.clientY - dragStartY;
  dragStartY = null;

  try {
    const target = event.currentTarget as HTMLElement | null;
    if (target?.hasPointerCapture?.(event.pointerId)) target.releasePointerCapture(event.pointerId);
  } catch {
    // Capture may already have been released by the browser.
  }

  if (Math.abs(delta) < 36) return;

  suppressNextHandleClick = true;
  if (delta < 0) {
    phase.value = "expanded";
  } else {
    phase.value = phase.value === "expanded" ? "half" : "closed";
  }
}

function onHandlePointerCancel() {
  dragStartY = null;
}

function onHandleClick() {
  if (suppressNextHandleClick) {
    suppressNextHandleClick = false;
    return;
  }
  cyclePhase();
}

// A new selection is a new decision task. Reopen it at the designed half
// height instead of carrying an expanded/closed phase from the previous place.
watch(
  () => [props.open, props.place?.id] as const,
  ([open, placeId], previous) => {
    const [wasOpen, previousPlaceId] = previous ?? [false, undefined];
    if (open && (!wasOpen || placeId !== previousPlaceId)) phase.value = "half";
  },
);

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
        :aria-label="
          phase === 'half' ? '展开场所面板' : phase === 'expanded' ? '收起场所面板' : '恢复场所面板'
        "
        :aria-expanded="phase === 'expanded'"
        @pointerdown.stop="onHandlePointerDown"
        @pointerup.stop="onHandlePointerUp"
        @pointercancel.stop="onHandlePointerCancel"
        @click.stop="onHandleClick"
      >
        <span class="sheet__handle-bar" aria-hidden="true" />
      </button>

      <div class="sheet__body">
        <div class="sheet__head">
          <div class="sheet__title-row">
            <PlaceTypeGlyph :place-type="place.place_type" size="sm" />
            <h2 class="sheet__name">{{ place.canonical_name }}</h2>
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
            <template v-if="place.distance_m != null">
              · {{ Math.round(place.distance_m) }}m
            </template>
          </p>
        </div>

        <!-- Full media belongs to expanded detail and is never fabricated for
             missing records. The half sheet stays decision-first. -->
        <img
          v-if="sceneMediaUrl && phase === 'expanded'"
          class="sheet__scene"
          :src="sceneMediaUrl"
          :alt="`场所场景：${place.canonical_name}`"
          loading="lazy"
          decoding="async"
          referrerpolicy="no-referrer"
        />

        <div class="sheet__primary" data-testid="sheet-map-lens">
          <span class="sheet__primary-label">{{ primaryLabel }}</span>
          <strong>{{ primaryText }}</strong>
          <p
            v-if="!mapLensLabel && keyCondition && !loading && !error"
            class="sheet__condition"
            data-testid="sheet-condition"
          >
            需满足：{{ keyCondition }}
          </p>
        </div>

        <p v-if="mapLensLabel" class="sheet__secondary-fact" data-testid="sheet-verdict">
          <span>规则</span>
          <strong data-testid="sheet-verdict-text">{{ secondaryRuleLine }}</strong>
        </p>

        <div v-if="showRealitySupplement" class="sheet__reality" data-testid="sheet-reality">
          <span class="muted sheet__reality-label">最近现场</span>
          <span class="sheet__reality-line">
            {{ loading ? "加载中…" : error ? "暂时无法取得" : realityLine }}
          </span>
        </div>

        <!-- Evidence/Freshness：真实来源 + 规则核验时间 + Reality 证据计数。 -->
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
            class="btn primary sheet__cta"
            :to="`/place/${place.id}`"
            data-testid="sheet-open-detail"
          >
            查看地点 →
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
  height: 28px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: ns-resize;
  touch-action: none;
  user-select: none;
}

.sheet__handle:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
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
  padding: 0 var(--pa-space-4) var(--pa-space-4);
  display: flex;
  flex-direction: column;
  gap: 0;
}
.sheet__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.sheet[data-phase="closed"] .sheet__body {
  overflow: hidden;
  padding-bottom: 8px;
}

.sheet[data-phase="closed"] .sheet__head {
  min-height: 68px;
  justify-content: center;
}

.sheet[data-phase="closed"]
  :is(
    .sheet__primary,
    .sheet__secondary-fact,
    .sheet__reality,
    .sheet__block,
    .sheet__actions,
    .sheet__scene
  ) {
  display: none;
}

.sheet[data-phase="closed"] .sheet__meta {
  display: block;
}

.sheet__title-row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  min-height: 32px;
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
.sheet__primary {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin-top: var(--pa-space-2);
  padding: var(--pa-space-2) 0 var(--pa-space-2) var(--pa-space-3);
  border-left: 3px solid var(--pa-color-border-strong);
}
.sheet__primary-label {
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
}
.sheet__primary strong {
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-26);
}
.sheet__secondary-fact {
  display: flex;
  gap: var(--pa-space-2);
  align-items: baseline;
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
}
.sheet__secondary-fact span {
  flex: 0 0 auto;
  color: var(--pa-color-text-muted);
}
.sheet__secondary-fact strong {
  font-weight: var(--pa-font-weight-600);
}
.sheet__scene {
  display: block;
  width: 100%;
  max-height: 148px;
  aspect-ratio: 16 / 7;
  object-fit: cover;
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface-muted);
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
.sheet__verdict--secondary {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-23);
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
  margin-top: var(--pa-space-2);
  padding-top: var(--pa-space-2);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.sheet__reality-label {
  font-size: var(--pa-font-size-sm);
}
.sheet__reality-line {
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-primary);
}
.sheet__actions {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--pa-space-2);
  padding-top: var(--pa-space-2);
}

.sheet__cta {
  width: auto;
  min-width: 136px;
  min-height: var(--pa-size-control-lg);
  justify-content: center;
}

/* Half is a glanceable decision surface. Keep the primary navigation action
 * completely visible without making the sheet taller: it becomes a compact
 * inline destination link pinned inside the sheet's lower reading edge. */
.sheet[data-phase="half"] .sheet__body {
  padding-bottom: 52px;
}

.sheet[data-phase="half"] .sheet__actions {
  position: absolute;
  right: var(--pa-space-4);
  bottom: var(--pa-space-3);
  margin: 0;
  padding: 0;
}

.sheet[data-phase="half"] .sheet__cta {
  min-width: 0;
  min-height: 32px;
  padding: 0 4px;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--pa-color-accent);
  box-shadow: none;
}

.sheet__close {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-layout-touch-target);
  height: var(--pa-layout-touch-target);
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
