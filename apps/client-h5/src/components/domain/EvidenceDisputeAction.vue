<script setup lang="ts">
import { computed, ref } from "vue";
import { client, type RealityEventView } from "@petaccess/client-core";
import { presentDescription } from "../../errors";

const props = withDefaults(defineProps<{ event: RealityEventView; signedIn?: boolean }>(), {
  signedIn: false,
});

const open = ref(false);
const submitted = ref(Boolean(props.event.dispute_open));
const reason = ref("incorrect_fact");
const note = ref("");
const busy = ref(false);
const error = ref("");

const targetType = computed(() => {
  if (props.event.event_type === "staff_response") return "staff_response_observation";
  if (props.event.event_type === "animal_facility") return "animal_facility";
  return "observed_presence";
});

const canSubmit = computed(() => !busy.value && note.value.trim().length >= 4);

async function submit() {
  if (!canSubmit.value) return;
  busy.value = true;
  error.value = "";
  try {
    await client.submitDispute({
      target_type: targetType.value,
      target_id: props.event.id,
      reason_code: reason.value,
      notice_text: note.value.trim(),
    });
    submitted.value = true;
    open.value = false;
  } catch (err) {
    error.value = presentDescription(err);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="evidence-dispute" data-ui="evidence-dispute">
    <p v-if="submitted" class="evidence-dispute__pending" data-testid="reality-dispute-pending">
      异议处理中 · 原记录会保留并标记，核验结论不会被用户直接改写。
    </p>

    <template v-else-if="signedIn">
      <button
        v-if="!open"
        type="button"
        class="btn-inline evidence-dispute__trigger"
        data-testid="reality-dispute-open"
        @click="open = true"
      >
        这条记录有误？提出异议 →
      </button>

      <form v-else class="evidence-dispute__form" @submit.prevent="submit">
        <label>
          <span>问题类型</span>
          <select v-model="reason" data-testid="reality-dispute-reason">
            <option value="incorrect_fact">事实内容不准确</option>
            <option value="wrong_place">场所 / 区域不对</option>
            <option value="wrong_time">时间不对</option>
            <option value="outdated">记录已过时</option>
            <option value="privacy">涉及隐私问题</option>
            <option value="other">其他</option>
          </select>
        </label>

        <label>
          <span>需要核验什么？</span>
          <textarea
            v-model="note"
            rows="3"
            maxlength="1000"
            data-testid="reality-dispute-note"
            placeholder="只写可核验事实，例如：这条记录对应的是隔壁门店。"
          />
        </label>

        <p v-if="error" class="notice evidence-dispute__error">{{ error }}</p>
        <div class="evidence-dispute__actions">
          <button type="button" class="btn-inline" @click="open = false">取消</button>
          <button
            type="submit"
            class="primary"
            :disabled="!canSubmit"
            data-testid="reality-dispute-submit"
          >
            {{ busy ? "提交中…" : "提交异议" }}
          </button>
        </div>
        <p class="muted evidence-dispute__note">
          提交只会开启核验流程，不会删除记录，也不会自动改变规则。
        </p>
      </form>
    </template>

    <RouterLink
      v-else
      class="btn-inline evidence-dispute__trigger"
      :to="{ name: 'onboarding', query: { next: `/place/${event.place_id}/evidence` } }"
      data-testid="reality-dispute-sign-in"
    >
      登录后提出异议 →
    </RouterLink>
  </div>
</template>

<style scoped src="./EvidenceDisputeAction.css"></style>
