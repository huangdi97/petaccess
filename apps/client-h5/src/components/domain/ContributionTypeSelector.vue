<script setup lang="ts">
/**
 * ContributionTypeSelector — 贡献线索时选择事实类型.
 *
 * Radio-style selection over the contribution types; the selected option's
 * description explains what that type covers.
 */
import { computed } from "vue";
import PaRadioGroup from "../ui/PaRadioGroup.vue";

export interface ContributionTypeOption {
  value: string;
  label: string;
  description?: string;
}

/** PaRadioGroup's structural option shape (value / label / optional disabled). */
type RadioGroupOption = { value: string; label: string; disabled?: boolean };

const DEFAULT_OPTIONS: ContributionTypeOption[] = [
  {
    value: "observed_presence",
    label: "现场观察",
    description: "你亲眼看到的现场情况",
  },
  {
    value: "staff_response",
    label: "工作人员响应",
    description: "与管理方/员工的当面或线上沟通记录",
  },
  {
    value: "animal_facility",
    label: "设施信息",
    description: "场所内的动物相关设施（如饮水点、暂存区）",
  },
];

const props = withDefaults(
  defineProps<{
    modelValue: string;
    options?: ContributionTypeOption[];
    disabled?: boolean;
  }>(),
  { options: () => DEFAULT_OPTIONS, disabled: false },
);

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

defineOptions({ name: "ContributionTypeSelector" });

const HINT = "请选择要贡献的事实类型";

const groupOptions = computed<RadioGroupOption[]>(() =>
  props.options.map((option) => ({ value: option.value, label: option.label })),
);

const selected = computed(() => props.options.find((option) => option.value === props.modelValue));
</script>

<template>
  <div class="contribution-type-selector">
    <p class="contribution-type-selector__hint">{{ HINT }}</p>
    <PaRadioGroup
      :model-value="modelValue"
      :options="groupOptions"
      :aria-label="HINT"
      :disabled="disabled"
      @update:model-value="emit('update:modelValue', $event)"
    />
    <p v-if="selected?.description" class="contribution-type-selector__description">
      {{ selected.description }}
    </p>
  </div>
</template>

<style scoped>
.contribution-type-selector {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.contribution-type-selector__hint {
  margin: 0;
  font-size: var(--pa-font-size-base);
  color: var(--pa-color-text-primary);
}

.contribution-type-selector__description {
  margin: 0;
  font-size: var(--pa-font-size-md);
  color: var(--pa-color-text-muted);
}
</style>
