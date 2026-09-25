<script setup lang="ts">
/**
 * ContributeQuickForm — 快速确认：判断已收录规则是否仍与现场一致（legacy verify 端点）。
 * 不改写规则内容；不确定同样有价值。
 */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { proximity } from "./contributeSupport";
import { presentDescription } from "../../errors";

defineOptions({ name: "ContributeQuickForm" });

const props = defineProps<{
  placeId: string;
  online: boolean;
  signedIn: boolean;
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();

const result = ref<"still_valid" | "changed" | "uncertain">("still_valid");
const busy = ref(false);
const error = ref("");
const canSubmit = computed(() => props.online && props.signedIn && !busy.value);

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
  <div>
    <strong>页面显示的已收录规则，目前仍然如此吗？</strong>
    <p class="muted" style="margin-top: 4px">
      你只需判断现场是否与已收录内容一致；这不会修改规则内容本身。
    </p>
    <div v-if="error" class="notice" data-testid="quick-error">{{ error }}</div>
    <div class="row" style="margin-top: 10px">
      <button
        class="pill"
        :class="{ active: result === 'still_valid' }"
        data-testid="quick-still-valid"
        @click="result = 'still_valid'"
      >
        仍然如此
      </button>
      <button
        class="pill"
        :class="{ active: result === 'changed' }"
        data-testid="quick-changed"
        @click="result = 'changed'"
      >
        已变化
      </button>
      <button
        class="pill"
        :class="{ active: result === 'uncertain' }"
        data-testid="quick-uncertain"
        @click="result = 'uncertain'"
      >
        不确定
      </button>
    </div>
    <div class="row" style="margin-top: 14px">
      <button class="primary" :disabled="!canSubmit" data-testid="quick-submit" @click="submit">
        {{ busy ? "提交中…" : "提交确认" }}
      </button>
      <button :disabled="busy" @click="emit('back')">返回</button>
    </div>
  </div>
</template>
