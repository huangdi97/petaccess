<script setup lang="ts">
/** ContributeDone — M7 submission result screen (结构化确认，无自由文本). */
import StateMessage from "../StateMessage.vue";

defineOptions({ name: "ContributeDone" });

defineProps<{ msg: string; placeId: string }>();
defineEmits<{ continue: [] }>();
</script>

<template>
  <StateMessage kind="PARTIAL" :description="msg" data-testid="contribute-result">
    <template #action>
      <div class="row">
        <button class="primary" @click="$emit('continue')">继续贡献</button>
        <RouterLink :to="{ name: 'place', params: { id: placeId } }">
          <button>返回场所</button>
        </RouterLink>
      </div>
    </template>
  </StateMessage>
</template>
