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

const uiFixture = computed<string>(() => `contribution-${uiState.value}-v1`);
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
    <div class="contribute-workspace__body">
      <h1 class="visually-hidden">
        {{ uiState === "choose-type" ? "你刚刚知道了什么？" : "现场贡献" }}
      </h1>
      <span v-if="uiState === 'choose-type'" class="visually-hidden" data-ui-count="choice-count">{{
        choiceCount
      }}</span>

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
          <RouterLink class="btn" to="/map" style="margin-left: 8px" data-testid="contribute-go-map"
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
        <ContributeEntry v-if="step === 'entry'" @select="step = $event" @reality="startReality" />
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
    </div>
  </div>
</template>

<style scoped>
.contribute-workspace {
  min-height: 100%;
}
.contribute-workspace__body {
  padding: var(--pa-space-4);
  max-width: var(--pa-layout-content-680);
  margin: 0 auto;
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
