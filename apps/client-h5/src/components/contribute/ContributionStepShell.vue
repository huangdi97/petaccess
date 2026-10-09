<script setup lang="ts">
/**
 * ContributionStepShell — contribution 多步表单的共享 step shell（v0.2.5 §28–32）。
 *
 * 负责：Place context（我在给哪个场所提交）+ progress（3-segment，非纯文本）+ title +
 * description + question body（slot）+ footer actions（back/secondary 与 primary 各恰一）+ privacy link。
 *
 * Step content max width 640；视觉区域至少 440–520（靠 layout，不塞内容）。
 * §50 gate：option group 不使用 pill 风格（radio rows），primary CTA 恰 1、secondary back 恰 1。
 */
import ContributionProgress from "./ContributionProgress.vue";

defineOptions({ name: "ContributionStepShell" });

withDefaults(
  defineProps<{
    /** §29：我当前在给哪个场所提交。 */
    placeName: string;
    placeZone?: string;
    /** §30：当前步骤（1/2/3）与总步数。 */
    step: number;
    total: number;
    title: string;
    description?: string;
  }>(),
  { description: "", placeZone: "范围待确认" },
);

defineEmits<{ back: [] }>();
</script>

<template>
  <section class="step-shell" data-testid="step-shell" data-ui="contribution-step-shell">
    <!-- §29 place context -->
    <p class="step-shell__place" data-testid="step-place-context">
      <span class="step-shell__place-label">当前场所</span>
      <strong>{{ placeName }}</strong>
      <span>· {{ placeZone }}</span>
    </p>

    <ContributionProgress :step="step" :total="total" />

    <h2 class="step-shell__title">{{ title }}</h2>
    <p v-if="description" class="muted step-shell__desc">{{ description }}</p>

    <!-- question body -->
    <div class="step-shell__body">
      <slot />
    </div>

    <!-- footer actions：primary 恰 1，secondary back 恰 1（§32）。 -->
    <footer class="step-shell__actions">
      <button type="button" class="step-shell__back" data-testid="step-back" @click="$emit('back')">
        返回
      </button>
      <slot name="primary" />
    </footer>

    <!-- §42 privacy/help link -->
    <p class="step-shell__privacy">
      提交内容会进入人工核验。
      <RouterLink class="btn-inline" to="/privacy" data-testid="privacy-link">
        隐私与审核说明 →
      </RouterLink>
    </p>
  </section>
</template>

<style scoped src="./ContributionStepShell.css"></style>
