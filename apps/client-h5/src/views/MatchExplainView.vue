<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  client,
  ApiError,
  session,
  type AccessAnswer,
  type BoundaryMatchResult,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import BoundaryMatchPanel from "../components/explain/BoundaryMatchPanel.vue";
import ExplainResultPanel from "../components/explain/ExplainResultPanel.vue";
import StateMessage from "../components/StateMessage.vue";
import { consumerExplanation } from "../consumer/explanation";
import { presentDescription } from "../errors";

const route = useRoute();
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));
const resolved = ref<AccessAnswer | null>(null);
const boundary = ref<BoundaryMatchResult | null>(null);
const error = ref("");
const note = ref("");
const busy = ref(false);

const steps = computed(() => (resolved.value ? consumerExplanation(resolved.value) : []));

async function resolveRules() {
  error.value = "";
  busy.value = true;
  try {
    const animal = session.activePet
      ? {
          animal: session.activePet.species,
          service_role: session.activePet.service_role ?? "none",
          declared_role: session.activePet.declared_role ?? null,
        }
      : { animal: "dog", service_role: session.mode === "service_dog" ? "working" : "none" };
    resolved.value = await client.accessAnswer(placeId.value, { ...animal, action: "enter" });
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}

async function loadBoundary() {
  note.value = "";
  if (!session.signedIn) {
    boundary.value = null;
    note.value = "尚未设置共处边界，设置后可在此逐项比对。";
    return;
  }
  try {
    boundary.value = await client.boundaryMatch(placeId.value);
  } catch (e) {
    if (
      e instanceof ApiError &&
      (e as unknown as { code?: string }).code === "no_boundary_profile"
    ) {
      boundary.value = null;
      note.value = "尚未设置共处边界，设置后可在此逐项比对。";
      return;
    }
    note.value = presentDescription(e);
  }
}

watch(
  placeId,
  () => {
    if (!placeId.value) return;
    void Promise.all([resolveRules(), loadBoundary()]);
  },
  { immediate: true },
);
</script>

<template>
  <AppShell>
    <header class="explain-head">
      <div>
        <h1>为什么是这个结果</h1>
        <p class="muted">
          这里展示当前查询所依据的规则层级、适用条件和来源；不会用一次现场观察替代正式规则。
        </p>
      </div>
      <button
        type="button"
        class="explain-refresh"
        :disabled="busy"
        data-testid="re-resolve"
        @click="resolveRules"
      >
        {{ busy ? "更新中…" : "重新获取" }}
      </button>
    </header>

    <StateMessage v-if="error" kind="ERROR" :description="error" data-testid="match-error">
      <template #action>
        <button type="button" class="primary" @click="resolveRules">重试</button>
      </template>
    </StateMessage>

    <ExplainResultPanel v-if="resolved" :answer="resolved" :steps="steps" />
    <BoundaryMatchPanel :boundary="boundary" :note="note" />
  </AppShell>
</template>

<style scoped>
.explain-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-5);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.explain-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.explain-refresh {
  flex: 0 0 auto;
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  cursor: pointer;
}

@media (max-width: 767px) {
  .explain-head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }
}
</style>
