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

<style scoped src="./BoundaryPreferenceList.css"></style>
