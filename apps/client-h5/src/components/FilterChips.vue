<script setup lang="ts">
/**
 * Reusable filter chips (spec §2.2). Multi-select; the caller owns the state.
 *
 * Two product rules are encoded in the markup, not in prose:
 *   - the active count is announced, so a user can see a filter is narrowing;
 *   - "信息不足" is a first-class option that is OFF by default, and clearing
 *     filters is one tap — the product never hides unknown places silently.
 */
export interface ChipOption {
  key: string;
  label: string;
}

const props = withDefaults(
  defineProps<{
    options: ChipOption[];
    modelValue: string[];
    /** Always-visible reminder that filtering is optional and neutral. */
    hint?: string | null;
  }>(),
  { hint: null },
);

const emit = defineEmits<{ "update:modelValue": [value: string[]] }>();

function toggle(key: string) {
  const next = props.modelValue.includes(key)
    ? props.modelValue.filter((k) => k !== key)
    : [...props.modelValue, key];
  emit("update:modelValue", next);
}
</script>

<template>
  <div class="filter-bar">
    <div class="row" role="group" aria-label="筛选">
      <button
        v-for="o in options"
        :key="o.key"
        class="pill"
        :class="{ active: modelValue.includes(o.key) }"
        :aria-pressed="modelValue.includes(o.key)"
        :data-filter="o.key"
        @click="toggle(o.key)"
      >
        {{ o.label }}
      </button>
      <button
        v-if="modelValue.length"
        class="pill"
        data-testid="filter-clear"
        @click="emit('update:modelValue', [])"
      >
        清除筛选（{{ modelValue.length }}）
      </button>
    </div>
    <p v-if="hint" class="muted" style="margin: 6px 0 0">{{ hint }}</p>
  </div>
</template>
