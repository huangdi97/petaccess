<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { client, session, type PlaceDetail, type Zone } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import OperatorClaimForm from "../components/operator/OperatorClaimForm.vue";
import OperatorPolicyForm from "../components/operator/OperatorPolicyForm.vue";
import { presentDescription } from "../errors";

const route = useRoute();
const router = useRouter();
const placeId = computed(() => String(route.params.id ?? ""));

const place = ref<PlaceDetail | null>(null);
const zones = ref<Zone[]>([]);
const activeClaimId = ref("");
const loading = ref(true);
const error = ref("");
const submitted = ref(false);
const claimStatus = ref("");
const previousClaimStatus = ref("");

const CLAIM_STATUS_LABELS: Record<string, string> = {
  submitted: "等待人工核验",
  verifying: "正在核验",
  approved: "认领已通过",
  rejected: "认领未通过",
  revoked: "认领已撤销",
};

const claimStatusLabel = computed(() => CLAIM_STATUS_LABELS[claimStatus.value] ?? "等待人工核验");
const previousClaimStatusLabel = computed(
  () => CLAIM_STATUS_LABELS[previousClaimStatus.value] ?? "",
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await session.restore();
    [place.value, zones.value] = await Promise.all([
      client.place(placeId.value),
      client.zones(placeId.value).catch(() => [] as Zone[]),
    ]);
    submitted.value = false;
    claimStatus.value = "";
    previousClaimStatus.value = "";
    activeClaimId.value = "";
    if (session.signedIn) {
      const mine = await client.myOperatorClaims(placeId.value);
      const latest = mine[0];
      if (latest) {
        previousClaimStatus.value = latest.status;
        activeClaimId.value = latest.id;
        if (["submitted", "verifying", "approved"].includes(latest.status)) {
          claimStatus.value = latest.status;
          submitted.value = true;
        }
      }
    }
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

function handleSubmitted(claimId: string, status: string) {
  activeClaimId.value = claimId;
  claimStatus.value = status;
  submitted.value = true;
}

watch(placeId, () => void load(), { immediate: true });
</script>

<template>
  <AppShell>
    <main class="operator-claim" data-testid="operator-claim-page">
      <header class="operator-claim__head">
        <h1>场所方认领</h1>
        <p class="muted">
          认领用于确认谁有权代表场所维护管理方声明。提交认领不会自动改变任何准入规则，也不会删除用户现场记录。
        </p>
      </header>

      <SkeletonList v-if="loading" :rows="3" />
      <StateMessage v-else-if="error" kind="ERROR" :description="error">
        <template #action>
          <button class="primary" @click="load">重试</button>
        </template>
      </StateMessage>

      <template v-else-if="place">
        <section class="operator-claim__place">
          <strong>{{ place.canonical_name }}</strong>
          <p class="muted">{{ place.canonical_address ?? "地址未收录" }}</p>
        </section>

        <StateMessage
          v-if="!session.signedIn"
          kind="PERMISSION_DENIED"
          title="登录后才能提交场所方认领"
          description="公开规则与现场仍可免登录浏览。认领需要绑定申请人身份并进入人工核验。"
        >
          <template #action>
            <button
              class="primary"
              @click="
                router.push({
                  name: 'onboarding',
                  query: { next: `/place/${placeId}/operator-claim` },
                })
              "
            >
              去登录
            </button>
          </template>
        </StateMessage>

        <template v-else-if="submitted">
          <section class="operator-claim__result" data-testid="operator-claim-result" role="status">
            <strong>{{
              claimStatus === "approved" ? "场所方身份已核验" : "认领申请已提交"
            }}</strong>
            <p v-if="claimStatus === 'approved'">
              当前状态：{{
                claimStatusLabel
              }}。你现在可以提交管理方正式政策；法律、监管规则与现场事实仍保持独立。
            </p>
            <p v-else>
              当前状态：{{ claimStatusLabel }}。审核通过前，你不会获得管理方权限，
              页面上的正式规则也不会因此改变。
            </p>
            <RouterLink class="btn-inline" :to="`/place/${placeId}`">返回场所 →</RouterLink>
          </section>

          <OperatorPolicyForm
            v-if="claimStatus === 'approved' && activeClaimId"
            :claim-id="activeClaimId"
            :zones="zones"
          />
        </template>

        <OperatorClaimForm
          v-else
          :place-id="placeId"
          :previous-status-label="
            ['rejected', 'revoked'].includes(previousClaimStatus)
              ? previousClaimStatusLabel
              : undefined
          "
          @submitted="handleSubmitted"
          @error="error = $event"
        />
      </template>
    </main>
  </AppShell>
</template>

<style scoped src="./OperatorClaimView.css"></style>
