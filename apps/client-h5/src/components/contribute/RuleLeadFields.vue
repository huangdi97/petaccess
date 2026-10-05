<script setup lang="ts">
type RuleIntent = "still_valid" | "changed" | "new_lead";

defineProps<{ zones: { id: string; name: string }[] }>();

const intent = defineModel<RuleIntent>("intent", { required: true });
const effect = defineModel<"allowed" | "restricted" | "conditional" | "">("effect", {
  required: true,
});
const zone = defineModel<string>("zone", { required: true });
const conditions = defineModel<string[]>("conditions", { required: true });

const INTENTS = [
  { key: "still_valid", label: "页面规则仍然如此", hint: "确认已收录规则目前仍与现场一致" },
  { key: "changed", label: "页面规则已经变化", hint: "指出现在了解到的新情况" },
  { key: "new_lead", label: "我看到或了解到一条规则", hint: "提交新的规则线索，等待人工核验" },
] as const;

const CONDITION_OPTIONS = [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
] as const;

function toggleCondition(key: string) {
  conditions.value = conditions.value.includes(key)
    ? conditions.value.filter((value) => value !== key)
    : [...conditions.value, key];
}
</script>

<template>
  <div class="rule-intents" role="radiogroup" aria-label="规则线索类型">
    <button
      v-for="option in INTENTS"
      :key="option.key"
      type="button"
      class="rule-intent"
      :class="{ 'rule-intent--active': intent === option.key }"
      role="radio"
      :aria-checked="intent === option.key"
      :data-testid="`rule-intent-${option.key}`"
      @click="intent = option.key"
    >
      <span class="rule-intent__mark" aria-hidden="true" />
      <span class="rule-intent__copy">
        <span class="rule-intent__label">{{ option.label }}</span>
        <span class="muted rule-intent__hint">{{ option.hint }}</span>
      </span>
    </button>
  </div>

  <div v-if="intent !== 'still_valid'" class="rule-fields" data-ui="rule-lead-fields">
    <h3>你现在了解到的规则</h3>
    <label for="rule-known">结论</label>
    <select id="rule-known" v-model="effect" data-testid="rule-known">
      <option value="">请选择</option>
      <option value="allowed">明确允许</option>
      <option value="restricted">明确限制</option>
      <option value="conditional">有条件进入</option>
    </select>

    <label for="rule-zone">适用区域</label>
    <select id="rule-zone" v-model="zone">
      <option value="">全场 / 不确定</option>
      <option v-for="item in zones" :key="item.id" :value="item.id">{{ item.name }}</option>
    </select>

    <label>已知条件（可多选）</label>
    <div class="condition-options" role="group" aria-label="规则条件">
      <button
        v-for="option in CONDITION_OPTIONS"
        :key="option.key"
        type="button"
        class="condition-option"
        :class="{ 'condition-option--active': conditions.includes(option.key) }"
        role="checkbox"
        :aria-checked="conditions.includes(option.key)"
        @click="toggleCondition(option.key)"
      >
        <span class="condition-option__mark" aria-hidden="true" />
        <span class="condition-option__label">{{ option.label }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped src="./RuleLeadFields.css"></style>
