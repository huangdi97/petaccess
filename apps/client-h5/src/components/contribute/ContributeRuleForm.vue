<script setup lang="ts">
/**
 * ContributeRuleForm — 我知道规则（结构化表单，legacy createObservation 规则路径）。
 * 提交为「用户陈述」，与场所正式规则并存展示，不覆盖已收录规则。
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { isoAt, proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";

defineOptions({ name: "ContributeRuleForm" });

const props = defineProps<{
  placeId: string;
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

async function submit() {
  if (!canSubmit.value || !knowRule.value) return;
  error.value = "";
  busy.value = true;
  try {
    await client.createObservation({
      place_id: props.placeId,
      zone_id: zone.value || null,
      occurred_at: isoAt(new Date().toISOString().slice(0, 10)),
      occurred_precision: "same_day",
      animal_scope: "dog",
      observed_action: "enter",
      staff_action: "no_interaction_observed",
      place_confidence: "confirmed_on_site",
      note: [`用户声明：${knowRule.value}`, conditions.value.join(",")].filter(Boolean).join(" | "),
      evidence_refs: null,
      ...proximity(),
    });
    emit(
      "done",
      "已提交你的说明。这是「用户陈述」，会与场所正式规则并存展示，不会覆盖已收录的规则。",
    );
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div>
    <strong>我知道规则（结构化表单）</strong>
    <p class="muted" style="margin-top: 4px">
      你的说明会以「用户陈述」与场所正式规则并存展示，不会覆盖已收录规则。
    </p>
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
    <div class="row">
      <button
        v-for="c in CONDITION_OPTIONS"
        :key="c.key"
        class="pill"
        :class="{ active: conditions.includes(c.key) }"
        @click="
          conditions.includes(c.key)
            ? (conditions = conditions.filter((k) => k !== c.key))
            : conditions.push(c.key)
        "
      >
        {{ c.label }}
      </button>
    </div>

    <div class="row" style="margin-top: 14px">
      <button
        class="primary"
        :disabled="!canSubmit || !knowRule"
        data-testid="rule-submit"
        @click="submit"
      >
        {{ busy ? "提交中…" : "提交" }}
      </button>
      <button :disabled="busy" @click="emit('back')">返回</button>
    </div>
  </div>
</template>
