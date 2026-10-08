<script setup lang="ts">
import { computed, ref } from "vue";
import { client, type Zone } from "@petaccess/client-core";
import { presentDescription } from "../../errors";

const props = defineProps<{
  claimId: string;
  zones: Zone[];
}>();

const zoneId = ref("");
const animalScope = ref<"ordinary_pet" | "dog" | "cat" | "service_dog">("ordinary_pet");
const action = ref<"enter" | "stay" | "dine" | "ride_elevator" | "ground_contact">("enter");
const effect = ref<"allowed" | "conditional" | "prohibited">("conditional");
const conditions = ref<string[]>([]);
const effectiveDate = ref("");
const note = ref("");
const busy = ref(false);
const error = ref("");
const result = ref("");

const CONDITION_OPTIONS = [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
];

const canSubmit = computed(
  () => !busy.value && (effect.value !== "conditional" || conditions.value.length > 0),
);

function toggleCondition(key: string) {
  conditions.value = conditions.value.includes(key)
    ? conditions.value.filter((item) => item !== key)
    : [...conditions.value, key];
}

function effectiveFrom(): string | undefined {
  if (!effectiveDate.value) return undefined;
  return new Date(`${effectiveDate.value}T00:00:00`).toISOString();
}

async function submit() {
  if (!canSubmit.value) return;
  busy.value = true;
  error.value = "";
  result.value = "";
  try {
    const answer = {
      zone_id: zoneId.value || null,
      animal_scope: animalScope.value,
      action: action.value,
      effect: effect.value,
      conditions:
        effect.value === "conditional"
          ? conditions.value.map((condition_type) => ({ condition_type, value_flag: true }))
          : [],
      note: note.value.trim() || null,
    };
    await client.submitOperatorRules(props.claimId, [answer], effectiveFrom());
    result.value =
      "管理方政策已提交并形成新的版本。它只更新对应的管理方政策单元，不覆盖法律或监管规则。";
    note.value = "";
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="operator-policy" data-testid="operator-policy">
    <header class="operator-policy__head">
      <h2>维护管理方规则</h2>
      <p class="muted">
        你的场所方身份已经核验。这里提交的是管理方正式政策，不是现场 Observation；
        新版本只替换同一政策单元，不会覆盖法律或监管规则。
      </p>
    </header>

    <div v-if="error" class="notice" role="alert">{{ error }}</div>
    <div v-if="result" class="notice operator-policy__result" role="status">{{ result }}</div>

    <form class="operator-policy__form" @submit.prevent="submit">
      <div class="operator-policy__grid">
        <label class="operator-policy__field">
          <span>适用区域</span>
          <select v-model="zoneId" data-testid="operator-policy-zone">
            <option value="">全场</option>
            <option v-for="zone in zones" :key="zone.id" :value="zone.id">
              {{ zone.name }}
            </option>
          </select>
        </label>

        <label class="operator-policy__field">
          <span>动物范围</span>
          <select v-model="animalScope" data-testid="operator-policy-animal">
            <option value="ordinary_pet">普通宠物</option>
            <option value="dog">犬只</option>
            <option value="cat">猫</option>
            <option value="service_dog">服务犬</option>
          </select>
        </label>

        <label class="operator-policy__field">
          <span>行为</span>
          <select v-model="action" data-testid="operator-policy-action">
            <option value="enter">进入</option>
            <option value="stay">停留</option>
            <option value="dine">就餐</option>
            <option value="ride_elevator">乘电梯</option>
            <option value="ground_contact">落地活动</option>
          </select>
        </label>

        <label class="operator-policy__field">
          <span>管理方结论</span>
          <select v-model="effect" data-testid="operator-policy-effect">
            <option value="allowed">允许</option>
            <option value="conditional">有条件允许</option>
            <option value="prohibited">禁止</option>
          </select>
        </label>
      </div>

      <fieldset v-if="effect === 'conditional'" class="operator-policy__conditions">
        <legend>进入条件</legend>
        <div class="operator-policy__condition-list">
          <label v-for="item in CONDITION_OPTIONS" :key="item.key" class="operator-policy__check">
            <input
              type="checkbox"
              :checked="conditions.includes(item.key)"
              @change="toggleCondition(item.key)"
            />
            <span>{{ item.label }}</span>
          </label>
        </div>
        <small>
          “有条件允许”至少需要一项明确条件；没有把握的条件不要补写，也不要用自由文本代替结构化条件。
        </small>
      </fieldset>

      <div class="operator-policy__grid">
        <label class="operator-policy__field">
          <span>生效日期（可选）</span>
          <input v-model="effectiveDate" type="date" data-testid="operator-policy-effective" />
          <small>留空表示从本次提交时间开始。</small>
        </label>

        <label class="operator-policy__field">
          <span>补充说明（可选）</span>
          <textarea
            v-model="note"
            maxlength="1000"
            data-testid="operator-policy-note"
            placeholder="只补充适用范围、例外或现场执行说明。"
          />
        </label>
      </div>

      <p class="operator-policy__boundary">
        这条记录属于 OPERATOR_POLICY。它不会把工作人员的一次处理变成政策，也不能覆盖
        LEGAL / REGULATORY_GUIDANCE；现场事实与证据仍独立保留。
      </p>

      <button
        class="primary"
        type="submit"
        :disabled="!canSubmit"
        data-testid="operator-policy-submit"
      >
        {{ busy ? "提交中…" : "提交管理方规则" }}
      </button>
    </form>
  </section>
</template>

<style scoped src="./OperatorPolicyForm.css"></style>
