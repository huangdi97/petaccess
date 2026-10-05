<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, type RuleView } from "@petaccess/client-core";

const props = defineProps<{
  placeId: string;
  zones: { id: string; name: string }[];
}>();

const model = defineModel<string>({ required: true });
const rules = ref<RuleView[]>([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    rules.value = (await client.rules(props.placeId)).filter((rule) => rule.status === "current");
    if (rules.value.length === 1 && !model.value) model.value = rules.value[0]?.id ?? "";
  } catch {
    rules.value = [];
  } finally {
    loading.value = false;
  }
}

function label(rule: RuleView): string {
  const scope =
    rule.animal_scope === "dog"
      ? "犬"
      : rule.animal_scope === "cat"
        ? "猫"
        : rule.animal_scope === "ordinary_pet"
          ? "普通宠物"
          : "其他动物";
  const effect =
    rule.effect === "allowed"
      ? "允许进入"
      : rule.effect === "prohibited"
        ? "限制进入"
        : rule.effect === "conditional"
          ? "有条件进入"
          : "结论待核验";
  const zoneName = props.zones.find((zone) => zone.id === rule.zone_id)?.name;
  return `${scope} · ${effect} · ${zoneName ?? "场所范围"}`;
}

onMounted(load);
</script>

<template>
  <div class="rule-target">
    <label for="rule-target">这次针对哪一条已收录规则？</label>
    <select
      id="rule-target"
      v-model="model"
      data-testid="rule-target"
      :disabled="loading || !rules.length"
    >
      <option value="">
        {{ loading ? "正在读取已收录规则…" : rules.length ? "请选择具体规则" : "当前没有可核验规则" }}
      </option>
      <option v-for="rule in rules" :key="rule.id" :value="rule.id">
        {{ label(rule) }}
      </option>
    </select>
    <p class="rule-target__note">
      多条规则必须明确选择目标，避免把“仍有效 / 已变化”写到另一条规则上。
    </p>
  </div>
</template>

<style scoped>
.rule-target {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.rule-target label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

.rule-target__note {
  margin: 0;
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-muted);
  line-height: var(--pa-line-height-20);
}
</style>
