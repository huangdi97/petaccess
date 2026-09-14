<script setup lang="ts">
/**
 * Page-level async / edge state block (Master Goal §5.5).
 *
 * Renders one of the non-loading page states from the shared vocabulary. The
 * icon and the title are always in the DOM, so the state is never communicated
 * by colour alone; `role="status"` makes it announced when it appears.
 *
 * LOADING is intentionally not handled here — callers render `SkeletonList`
 * instead, because a skeleton communicates "content is coming and here is its
 * shape", which a message cannot.
 */
import { computed } from "vue";
import { PAGE_STATES, type PageStateKey } from "@petaccess/design-tokens";

const props = withDefaults(
  defineProps<{
    kind: Exclude<PageStateKey, "LOADING">;
    /** Override the default sentence when the view has something more precise. */
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
