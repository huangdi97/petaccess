<script setup lang="ts">
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { presentDescription } from "../../errors";

const props = defineProps<{
  placeId: string;
  previousStatusLabel?: string;
}>();
const emit = defineEmits<{
  submitted: [claimId: string, status: string];
  error: [message: string];
}>();

const operatorName = ref("");
const orgType = ref<"company" | "government" | "property_mgmt" | "individual_owner" | "other">(
  "company",
);
const method = ref<"work_email" | "official_domain" | "other">("work_email");
const workEmail = ref("");
const website = ref("");
const note = ref("");
const busy = ref(false);

const methodReady = computed(() => {
  if (method.value === "work_email") return workEmail.value.trim().length > 3;
  if (method.value === "official_domain") return website.value.trim().length > 5;
  return note.value.trim().length >= 4;
});
const canSubmit = computed(
  () => operatorName.value.trim().length >= 2 && methodReady.value && !busy.value,
);

async function submit() {
  if (!canSubmit.value) return;
  busy.value = true;
  emit("error", "");
  try {
    const result = await client.submitOperatorClaim({
      place_id: props.placeId,
      operator_name: operatorName.value.trim(),
      org_type: orgType.value,
      work_email: workEmail.value.trim() || null,
      website: website.value.trim() || null,
      verification_method: method.value,
      verification_note: note.value.trim() || null,
    });
    emit("submitted", result.id, result.status);
  } catch (error) {
    emit("error", presentDescription(error));
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <form class="operator-claim-form" @submit.prevent="submit">
    <p v-if="previousStatusLabel" class="operator-claim-form__previous" role="status">
      上一次申请：{{ previousStatusLabel }}。你可以修正核验信息后重新提交。
    </p>

    <label class="operator-claim-form__field">
      <span>管理方名称</span>
      <input v-model="operatorName" required maxlength="160" data-testid="operator-name" />
      <small>填写营业执照、官网或工作邮箱能够对应的主体名称。</small>
    </label>

    <label class="operator-claim-form__field">
      <span>主体类型</span>
      <select v-model="orgType" data-testid="operator-org-type">
        <option value="company">企业 / 品牌</option>
        <option value="property_mgmt">物业 / 商场管理方</option>
        <option value="individual_owner">个体经营者</option>
        <option value="government">政府 / 公共机构</option>
        <option value="other">其他</option>
      </select>
    </label>

    <label class="operator-claim-form__field">
      <span>优先核验方式</span>
      <select v-model="method" data-testid="operator-verification-method">
        <option value="work_email">工作邮箱</option>
        <option value="official_domain">官方网站</option>
        <option value="other">其他可核验方式</option>
      </select>
    </label>

    <label v-if="method === 'work_email'" class="operator-claim-form__field">
      <span>工作邮箱</span>
      <input v-model="workEmail" type="email" autocomplete="email" data-testid="operator-email" />
      <small>建议使用与管理方域名一致的工作邮箱。</small>
    </label>

    <label v-if="method === 'official_domain'" class="operator-claim-form__field">
      <span>官方网站</span>
      <input v-model="website" type="url" placeholder="https://…" data-testid="operator-website" />
      <small>填写能确认主体与当前场所关系的官网页面。</small>
    </label>

    <label class="operator-claim-form__field">
      <span>{{ method === "other" ? "核验说明" : "补充说明（可选）" }}</span>
      <textarea
        v-model="note"
        maxlength="500"
        data-testid="operator-verification-note"
        placeholder="例如：我的职位、场所与管理方关系、可由谁核验。"
      />
    </label>

    <p class="operator-claim-form__boundary">
      认领只建立“谁可以代表场所提交管理方声明”的身份关系。认领本身不是准入政策，
      也不会把一次工作人员处理升级成管理方规则。
    </p>

    <div class="operator-claim-form__actions">
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

<style scoped src="./OperatorClaimForm.css"></style>
