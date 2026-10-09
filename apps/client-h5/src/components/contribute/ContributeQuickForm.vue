<script setup lang="ts">
/**
 * ContributeQuickForm — place correction lead.
 *
 * The entry label is "场所信息有误", so this flow must not silently turn into
 * a rule-verification flow. Corrections stay review evidence until a human
 * applies them to the appropriate Place/Rule/Reality record.
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

type CorrectionKind = "name" | "address" | "place_state" | "other";
const kind = ref<CorrectionKind>("address");
const detail = ref("");
const correctValueUnknown = ref(false);
const busy = ref(false);
const error = ref("");

const OPTIONS: { key: CorrectionKind; label: string; hint: string }[] = [
  { key: "name", label: "名称有误", hint: "名称、别名或门店标识不准确" },
  { key: "address", label: "地址 / 位置有误", hint: "地址、楼层或地图位置需要修正" },
  { key: "place_state", label: "场所状态有变化", hint: "例如已关闭、搬迁或重复收录" },
  { key: "other", label: "其他场所信息", hint: "不属于以上类型的基础信息问题" },
];

const canSubmit = computed(
  () =>
    props.online &&
    props.signedIn &&
    !busy.value &&
    (correctValueUnknown.value || detail.value.trim().length >= 2),
);

async function submit() {
  if (!canSubmit.value || !props.placeId) return;
  error.value = "";
  busy.value = true;
  try {
    const selected = OPTIONS.find((option) => option.key === kind.value);
    await client.verify({
      place_id: props.placeId,
      rule_id: null,
      event_type: "place_correction",
      result: "uncertain",
      note: correctValueUnknown.value
        ? `${selected?.label ?? "场所信息纠错"}：当前信息有误，但提交者不知道正确值`
        : `${selected?.label ?? "场所信息纠错"}：${detail.value.trim()}`,
      evidence_refs: null,
      ...proximity(),
    });
    emit("done", "纠错线索已提交，等待人工核验。核验完成前不会直接改写场所、规则或现场事实。");
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
    place-zone="场所整体"
    :step="2"
    :total="3"
    title="哪里需要纠正？"
    description="先指出哪类基础信息有误；提交后进入人工核验，不会直接改写场所或规则。"
    @back="emit('back')"
  >
    <div v-if="error" class="notice" data-testid="quick-error">{{ error }}</div>

    <div
      class="option-group"
      role="radiogroup"
      aria-label="需要纠正的信息类型"
      data-testid="quick-options"
    >
      <button
        v-for="option in OPTIONS"
        :key="option.key"
        type="button"
        class="option-row"
        role="radio"
        :aria-checked="kind === option.key"
        :class="{ 'option-row--active': kind === option.key }"
        @click="kind = option.key"
      >
        <span class="option-row__radio" aria-hidden="true" />
        <span class="option-row__text">
          <span class="option-row__label">{{ option.label }}</span>
          <span class="muted option-row__hint">{{ option.hint }}</span>
        </span>
      </button>
    </div>

    <label class="correction-unknown">
      <input v-model="correctValueUnknown" type="checkbox" data-testid="correction-unknown" />
      <span>
        我只知道当前信息有误，不知道正确值
        <small class="muted">不确定是合法答案；人工核验会继续补充。</small>
      </span>
    </label>

    <label v-if="!correctValueUnknown" class="correction-detail" for="correction-detail">
      <span>正确情况或需要核验的内容</span>
      <textarea
        id="correction-detail"
        v-model="detail"
        rows="4"
        maxlength="600"
        data-testid="correction-detail"
        placeholder="例如：商场地址应为……；该门店已于……搬迁。"
      />
      <small class="muted">只写可核验事实，不需要评价场所。</small>
    </label>

    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="quick-submit" @click="submit">
        {{ busy ? "提交中…" : "提交纠错线索" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped src="./ContributeQuickForm.css"></style>
