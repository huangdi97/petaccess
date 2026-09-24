<script setup lang="ts">
/**
 * PaErrorState — unified domain error state (V020 catalog #25). Folds the
 * ERROR_PRESENTATIONS dictionary into a presentation; raw title/description/
 * retryLabel props override it for one-off pages. role="alert".
 */
import { computed } from "vue";
import {
  ERROR_PRESENTATIONS,
  type ErrorPresentation,
  type IconName,
} from "@petaccess/design-tokens";
import PaButton from "./PaButton.vue";
import PaIcon from "./PaIcon.vue";

const KIND_ICON: Record<ErrorPresentation["kind"], IconName> = {
  NETWORK_OFFLINE: "offline",
  SERVICE_UNAVAILABLE: "warning",
  AUTH_EXPIRED: "user",
  MAP_UNAVAILABLE: "map",
  CONTENT_NOT_FOUND: "question-circle",
  UNKNOWN_ERROR: "warning",
};

const props = withDefaults(
  defineProps<{
    presentation?: ErrorPresentation | null;
    onRetry?: (() => void) | null;
    /** Raw overrides; each falls back to the presentation dictionary. */
    title?: string | null;
    description?: string | null;
    retryLabel?: string | null;
  }>(),
  { presentation: null, onRetry: null, title: null, description: null, retryLabel: null },
);

defineOptions({ name: "PaErrorState" });

const effective = computed<ErrorPresentation>(
  () => props.presentation ?? ERROR_PRESENTATIONS.UNKNOWN_ERROR,
);

const icon = computed<IconName>(() => KIND_ICON[effective.value.kind]);
const title = computed(() => props.title ?? effective.value.title);
const description = computed(() => props.description ?? effective.value.description);
const retryLabel = computed(() => props.retryLabel ?? (effective.value.retryLabel || "重试"));

const showRetry = computed(() => typeof props.onRetry === "function");

function handleRetry() {
  props.onRetry?.();
}
</script>

<template>
  <div class="pa-error" data-state="ERROR" role="alert">
    <span class="pa-error__icon">
      <PaIcon :name="icon" size="lg" aria-hidden="true" />
    </span>
    <h2 class="pa-error__title">{{ title }}</h2>
    <p class="pa-error__description">{{ description }}</p>
    <PaButton v-if="showRetry" variant="primary" class="pa-error__action" @click="handleRetry">
      {{ retryLabel }}
    </PaButton>
  </div>
</template>

<style scoped>
.pa-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--pa-space-6) var(--pa-space-4);
}

.pa-error__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--pa-space-7);
  height: var(--pa-space-7);
  border-radius: 50%;
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-secondary);
}

.pa-error__title {
  margin: var(--pa-space-4) 0 0;
  font-size: var(--pa-font-size-xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.pa-error__description {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-muted);
}

.pa-error__action {
  margin-top: var(--pa-space-5);
}
</style>
