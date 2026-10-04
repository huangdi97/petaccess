<script setup lang="ts">
import { BOUNDARY_ATTRIBUTES, BOUNDARY_STANCE_LABELS } from "../../consumer/boundaryOptions";

defineProps<{ chosen: Record<string, string> }>();
const emit = defineEmits<{ pick: [attribute: string, stance: string] }>();
</script>

<template>
  <section class="boundary-list" aria-label="共处偏好">
    <div
      v-for="attr in BOUNDARY_ATTRIBUTES"
      :key="attr.value"
      class="boundary-row"
      data-testid="boundary-attr"
    >
      <div class="boundary-row__body">
        <strong>{{ attr.label }}</strong>
        <span v-if="chosen[attr.value]" class="muted">
          当前：{{ BOUNDARY_STANCE_LABELS[chosen[attr.value]] }}
        </span>
        <span v-else class="muted">未设置</span>
      </div>

      <div class="boundary-choices" :aria-label="attr.label">
        <button
          v-for="stance in attr.stances"
          :key="stance"
          type="button"
          class="boundary-choice"
          :class="{ 'boundary-choice--active': chosen[attr.value] === stance }"
          :aria-pressed="chosen[attr.value] === stance"
          :data-testid="`stance-${attr.value}-${stance}`"
          @click="emit('pick', attr.value, stance)"
        >
          {{ BOUNDARY_STANCE_LABELS[stance] }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.boundary-list {
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto;
  align-items: center;
  gap: var(--pa-space-5);
  min-height: 72px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.boundary-choices {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--pa-space-1);
}

.boundary-choice {
  min-height: 36px;
  padding: 0 var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-secondary);
  cursor: pointer;
}

.boundary-choice:hover,
.boundary-choice:focus-visible {
  border-color: var(--pa-color-accent);
}

.boundary-choice--active {
  border-color: var(--pa-color-accent);
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-600);
}

@media (max-width: 767px) {
  .boundary-row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-2);
    align-items: flex-start;
  }

  .boundary-choices {
    justify-content: flex-start;
  }
}
</style>
