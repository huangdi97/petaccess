<script setup lang="ts">
/**
 * ContributeView — M7 contribution wizard orchestrator (A1/A4).
 * Keeps the gating (place / signed-in), the step machine and the shared form
 * props; every screen is a step component. The only active lanes are:
 * Rule lead/confirmation, RealityReport facts, and Place correction.
 * Legacy signage/Observation screens are intentionally not wired as parallel
 * truth paths. No free-text comment box.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, session } from "@petaccess/client-core";
import StateMessage from "../components/StateMessage.vue";
import SkeletonList from "../components/SkeletonList.vue";
import ContributeEntry from "../components/contribute/ContributeEntry.vue";
import ContributeQuickForm from "../components/contribute/ContributeQuickForm.vue";
import ContributeRuleForm from "../components/contribute/ContributeRuleForm.vue";
import ContributeRealityForm from "../components/contribute/ContributeRealityForm.vue";
import ContributeEffortForm from "../components/contribute/ContributeEffortForm.vue";
import ContributeDone from "../components/contribute/ContributeDone.vue";
import { useBreakpoint } from "../composables/useBreakpoint";
import { useOnline } from "../composables/useOnline";

defineOptions({ name: "ContributeView" });

type Step = "entry" | "quick" | "rule" | "reality" | "effort" | "done";
type RealityKind = "observed_presence" | "staff_response" | "animal_facility";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));
const effortTargetClaimId = computed(() =>
  typeof route.query.target === "string" ? route.query.target : null,
);
const effortInitialZoneId = computed(() =>
  typeof route.query.zone === "string" ? route.query.zone : null,
);
const { online } = useOnline();

const step = ref<Step>("entry");
const realityKind = ref<RealityKind>("observed_presence");
const msg = ref("");
const formReviewing = ref(false);
const signedIn = ref(false);
const contextLoading = ref(true);
const contextError = ref("");
const zones = ref<{ id: string; name: string }[]>([]);
/** §29：step shell 顶部显示「我给哪个场所提交」。 */
const placeName = ref("");
const parentPlaceId = ref<string | null>(null);

// The router reuses this component between /contribute/:id routes. Read
// the target ID once per generation: a late A response must not insert A's
// zones/name into B's form, where the subsequent submit would target B.
let placeContextGeneration = 0;
async function loadContext() {
  const generation = ++placeContextGeneration;
  const targetPlaceId = placeId.value;
  reset();
  contextLoading.value = true;
  contextError.value = "";
  signedIn.value = false;
  zones.value = [];
  placeName.value = "";
  parentPlaceId.value = null;
  if (route.query.mode === "effort") step.value = "effort";
  try {
    await session.restore();
    if (generation !== placeContextGeneration) return;
    signedIn.value = session.signedIn;
    if (!signedIn.value || !targetPlaceId) return;
    // Both identity and zone scope must be retrieved before a fact is
    // submitted. A missing place is never a valid fallback form target.
    const [place, nextZones] = await Promise.all([
      client.place(targetPlaceId),
      client.zones(targetPlaceId),
    ]);
    if (generation !== placeContextGeneration || placeId.value !== targetPlaceId) return;
    placeName.value = place.canonical_name;
    zones.value = nextZones;
    parentPlaceId.value = place.parent_place_id ?? null;
  } catch {
    if (generation === placeContextGeneration) {
      contextError.value = "无法确认当前场所及区域，请重试或重新选择场所。没有提交任何信息。";
    }
  } finally {
    if (generation === placeContextGeneration) contextLoading.value = false;
  }
}

watch(
  [placeId, () => route.query.mode, () => route.query.target, () => route.query.zone],
  loadContext,
  { immediate: true },
);

function reset() {
  step.value = "entry";
  msg.value = "";
  formReviewing.value = false;
}

function startReality(kind: RealityKind) {
  formReviewing.value = false;
  realityKind.value = kind;
  step.value = "reality";
}

function done(m: string) {
  formReviewing.value = false;
  msg.value = m;
  step.value = "done";
}

/** O6 capture-state integrity: every exposed state maps to the real screen.
 * choose-type → structured form → read-only review → done. */
const uiState = computed<string>(() => {
  if (!placeId.value) return "needs-place";
  if (contextLoading.value) return "loading-place";
  if (contextError.value) return "place-error";
  if (!signedIn.value) return "sign-in-required";
  if (formReviewing.value) return "review";
  switch (step.value) {
    case "entry":
      return "choose-type";
    case "done":
      return "done";
    case "reality":
    case "effort":
      return "step-2";
    default:
      return "step-1";
  }
});
/** §41: choice-count must reflect the real number of options on the entry. */
const choiceCount = computed<number>(() => (uiState.value === "choose-type" ? 5 : 0));

/** §15 context rail：本次贡献类型 —— 从真实 step 状态推导，不伪造。 */
const REALITY_KIND_LABELS: Record<RealityKind, string> = {
  observed_presence: "动物出现记录",
  staff_response: "工作人员处理记录",
  animal_facility: "动物相关设施记录",
};
const contributionKindLabel = computed(() => {
  if (step.value === "entry") return "选择贡献类型";
  if (step.value === "quick") return "场所信息纠错";
  if (step.value === "rule") return "规则线索 / 核验";
  if (step.value === "reality") return REALITY_KIND_LABELS[realityKind.value];
  if (step.value === "effort") return "本次未观察到动物";
  if (step.value === "done") return "提交完成";
  return "现场贡献";
});
/** §15 context rail：适用区域 —— 真实 zones 数据（无则保持 shell 默认）。 */
const contextZoneLabel = computed(() => {
  const scoped = zones.value.find((item) => item.id === effortInitialZoneId.value);
  if (scoped) return `本次所选区域：${scoped.name}`;
  const first = zones.value[0];
  if (!first) return "暂未收录具体区域";
  if (zones.value.length === 1) return `已收录区域：${first.name}`;
  return `${first.name} 等 ${zones.value.length} 个区域`;
});
const uiFixture = computed<string>(() => `contribution-${uiState.value}-v1`);

const { desktop: isDesktop } = useBreakpoint();
</script>

<template>
  <div
    class="contribute-workspace"
    data-testid="contribute-workspace"
    data-ui-page="contribution"
    :data-ui-state="uiState"
    :data-ui-fixture="uiFixture"
  >
    <div class="contribute-workspace__body" data-ui="contribution-workspace">
      <div class="contribute-workspace__layout">
        <main class="contribute-workspace__main" data-ui="contribution-main">
          <h1 class="visually-hidden">
            {{ uiState === "choose-type" ? "你刚刚知道了什么？" : "现场贡献" }}
          </h1>
          <span
            v-if="uiState === 'choose-type'"
            class="visually-hidden"
            data-ui-count="choice-count"
            >{{ choiceCount }}</span
          >

          <section
            v-if="!placeId"
            class="contribute-start"
            data-testid="contribute-needs-place"
            aria-labelledby="contribute-start-title"
          >
            <div class="contribute-start__hero">
              <p class="contribute-start__kicker">现场贡献</p>
              <h2 id="contribute-start-title">先选一个场所，再补充你刚刚知道的事实。</h2>
              <p class="muted contribute-start__intro">
                规则线索、现场动物、工作人员处理、相关设施和场所纠错都从具体地点开始；提交内容会先进入人工核验。
              </p>
              <div class="contribute-needs-place-actions">
                <RouterLink class="btn primary" to="/search" data-testid="contribute-go-search">
                  搜索场所
                </RouterLink>
                <RouterLink class="btn" to="/map" data-testid="contribute-go-map">
                  从地图选择
                </RouterLink>
              </div>
            </div>

            <div class="contribute-start__facts" aria-label="可以补充的事实">
              <div class="contribute-start__section-head">
                <h3>你可以补充什么</h3>
                <span class="muted">一次只提交一类事实，更容易核验。</span>
              </div>
              <ul class="contribute-start__fact-list">
                <li>
                  <strong>规则线索</strong>
                  <span>规则牌、公告或工作人员说明</span>
                </li>
                <li>
                  <strong>现场动物</strong>
                  <span>看到什么动物、在哪里、什么时间</span>
                </li>
                <li>
                  <strong>工作人员处理</strong>
                  <span>现场如何提示、引导或要求</span>
                </li>
                <li>
                  <strong>动物相关设施</strong>
                  <span>宠物区、饮水点、临时安置等</span>
                </li>
                <li>
                  <strong>场所纠错</strong>
                  <span>名称、地址或场所状态有误</span>
                </li>
              </ul>
            </div>

            <p class="contribute-start__boundary">
              一次现场观察不会自动变成正式准入规则；工作人员处理也不等于运营方政策。
            </p>
          </section>

          <SkeletonList v-else-if="contextLoading" :rows="4" />
          <StateMessage
            v-else-if="contextError"
            kind="ERROR"
            :description="contextError"
            data-testid="contribution-context-error"
          >
            <template #action>
              <button class="primary" type="button" @click="loadContext">重试</button>
              <RouterLink class="btn" to="/search">重新选择场所</RouterLink>
            </template>
          </StateMessage>

          <StateMessage
            v-else-if="!signedIn"
            kind="PERMISSION_DENIED"
            description="贡献需要登录后进行，以便记录来源与核验历史。未登录不会提交任何数据。"
          >
            <template #action>
              <RouterLink
                class="btn primary"
                :to="{ name: 'onboarding', query: { next: route.fullPath } }"
                >登录 / 注册</RouterLink
              >
            </template>
          </StateMessage>

          <template v-else>
            <div
              v-if="!isDesktop && step === 'entry'"
              class="contribute-mobile-context"
              data-testid="contribution-mobile-place-context"
              data-ui="contribution-mobile-place-context"
              aria-label="当前贡献场所"
            >
              <span class="contribute-mobile-context__label">当前场所</span>
              <strong class="contribute-mobile-context__value">
                {{ placeName || "场所名称待补充" }}
              </strong>
              <span class="contribute-mobile-context__sub">{{ contextZoneLabel }}</span>
            </div>

            <ContributeEntry
              v-if="step === 'entry'"
              @select="step = $event"
              @reality="startReality"
              @effort="step = 'effort'"
            />
            <ContributeQuickForm
              v-else-if="step === 'quick'"
              :place-id="placeId"
              :place-name="placeName"
              :online="online"
              :signed-in="signedIn"
              @done="done"
              @back="reset"
              @reviewing="formReviewing = $event"
            />
            <ContributeRuleForm
              v-else-if="step === 'rule'"
              :place-id="placeId"
              :place-name="placeName"
              :zones="zones"
              :online="online"
              :signed-in="signedIn"
              @done="done"
              @back="reset"
              @reviewing="formReviewing = $event"
            />
            <ContributeRealityForm
              v-else-if="step === 'reality'"
              :place-id="placeId"
              :place-name="placeName"
              :parent-place-id="parentPlaceId"
              :zones="zones"
              :initial-zone-id="effortInitialZoneId"
              :online="online"
              :signed-in="signedIn"
              :kind="realityKind"
              @done="done"
              @back="reset"
              @reviewing="formReviewing = $event"
            />
            <ContributeEffortForm
              v-else-if="step === 'effort'"
              :place-id="placeId"
              :place-name="placeName"
              :zones="zones"
              :online="online"
              :signed-in="signedIn"
              :target-claim-id="effortTargetClaimId"
              :initial-zone-id="effortInitialZoneId"
              @done="done"
              @back="reset"
              @reviewing="formReviewing = $event"
            />
            <ContributeDone
              v-else-if="step === 'done'"
              :msg="msg"
              :place-id="placeId"
              @continue="reset"
            />
          </template>
        </main>

        <!-- §15/§16 secondary context rail（desktop only）：只放真实上下文，
             不新增营销文案 / 统计 / badge wall。 -->
        <aside
          v-if="
            isDesktop &&
            placeId &&
            signedIn &&
            !contextLoading &&
            !contextError &&
            uiState !== 'done'
          "
          class="contribute-workspace__context"
          data-ui="contribution-context"
          aria-label="本次贡献说明"
        >
          <div class="contribute-context__block" data-ui="contribution-context-place">
            <span class="contribute-context__label">当前场所</span>
            <span class="contribute-context__value">{{ placeName || "场所名称待补充" }}</span>
            <span class="contribute-context__sub">{{ contextZoneLabel }}</span>
          </div>
          <div class="contribute-context__block" data-ui="contribution-context-kind">
            <span class="contribute-context__label">本次贡献</span>
            <span class="contribute-context__value">{{ contributionKindLabel }}</span>
          </div>
          <div class="contribute-context__block" data-ui="contribution-context-why">
            <span class="contribute-context__label">为什么需要这些信息</span>
            <p class="contribute-context__body">
              每条现场信息都会记录来源与时间，用于之后的人工核验。
            </p>
          </div>
          <div class="contribute-context__block" data-ui="contribution-context-after">
            <span class="contribute-context__label">提交之后</span>
            <p class="contribute-context__body">
              提交内容进入人工核验队列，AI 不会自动裁定；审核通过后才作为记录展示。
            </p>
          </div>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.contribute-workspace {
  min-height: 100%;
  background: var(--pa-color-surface-muted);
}
.contribute-workspace__body {
  /* v0.2.7 §16：TASK workspace 总宽 900–1040 —— main 680 + gap 48 + context 280。
     Mobile 保持单列（context rail 在桌面才渲染）。 */
  padding: var(--pa-space-4) var(--pa-space-5) var(--pa-space-7);
  max-width: 1080px;
  margin: 0 auto;
}
.contribute-workspace__layout {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-6);
}
.contribute-workspace__main {
  flex: 1 1 auto;
  width: 100%;
  min-width: 0;
  max-width: 700px;
  padding: var(--pa-space-5);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background: var(--pa-color-surface-raised);
  box-shadow: var(--pa-elevation-1);
  box-sizing: border-box;
}
/* §15/§16 secondary context rail：240–300px，只放真实上下文。 */
.contribute-workspace__context {
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.contribute-context__block {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.contribute-context__label {
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-medium);
  letter-spacing: var(--pa-letter-spacing-wide);
  color: var(--pa-color-text-muted);
}
.contribute-context__value {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-primary);
}
.contribute-context__sub {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
}
.contribute-context__body {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-secondary);
}

/* On phone/tablet the desktop context rail is absent. Keep one lightweight
 * place anchor above the first question so a fast field contribution cannot be
 * accidentally attached to the wrong venue. This is context, not another card. */
.contribute-mobile-context {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--pa-space-1) var(--pa-space-2);
  margin: 0 0 var(--pa-space-4);
  padding: 0 0 var(--pa-space-3);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.contribute-mobile-context__label {
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

.contribute-mobile-context__value {
  min-width: 0;
  overflow: hidden;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-20);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contribute-mobile-context__sub {
  grid-column: 2;
  min-width: 0;
  overflow: hidden;
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* v0.2.7-R1 P0-2 measured desktop layout model (real Windows runtime):
   - COMPACT_DESKTOP: 768px <= viewport < 1120px  -> rail + single column.
   - WIDE_DESKTOP:    viewport >= 1120px          -> rail + main|context.
   Content width = viewport - 68 (rail) - ~40 (page padding) - scrollbar.
   The designed workspace (main 680 + gap 48 + context 280 = 1008) fits with
   main >= 620 only from ~1120px CSS viewport upward; below that the column
   layout keeps the task readable instead of squeezing a broken two-column. */
@media (min-width: 1120px) {
  .contribute-workspace__layout {
    flex-direction: row;
    align-items: flex-start;
    justify-content: center;
    gap: 48px;
  }
  .contribute-workspace__context {
    position: sticky;
    top: var(--pa-space-5);
    padding: var(--pa-space-4);
    border: var(--pa-border-width) solid var(--pa-color-border-subtle);
    border-radius: var(--pa-radius-md);
    background: var(--pa-color-surface-raised);
  }
}
.contribute-start {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-6);
}

.contribute-start__hero {
  padding: var(--pa-space-5);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--pa-color-accent-weak) 82%, var(--pa-color-surface)) 0%,
    var(--pa-color-surface-raised) 72%
  );
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.contribute-start__kicker {
  margin: 0 0 var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-650);
  letter-spacing: var(--pa-letter-spacing-wide);
  color: var(--pa-color-accent);
}

.contribute-start__hero h2 {
  max-width: 560px;
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  line-height: var(--pa-line-height-32);
  color: var(--pa-color-text-primary);
  text-wrap: balance;
}

.contribute-start__intro {
  max-width: 620px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.contribute-needs-place-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
}

.contribute-start__facts {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
}

.contribute-start__section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--pa-space-3);
}

.contribute-start__section-head h3 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  color: var(--pa-color-text-primary);
}

.contribute-start__fact-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--pa-space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.contribute-start__fact-list li {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--pa-space-1);
  padding: var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
}

.contribute-start__fact-list strong {
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-md);
}

.contribute-start__fact-list span {
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

.contribute-start__boundary {
  margin: 0;
  padding: var(--pa-space-3) var(--pa-space-4);
  border-left: 3px solid var(--pa-color-accent);
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}
.contribute-workspace__notice {
  margin-top: var(--pa-space-5);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--pa-space-1);
}
.contribute-workspace__notice p {
  margin: 0;
  font-size: var(--pa-font-size-sm);
}
.contribute-step {
  margin: var(--pa-space-4) 0 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

@media (max-width: 620px) {
  .contribute-workspace__body {
    max-width: 100%;
    padding: var(--pa-space-3);
    box-sizing: border-box;
  }

  .contribute-workspace__layout,
  .contribute-workspace__main {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .contribute-workspace__main {
    padding: var(--pa-space-4);
    border-radius: var(--pa-radius-md);
  }

  .contribute-start {
    gap: var(--pa-space-4);
  }

  .contribute-start__hero {
    padding: var(--pa-space-4);
  }

  .contribute-start__section-head {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--pa-space-1);
  }

  .contribute-start__fact-list {
    grid-template-columns: 1fr;
  }
}
</style>
