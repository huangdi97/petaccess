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
  { description: "", placeZone: "公共区域" },
);

defineEmits<{ back: [] }>();
</script>

<template>
  <section class="step-shell" data-testid="step-shell" data-ui="contribution-step-shell">
    <!-- §29 place context -->
    <p class="step-shell__place" data-testid="step-place-context">
      {{ placeName }} · {{ placeZone }}
    </p>

    <!-- §30 progress：3-segment 条 + 文本 -->
    <div class="step-shell__progress" role="group" aria-label="步骤进度">
      <div
        v-for="i in total"
        :key="i"
        class="step-shell__segment"
        :class="{ 'step-shell__segment--active': i <= step }"
        aria-hidden="true"
      />
      <span class="muted step-shell__progress-label" data-testid="contribute-step">
        步骤 {{ step }} / {{ total }}
      </span>
    </div>

    <h2 class="step-shell__title">{{ title }}</h2>
    <p v-if="description" class="muted step-shell__desc">{{ description }}</p>

    <!-- question body -->
    <div class="step-shell__body">
      <slot />
    </div>

    <!-- footer actions：primary 恰 1，secondary back 恰 1（§32）。 -->
    <footer class="step-shell__actions">
      <button
        type="button"
        class="step-shell__back"
        data-testid="step-back"
        @click="$emit('back')"
      >
        返回
      </button>
      <slot name="primary" />
    </footer>

    <!-- §42 privacy/help link -->
    <p class="step-shell__privacy">
      <RouterLink class="btn-inline" to="/privacy" data-testid="privacy-link">
        隐私与审核说明 →
      </RouterLink>
    </p>
  </section>
</template>

<style scoped>
.step-shell {
  min-height: 440px;
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0 var(--pa-space-4);
}
.step-shell__place {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-secondary);
}
.step-shell__progress {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
}
.step-shell__segment {
  flex: 1 1 0;
  height: 4px;
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-border);
}
.step-shell__segment--active {
  background: var(--pa-color-accent);
}
.step-shell__progress-label {
  margin-left: var(--pa-space-2);
  white-space: nowrap;
}
.step-shell__title {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-24);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-32);
  color: var(--pa-color-text-primary);
}
.step-shell__desc {
  margin: 0;
}
.step-shell__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-3);
  flex: 1 1 auto;
}
.step-shell__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-4);
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.step-shell__back {
  border: none;
  background: transparent;
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-base);
  min-height: var(--pa-size-control-md);
  padding: 0 var(--pa-space-2);
  cursor: pointer;
}
.step-shell__back:hover,
.step-shell__back:focus-visible {
  color: var(--pa-color-text-primary);
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -1px;
}
.step-shell__privacy {
  margin: var(--pa-space-2) 0 0;
}

@media (max-width: 767px) {
  .step-shell {
    min-height: 480px;
  }
}
</style>