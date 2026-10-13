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
        <span class="boundary-row__current">
          当前：{{ chosen[attr.value] ? BOUNDARY_STANCE_LABELS[chosen[attr.value]] : "未设置" }}
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
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--pa-space-3);
  margin-top: var(--pa-space-4);
}

.boundary-row {
  display: flex;
  min-inline-size: 0;
  min-width: 0;
  flex-direction: column;
  gap: var(--pa-space-3);
  min-height: 154px;
  margin: 0;
  padding: var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background: var(--pa-color-surface-raised);
  box-shadow: 0 1px 0 color-mix(in srgb, var(--pa-color-text-primary) 4%, transparent);
}

.boundary-row__body {
  display: flex;
  width: 100%;
  min-width: 0;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: 0;
}

.boundary-row__body strong {
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-20);
}

.boundary-row__current {
  flex: 0 0 auto;
  max-width: 52%;
  padding: 3px 8px;
  border-radius: var(--pa-radius-pill);
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  text-align: right;
}

.boundary-choices {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(88px, 1fr));
  gap: 4px;
  width: 100%;
  min-width: 0;
  margin-top: auto;
  padding: 4px;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-control) + 2px);
  background: var(--pa-color-surface-muted);
}

.boundary-choice {
  position: relative;
  min-width: 0;
  cursor: pointer;
}

.boundary-choice input {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.boundary-choice span {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 7px 10px;
  border: var(--pa-border-width) solid transparent;
  border-radius: var(--pa-radius-control);
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-500);
  line-height: 1.25;
  text-align: center;
  transition:
    background var(--pa-motion-fast) var(--pa-motion-ease),
    border-color var(--pa-motion-fast) var(--pa-motion-ease),
    color var(--pa-motion-fast) var(--pa-motion-ease),
    box-shadow var(--pa-motion-fast) var(--pa-motion-ease);
}

.boundary-choice:hover span {
  background: var(--pa-color-surface-interactive);
  color: var(--pa-color-text-primary);
}

.boundary-choice input:checked + span {
  border-color: color-mix(in srgb, var(--pa-color-accent) 22%, var(--pa-color-border-subtle));
  background: var(--pa-color-surface-raised);
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-650);
  box-shadow: var(--pa-elevation-1);
}

.boundary-choice input:focus-visible + span {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

@media (max-width: 767px) {
  .boundary-list {
    grid-template-columns: 1fr;
    gap: var(--pa-space-2);
    margin-top: var(--pa-space-3);
  }

  .boundary-row {
    min-height: 0;
    padding: var(--pa-space-3);
  }

  .boundary-row__body {
    align-items: center;
  }

  .boundary-row__current {
    max-width: 58%;
  }

  .boundary-choices {
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  }

  .boundary-choice span {
    min-height: 42px;
    padding: 8px 9px;
  }
}

@media (max-width: 380px) {
  .boundary-choices {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
