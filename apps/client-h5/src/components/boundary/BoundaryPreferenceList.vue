<script setup lang="ts">
import { BOUNDARY_ATTRIBUTES, BOUNDARY_STANCE_LABELS } from "../../consumer/boundaryOptions";

defineProps<{ chosen: Record<string, string> }>();
const emit = defineEmits<{ pick: [attribute: string, stance: string] }>();
</script>

<template>
  <section class="boundary-list" aria-label="共处偏好">
    <fieldset
      v-for="attr in BOUNDARY_ATTRIBUTES"
      :key="attr.value"
      class="boundary-row"
      data-testid="boundary-attr"
    >
      <legend class="boundary-row__body">
        <strong>{{ attr.label }}</strong>
        <span class="muted">
          {{ chosen[attr.value] ? BOUNDARY_STANCE_LABELS[chosen[attr.value]] : "未设置" }}
        </span>
      </legend>

      <div class="boundary-choices">
        <label class="boundary-choice">
          <input
            type="radio"
            :name="`boundary-${attr.value}`"
            value=""
            :checked="!chosen[attr.value]"
            :data-testid="`stance-${attr.value}-unset`"
            @change="emit('pick', attr.value, '')"
          />
          <span>不设置</span>
        </label>

        <label v-for="stance in attr.stances" :key="stance" class="boundary-choice">
          <input
            type="radio"
            :name="`boundary-${attr.value}`"
            :value="stance"
            :checked="chosen[attr.value] === stance"
            :data-testid="`stance-${attr.value}-${stance}`"
            @change="emit('pick', attr.value, stance)"
          />
          <span>{{ BOUNDARY_STANCE_LABELS[stance] }}</span>
        </label>
      </div>
    </fieldset>
  </section>
</template>

<style scoped>
.boundary-list {
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(0, 1.35fr);
  align-items: center;
  gap: var(--pa-space-5);
  min-inline-size: 0;
  min-height: 72px;
  margin: 0;
  padding: var(--pa-space-3) 0;
  border: 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  min-width: 0;
  padding: 0;
}

.boundary-row__body strong {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
  color: var(--pa-color-text-primary);
}

.boundary-row__body .muted {
  font-size: var(--pa-font-size-sm);
}

.boundary-choices {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--pa-space-2) var(--pa-space-4);
}

.boundary-choice {
  display: inline-flex;
  align-items: center;
  gap: var(--pa-space-2);
  min-height: 36px;
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-md);
  cursor: pointer;
}

.boundary-choice input {
  width: 16px;
  height: 16px;
  margin: 0;
  accent-color: var(--pa-color-accent);
}

.boundary-choice:has(input:checked) {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-600);
}

.boundary-choice:focus-within {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 3px;
  border-radius: var(--pa-radius-sm);
}

@media (max-width: 767px) {
  .boundary-row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-2);
    align-items: flex-start;
    padding: var(--pa-space-4) 0;
  }

  .boundary-choices {
    justify-content: flex-start;
    gap: var(--pa-space-2) var(--pa-space-3);
  }
}
</style>
