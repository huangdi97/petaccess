<script setup lang="ts">
/**
 * Page-level async / edge state block — admin build (Master Goal §5.5).
 *
 * Same vocabulary as the consumer app: the wording comes from
 * `PAGE_STATES` in @petaccess/design-tokens, and the icon plus title are always
 * rendered so the state is never conveyed by colour alone.
 *
 * LOADING is handled by `.skeleton` markup instead, because a skeleton conveys
 * the shape of what is coming, which a message cannot.
 */
import { computed } from "vue";
import { PAGE_STATES, type PageStateKey } from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{
    kind: Exclude<PageStateKey, "LOADING">;
    /** Override the default sentence when the view knows something more precise. */
    description?: string | null;
  }>(),
  { description: null },
);

const state = computed(() => PAGE_STATES[props.kind]);
const body = computed(() => props.description ?? state.value.description);
</script>

<template>
  <div class="state-message" :data-state="state.key" role="status">
    <div class="state-message__icon" aria-hidden="true">{{ state.icon }}</div>
    <div class="state-message__title">{{ state.title }}</div>
    <p class="state-message__body">{{ body }}</p>
    <div v-if="$slots.action" class="state-message__action">
      <slot name="action" />
    </div>
  </div>
</template>
