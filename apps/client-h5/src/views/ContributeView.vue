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
import AppShell from "../components/AppShell.vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
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

// Reactive param + immediate: the router reuses this component across
// /contribute/:id changes; every submit carries place_id, so re-anchor first.
watch(
  placeId,
  async () => {
    reset();
    zones.value = [];
    await session.restore();
    signedIn.value = session.signedIn;
    if (!signedIn.value || !placeId.value) return;
    try {
      zones.value = await client.zones(placeId.value);
    } catch {
      /* best-effort; forms work without zones */
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
</script>

<template>
  <AppShell>
    <h1 class="visually-hidden">现场贡献</h1>
    <DesktopContentContainer mode="single-column">
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
        <div class="panel">
          <ContributeEntry
            v-if="step === 'entry'"
            @select="step = $event"
            @reality="startReality"
          />
          <ContributeQuickForm
            v-else-if="step === 'quick'"
            :place-id="placeId"
            :online="online"
            :signed-in="signedIn"
            @done="done"
            @back="reset"
          />
          <ContributeSignageForm
            v-else-if="step === 'signage'"
            :place-id="placeId"
            :zones="zones"
            :online="online"
            :signed-in="signedIn"
            @done="done"
            @back="reset"
          />
          <ContributeRuleForm
            v-else-if="step === 'rule'"
            :place-id="placeId"
            :zones="zones"
            :online="online"
            :signed-in="signedIn"
            @done="done"
            @back="reset"
          />
          <ContributeObservationForm
            v-else-if="step === 'experience'"
            :place-id="placeId"
            :zones="zones"
            :online="online"
            :signed-in="signedIn"
            @done="done"
            @back="reset"
          />
          <ContributeRealityForm
            v-else-if="step === 'reality'"
            :place-id="placeId"
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
        </div>

        <div class="notice">
          位置仅记录分桶后的现场核验结果（距离/精度），不保存原始 GPS 轨迹（ADR-012）。
          高频提交会被限流。证据媒体不公开，仅审核可见。
        </div>
      </template>
    </DesktopContentContainer>
  </AppShell>
</template>
