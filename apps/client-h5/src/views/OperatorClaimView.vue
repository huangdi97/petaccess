<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { client, session, type PlaceDetail } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

const route = useRoute();
const router = useRouter();
const placeId = computed(() => String(route.params.id ?? ""));

const place = ref<PlaceDetail | null>(null);
const loading = ref(true);
const error = ref("");
const busy = ref(false);
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

const operatorName = ref("");
const orgType = ref<"company" | "government" | "property_mgmt" | "individual_owner" | "other">(
  "company",
);
const method = ref<"work_email" | "official_domain" | "other">("work_email");
const workEmail = ref("");
const website = ref("");
const note = ref("");

const methodReady = computed(() => {
  if (method.value === "work_email") return workEmail.value.trim().length > 3;
  if (method.value === "official_domain") return website.value.trim().length > 5;
  return note.value.trim().length >= 4;
});
const canSubmit = computed(
  () =>
    session.signedIn && operatorName.value.trim().length >= 2 && methodReady.value && !busy.value,
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await session.restore();
    place.value = await client.place(placeId.value);
    submitted.value = false;
    claimStatus.value = "";
    previousClaimStatus.value = "";
    if (session.signedIn) {
      const mine = await client.myOperatorClaims(placeId.value);
      const latest = mine[0];
      if (latest) {
        previousClaimStatus.value = latest.status;
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

async function submit() {
  if (!canSubmit.value || !place.value) return;
  busy.value = true;
  error.value = "";
  try {
    const result = await client.submitOperatorClaim({
      place_id: place.value.id,
      operator_name: operatorName.value.trim(),
      org_type: orgType.value,
      work_email: workEmail.value.trim() || null,
      website: website.value.trim() || null,
      verification_method: method.value,
      verification_note: note.value.trim() || null,
    });
    claimStatus.value = result.status;
    submitted.value = true;
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
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

        <section
          v-else-if="submitted"
          class="operator-claim__result"
          data-testid="operator-claim-result"
          role="status"
        >
          <strong>认领申请已提交</strong>
          <p>
            当前状态：{{ claimStatusLabel }}。审核通过前，你不会获得管理方权限，
            页面上的正式规则也不会因此改变。
          </p>
          <RouterLink class="btn primary" :to="`/place/${placeId}`">返回场所</RouterLink>
        </section>

        <form v-else class="operator-claim__form" @submit.prevent="submit">
          <p
            v-if="previousClaimStatus && ['rejected', 'revoked'].includes(previousClaimStatus)"
            class="operator-claim__previous"
            role="status"
          >
            上一次申请：{{ previousClaimStatusLabel }}。你可以修正核验信息后重新提交。
          </p>
          <label class="operator-claim__field">
            <span>管理方名称</span>
            <input v-model="operatorName" required maxlength="160" data-testid="operator-name" />
            <small>填写营业执照、官网或工作邮箱能够对应的主体名称。</small>
          </label>

          <label class="operator-claim__field">
            <span>主体类型</span>
            <select v-model="orgType" data-testid="operator-org-type">
              <option value="company">企业 / 品牌</option>
              <option value="property_mgmt">物业 / 商场管理方</option>
              <option value="individual_owner">个体经营者</option>
              <option value="government">政府 / 公共机构</option>
              <option value="other">其他</option>
            </select>
          </label>

          <label class="operator-claim__field">
            <span>优先核验方式</span>
            <select v-model="method" data-testid="operator-verification-method">
              <option value="work_email">工作邮箱</option>
              <option value="official_domain">官方网站</option>
              <option value="other">其他可核验方式</option>
            </select>
          </label>

          <label v-if="method === 'work_email'" class="operator-claim__field">
            <span>工作邮箱</span>
            <input
              v-model="workEmail"
              type="email"
              autocomplete="email"
              data-testid="operator-email"
            />
            <small>建议使用与管理方域名一致的工作邮箱。</small>
          </label>

          <label v-if="method === 'official_domain'" class="operator-claim__field">
            <span>官方网站</span>
            <input
              v-model="website"
              type="url"
              placeholder="https://…"
              data-testid="operator-website"
            />
            <small>填写能确认主体与当前场所关系的官网页面。</small>
          </label>

          <label class="operator-claim__field">
            <span>{{ method === "other" ? "核验说明" : "补充说明（可选）" }}</span>
            <textarea
              v-model="note"
              maxlength="500"
              data-testid="operator-verification-note"
              placeholder="例如：我的职位、场所与管理方关系、可由谁核验。"
            />
          </label>

          <p class="operator-claim__boundary">
            认领只建立“谁可以代表场所提交管理方声明”的身份关系。之后提交的管理方规则仍会保留来源、版本和适用范围；
            认领本身不是准入政策，也不会把一次工作人员处理升级成管理方规则。
          </p>

          <div class="operator-claim__actions">
            <button
              class="primary"
              type="submit"
              :disabled="!canSubmit"
              data-testid="operator-claim-submit"
            >
              {{ busy ? "提交中…" : "提交认领申请" }}
            </button>
            <RouterLink class="btn-inline" :to="`/place/${placeId}`">取消并返回</RouterLink>
          </div>
        </form>
      </template>
    </main>
  </AppShell>
</template>

<style scoped src="./OperatorClaimView.css"></style>
