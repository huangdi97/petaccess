<script setup lang="ts">
/**
 * ContributeRuleForm — structured Rule lead, never an Observation.
 *
 * A visitor can report what they saw/heard about a rule, but the submission
 * remains review evidence until a reviewer creates/accepts a RuleCandidate.
 * Observation != Rule is structural here: this form never calls the onsite
 * Observation endpoint.
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";
import ContributionStepShell from "./ContributionStepShell.vue";

defineOptions({ name: "ContributeRuleForm" });

const props = defineProps<{
  placeId: string;
  placeName: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const knowRule = ref<"allowed" | "restricted" | "conditional" | "">("");
const zone = ref("");
const conditions = ref<string[]>([]);
const busy = ref(false);
const error = ref("");

const CONDITION_OPTIONS = [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
];

const canSubmit = computed(() => props.online && props.signedIn && !busy.value);

function toggleCondition(key: string) {
  conditions.value = conditions.value.includes(key)
    ? conditions.value.filter((k) => k !== key)
    : [...conditions.value, key];
}

async function submit() {
  if (!canSubmit.value || !knowRule.value) return;
  error.value = "";
  busy.value = true;
  try {
    const resultLabel =
      knowRule.value === "allowed"
        ? "明确允许"
        : knowRule.value === "restricted"
          ? "明确限制"
          : "有条件进入";
    const zoneLabel = props.zones.find((item) => item.id === zone.value)?.name ?? "全场 / 不确定";
    const conditionLabel = conditions.value.length ? conditions.value.join("、") : "未补充条件";
    await client.verify({
      place_id: props.placeId,
      zone_id: zone.value || null,
      rule_id: null,
      event_type: "rule_lead_submitted",
      result: "uncertain",
      note: `规则线索：${resultLabel}；区域：${zoneLabel}；条件：${conditionLabel}`,
      evidence_refs: null,
      ...proximity(),
    });
    emit(
      "done",
      "规则线索已提交，等待人工复核。它不会作为现场 Observation 展示，也不会自动变成正式规则。",
    );
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <ContributionStepShell
    :place-name="placeName"
    :step="1"
    :total="3"
    title="我看到或了解到一条规则"
    description="先把它作为规则线索提交。人工核验并形成正式 RuleCandidate 之前，不会改变页面上的正式规则结论。"
    @back="emit('back')"
  >
    <div v-if="error" class="notice" data-testid="rule-error">{{ error }}</div>

    <label for="rule-known">你了解到的规则是</label>
    <select v-model="knowRule" id="rule-known" data-testid="rule-known">
      <option value="">请选择</option>
      <option value="allowed">明确允许</option>
      <option value="restricted">明确限制</option>
      <option value="conditional">有条件进入</option>
    </select>

    <label for="rule-zone">适用区域</label>
    <select v-model="zone" id="rule-zone">
      <option value="">全场 / 不确定</option>
      <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
    </select>

    <label>条件（可多选 / 全不选）</label>
    <!-- §31 checkbox option rows（多选，非 pill）。 -->
    <div class="option-group" role="group" aria-label="规则条件">
      <button
        v-for="c in CONDITION_OPTIONS"
        :key="c.key"
        type="button"
        class="option-row"
        role="checkbox"
        :aria-checked="conditions.includes(c.key)"
        :class="{ 'option-row--active': conditions.includes(c.key) }"
        @click="toggleCondition(c.key)"
      >
        <span class="option-row__checkbox" aria-hidden="true" />
        <span class="option-row__text">
          <span class="option-row__label">{{ c.label }}</span>
        </span>
      </button>
    </div>

    <template #primary>
      <button
        class="primary"
        :disabled="!canSubmit || !knowRule"
        data-testid="rule-submit"
        @click="submit"
      >
        {{ busy ? "提交中…" : "提交" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped>
.option-group {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}
.option-row {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: 56px;
  padding: var(--pa-space-2) var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
  text-align: left;
  cursor: pointer;
}
.option-row--active {
  border-color: var(--pa-color-accent);
  background: var(--pa-color-accent-weak);
}
.option-row__checkbox {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  border: 2px solid var(--pa-color-border-strong);
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.option-row--active .option-row__checkbox {
  border-color: var(--pa-color-accent);
  background: var(--pa-color-accent);
}
.option-row--active .option-row__checkbox::after {
  content: "✓";
  color: var(--pa-color-surface);
  font-size: 13px;
  line-height: 1;
}
.option-row__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.option-row__label {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
.option-row__hint {
  font-size: var(--pa-font-size-sm);
}
.option-row:hover,
.option-row:focus-visible {
  border-color: var(--pa-color-accent);
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -1px;
}
</style>
