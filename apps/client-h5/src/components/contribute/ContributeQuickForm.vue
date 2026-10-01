<script setup lang="ts">
/**
 * ContributeQuickForm — 快速确认：判断已收录规则是否仍与现场一致（legacy verify 端点）。
 * v0.2.5 §28–32：统一走 ContributeStepShell（place context / progress / title /
 * question body / footer），选项组改为 radio option rows（§31，非 pill）。
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";
import ContributionStepShell from "./ContributionStepShell.vue";

defineOptions({ name: "ContributeQuickForm" });

const props = defineProps<{
  placeId: string;
  placeName: string;
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const result = ref<"still_valid" | "changed" | "uncertain">("still_valid");
const busy = ref(false);
const error = ref("");
const canSubmit = computed(() => props.online && props.signedIn && !busy.value);

const OPTIONS: { key: "still_valid" | "changed" | "uncertain"; label: string; hint: string }[] = [
  { key: "still_valid", label: "仍然如此", hint: "与页面显示内容一致" },
  { key: "changed", label: "已变化", hint: "现场规则与页面记录不同" },
  { key: "uncertain", label: "不确定", hint: "暂时无法判断" },
];

async function submit() {
  if (!canSubmit.value || !props.placeId) return;
  error.value = "";
  busy.value = true;
  try {
    const rules = await client.rules(props.placeId);
    const target = rules.find((r) => r.status === "current") ?? rules[0];
    await client.verify({
      place_id: props.placeId,
      rule_id: target?.id ?? null,
      event_type: "field_check",
      result: result.value,
      note: null,
      ...proximity(),
    });
    emit(
      "done",
      result.value === "still_valid"
        ? "已记录：现场与已收录规则一致。这会提高该规则的核验置信度，但不会改变规则内容。"
        : result.value === "changed"
          ? "已记录：现场与已收录规则不一致。该记录进入人工复核队列，规则不会自动改写。"
          : "已记录：不确定。不确定的记录同样有价值，不会被当作否定。",
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
    title="页面显示的已收录规则，目前仍然如此吗？"
    description="你只需判断现场是否与已收录内容一致；这不会修改规则内容本身。"
    @back="emit('back')"
  >
    <div v-if="error" class="notice" data-testid="quick-error">{{ error }}</div>
    <!-- §31 radio option rows（非 pill）。 -->
    <div class="option-group" role="radiogroup" aria-label="现场与规则是否一致" data-testid="quick-options">
      <button
        v-for="opt in OPTIONS"
        :key="opt.key"
        type="button"
        class="option-row"
        role="radio"
        :aria-checked="result === opt.key"
        :class="{ 'option-row--active': result === opt.key }"
        :data-testid="`quick-${opt.key}`"
        @click="result = opt.key"
      >
        <span class="option-row__radio" aria-hidden="true" />
        <span class="option-row__text">
          <span class="option-row__label">{{ opt.label }}</span>
          <span class="muted option-row__hint">{{ opt.hint }}</span>
        </span>
      </button>
    </div>

    <template #primary>
      <button
        class="primary"
        :disabled="!canSubmit"
        data-testid="quick-submit"
        @click="submit"
      >
        {{ busy ? "提交中…" : "提交确认" }}
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
.option-row__radio {
  width: 18px;
  height: 18px;
  border-radius: var(--pa-radius-pill);
  border: 2px solid var(--pa-color-border-strong);
  flex: 0 0 auto;
}
.option-row--active .option-row__radio {
  border-color: var(--pa-color-accent);
  background: radial-gradient(circle, var(--pa-color-accent) 0 5px, transparent 6px);
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