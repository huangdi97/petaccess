<script setup lang="ts">
import { MODE_LABELS, type QueryMode } from "@petaccess/client-core";

defineProps<{ mode: QueryMode }>();
defineEmits<{ change: [m: QueryMode] }>();

const modes: QueryMode[] = ["with_pet", "restrictions", "service_dog", "rules_only"];
</script>

<template>
  <div class="row" style="margin-bottom: 12px">
    <button v-for="m in modes" :key="m" class="pill" :class="{ active: mode === m }"
            :data-mode="m" @click="$emit('change', m)">
      {{ MODE_LABELS[m] }}
    </button>
  </div>
</template>
