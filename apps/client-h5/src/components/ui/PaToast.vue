<script setup lang="ts">
/**
 * PaToast — transient bottom-centre notification (V020 catalog #20).
 * role="status", or role="alert" for kind="error". Auto-closes after
 * `duration` ms unless duration is 0 (sticky until `close` is emitted).
 */
import { computed, onBeforeUnmount, onMounted } from "vue";
import type { IconName } from "@petaccess/design-tokens";
import PaIcon from "./PaIcon.vue";
import PaIconButton from "./PaIconButton.vue";

type ToastKind = "success" | "info" | "warning" | "error";

const KIND_ICON: Record<ToastKind, IconName> = {
  success: "check-circle",
  info: "info",
  warning: "warning",
  error: "x-circle",
};

const props = withDefaults(
  defineProps<{
    kind: ToastKind;
    message: string;
    /** Auto-close delay in ms; 0 keeps the toast until `close` is emitted. */
    duration?: number;
  }>(),
  { duration: 3500 },
);

const emit = defineEmits<{ close: [] }>();

defineOptions({ name: "PaToast" });

const icon = computed<IconName>(() => KIND_ICON[props.kind]);

let timer: ReturnType<typeof setTimeout> | undefined;

function scheduleClose() {
  if (props.duration > 0) timer = setTimeout(() => emit("close"), props.duration);
}

onMounted(scheduleClose);
onBeforeUnmount(() => {
  if (timer) clearTimeout(timer);
});
</script>

<template>
  <div class="pa-toast" :class="`pa-toast--${kind}`" :role="kind === 'error' ? 'alert' : 'status'">
    <PaIcon :name="icon" size="md" class="pa-toast__icon" aria-hidden="true" />
    <p class="pa-toast__message">{{ message }}</p>
    <PaIconButton icon="close" label="关闭提示" size="sm" @click="emit('close')" />
  </div>
</template>

<style scoped>
.pa-toast {
  position: fixed;
  bottom: calc(var(--pa-safe-bottom) + var(--pa-space-5));
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--pa-z-toast);
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  width: max-content;
  max-width: var(--pa-layout-max-width);
  background: var(--pa-color-surface-raised);
  border-radius: var(--pa-radius-md);
  box-shadow: var(--pa-elevation-3);
  padding: var(--pa-space-2) var(--pa-space-3);
}

.pa-toast__message {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-base);
  color: var(--pa-color-text-primary);
}

.pa-toast--success .pa-toast__icon {
  color: var(--pa-color-status-allowed);
}

.pa-toast--info .pa-toast__icon {
  color: var(--pa-color-accent);
}

.pa-toast--warning .pa-toast__icon {
  color: var(--pa-color-status-conditional);
}

.pa-toast--error .pa-toast__icon {
  color: var(--pa-color-status-restricted);
}
</style>
