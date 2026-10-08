<script setup lang="ts">
type RuleIntent = "still_valid" | "changed" | "signage" | "new_lead";

defineProps<{ zones: { id: string; name: string }[] }>();

const intent = defineModel<RuleIntent>("intent", { required: true });
const effect = defineModel<"allowed" | "restricted" | "conditional" | "">("effect", {
  required: true,
});
const animalScope = defineModel<"ordinary_pet" | "dog" | "cat" | "other">("animalScope", {
  required: true,
});
const zone = defineModel<string>("zone", { required: true });
const conditions = defineModel<string[]>("conditions", { required: true });
const sourceBasis = defineModel<string>("sourceBasis", { required: true });

const INTENTS = [
  { key: "still_valid", label: "页面规则仍然如此", hint: "确认已收录规则目前仍与现场一致" },
  { key: "changed", label: "页面规则已经变化", hint: "指出现在了解到的新情况" },
  { key: "signage", label: "我拍到了规则牌 / 公告", hint: "只提交证据也可以，不要求你先解释规则" },
  { key: "new_lead", label: "我知道或了解到一条规则", hint: "提交新的规则线索，等待人工核验" },
] as const;

const CONDITION_OPTIONS = [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
] as const;

const SOURCE_BASIS_OPTIONS = [
  { key: "onsite_signage", label: "现场规则牌 / 公告" },
  { key: "staff_statement", label: "工作人员口头说明" },
  { key: "official_online", label: "场所或政府官方公开信息" },
  { key: "other", label: "其他线索" },
  { key: "uncertain", label: "不确定来源类型" },
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

  <div
    v-if="intent === 'changed' || intent === 'new_lead'"
    class="rule-fields"
    data-ui="rule-lead-fields"
  >
    <h3>你现在了解到的规则</h3>
    <label for="rule-known">结论</label>
    <select id="rule-known" v-model="effect" data-testid="rule-known">
      <option value="">请选择</option>
      <option value="allowed">明确允许</option>
      <option value="restricted">明确限制</option>
      <option value="conditional">有条件进入</option>
    </select>

    <label for="rule-source-basis">你是怎么知道的？</label>
    <select id="rule-source-basis" v-model="sourceBasis" data-testid="rule-source-basis">
      <option value="">请选择</option>
      <option v-for="option in SOURCE_BASIS_OPTIONS" :key="option.key" :value="option.key">
        {{ option.label }}
      </option>
    </select>
    <p class="muted rule-fields__source-note">
      工作人员口头说明只作为待核验线索，不会自动变成管理方正式政策。
    </p>

    <label for="rule-animal-scope">适用动物</label>
    <select id="rule-animal-scope" v-model="animalScope" data-testid="rule-animal-scope">
      <option value="ordinary_pet">普通宠物</option>
      <option value="dog">犬</option>
      <option value="cat">猫</option>
      <option value="other">其他动物</option>
    </select>

    <label for="rule-zone">适用区域</label>
    <select id="rule-zone" v-model="zone" :disabled="intent === 'changed'">
      <option value="">全场 / 不确定</option>
      <option v-for="item in zones" :key="item.id" :value="item.id">{{ item.name }}</option>
    </select>
    <p v-if="intent === 'changed'" class="muted rule-fields__source-note">
      规则变化必须沿用所选现行规则的空间范围；选择具体规则后会自动带入。
    </p>

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

  <div v-if="intent === 'signage'" class="rule-fields" data-ui="rule-signage-scope">
    <h3>这张规则牌在哪里？</h3>
    <label for="rule-signage-zone">所在区域（可选）</label>
    <select id="rule-signage-zone" v-model="zone" data-testid="rule-signage-zone">
      <option value="">场所范围 / 不确定</option>
      <option v-for="item in zones" :key="item.id" :value="item.id">{{ item.name }}</option>
    </select>
    <p class="muted rule-fields__source-note">
      只记录你能确认的空间范围；不确定时保持场所范围，不从照片内容猜测区域。
    </p>
  </div>
</template>

<style scoped src="./RuleLeadFields.css"></style>
