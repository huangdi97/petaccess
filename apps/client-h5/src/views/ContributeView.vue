<script setup lang="ts">
/**
 * ContributeView — M7 contribution wizard orchestrator (A1/A4).
 * Keeps the gating (place / signed-in), the step machine and the shared form
 * props; every screen is a step component. Reality contributions go through
 * the parent-flow API (ContributeRealityForm); quick / signage / rule /
 * experience keep their legacy endpoints. No free-text comment box.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, session } from "@petaccess/client-core";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import StateMessage from "../components/StateMessage.vue";
import ContributeEntry from "../components/contribute/ContributeEntry.vue";
import ContributeQuickForm from "../components/contribute/ContributeQuickForm.vue";
import ContributeSignageForm from "../components/contribute/ContributeSignageForm.vue";
import ContributeRuleForm from "../components/contribute/ContributeRuleForm.vue";
import ContributeObservationForm from "../components/contribute/ContributeObservationForm.vue";
import ContributeRealityForm from "../components/contribute/ContributeRealityForm.vue";
import ContributeDone from "../components/contribute/ContributeDone.vue";
import { useBreakpoint } from "../composables/useBreakpoint";
import { useOnline } from "../composables/useOnline";

defineOptions({ name: "ContributeView" });

type Step = "entry" | "quick" | "signage" | "rule" | "experience" | "reality" | "done";
type RealityKind = "observed_presence" | "staff_response" | "animal_facility";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));
const { online } = useOnline();

const step = ref<Step>("entry");
const realityKind = ref<RealityKind>("observed_presence");
const msg = ref("");
const signedIn = ref(false);
const zones = ref<{ id: string; name: string }[]>([]);
/** §29：step shell 顶部显示「我给哪个场所提交」。 */
const placeName = ref("");

// Reactive param + immediate: the router reuses this component across
// /contribute/:id changes; every submit carries place_id, so re-anchor first.
watch(
  placeId,
  async () => {
    reset();
    zones.value = [];
    placeName.value = "";
    await session.restore();
    signedIn.value = session.signedIn;
    if (!signedIn.value || !placeId.value) return;
    try {
      const [zs, place] = await Promise.all([
        client.zones(placeId.value),
        client.place(placeId.value).catch(() => null),
      ]);
      zones.value = zs;
      placeName.value = place?.canonical_name ?? "";
    } catch {
      /* best-effort; forms work without zones/name */
    }
  },
  { immediate: true },
);

function reset() {
  step.value = "entry";
  msg.value = "";
}

function startReality(kind: RealityKind) {
  realityKind.value = kind;
  step.value = "reality";
}

function done(m: string) {
  msg.value = m;
  step.value = "done";
}

/** O6 capture-state integrity (§40/§41): the wizard exposes real states —
 * choose-type (entry), focused form steps (step-1 = legacy confirmations,
 * step-2 = reality parent-flow), done. Every value maps to an actual screen. */
const uiState = computed<string>(() => {
  if (!placeId.value) return "needs-place";
  if (!signedIn.value) return "sign-in-required";
  switch (step.value) {
    case "entry":
      return "choose-type";
    case "done":
      return "done";
    case "reality":
      return "step-2";
    default:
      return "step-1";
  }
});
/** §41: choice-count must reflect the real number of options on the entry. */
const choiceCount = computed<number>(() => (uiState.value === "choose-type" ? 5 : 0));

/** §15 context rail：本次贡献类型 —— 从真实 step 状态推导，不伪造。 */
const STEP_LABELS: Record<string, string> = {
  "choose-type": "选择贡献类型",
  "step-1": "提交确认信息",
  "step-2": "现场记录",
  done: "提交完成",
};
const contributionKindLabel = computed(() => STEP_LABELS[uiState.value] ?? "现场贡献");
/** §15 context rail：适用区域 —— 真实 zones 数据（无则保持 shell 默认）。 */
const contextZoneLabel = computed(() => {
  const first = zones.value[0];
  return first ? `${first.name} 等 ${zones.value.length} 个区域` : "公共区域";
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
    <QueryContextBar v-if="placeId" />
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

          <StateMessage
            v-if="!placeId"
            kind="PARTIAL"
            data-testid="contribute-needs-place"
            description="现场贡献绑定到具体场所与区域。先在搜索或地图里选定一个场所，再从该场所发起。"
          >
            <template #action>
              <RouterLink class="btn primary" to="/search" data-testid="contribute-go-search"
                >去搜索场所</RouterLink
              >
              <RouterLink
                class="btn"
                to="/map"
                style="margin-left: 8px"
                data-testid="contribute-go-map"
                >看地图</RouterLink
              >
            </template>
          </StateMessage>

          <StateMessage
            v-else-if="!signedIn"
            kind="PERMISSION_DENIED"
            description="贡献需要登录后进行，以便记录来源与核验历史。未登录不会提交任何数据。"
          >
            <template #action>
              <RouterLink class="btn primary" to="/onboarding">登录 / 注册</RouterLink>
            </template>
          </StateMessage>

          <template v-else>
            <ContributeEntry
              v-if="step === 'entry'"
              @select="step = $event"
              @reality="startReality"
            />
            <ContributeQuickForm
              v-else-if="step === 'quick'"
              :place-id="placeId"
              :place-name="placeName"
              :online="online"
              :signed-in="signedIn"
              @done="done"
              @back="reset"
            />
            <ContributeSignageForm
              v-else-if="step === 'signage'"
              :place-id="placeId"
              :place-name="placeName"
              :zones="zones"
              :online="online"
              :signed-in="signedIn"
              @done="done"
              @back="reset"
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
            />
            <ContributeObservationForm
              v-else-if="step === 'experience'"
              :place-id="placeId"
              :place-name="placeName"
              :zones="zones"
              :online="online"
              :signed-in="signedIn"
              @done="done"
              @back="reset"
            />
            <ContributeRealityForm
              v-else-if="step === 'reality'"
              :place-id="placeId"
              :place-name="placeName"
              :zones="zones"
              :online="online"
              :signed-in="signedIn"
              :kind="realityKind"
              @done="done"
              @back="reset"
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
          v-if="isDesktop && placeId && signedIn && uiState !== 'done'"
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
}
.contribute-workspace__body {
  /* v0.2.7 §16：TASK workspace 总宽 900–1040 —— main 680 + gap 48 + context 280。
     Mobile 保持单列（context rail 在桌面才渲染）。 */
  padding: var(--pa-space-4) var(--pa-space-5) var(--pa-space-7);
  max-width: 1040px;
  margin: 0 auto;
}
.contribute-workspace__layout {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-6);
}
.contribute-workspace__main {
  flex: 1 1 auto;
  min-width: 0;
  max-width: 680px;
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
  color: var(--pa-color-text-secondary);
}
.contribute-context__value {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
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
@media (min-width: 1024px) {
  .contribute-workspace__layout {
    flex-direction: row;
    align-items: flex-start;
    justify-content: center;
    gap: 48px;
  }
  .contribute-workspace__context {
    border-top: none;
    padding-top: var(--pa-space-3);
  }
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
</style>
