<script setup lang="ts">
import { useRouter } from "vue-router";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";

const router = useRouter();
</script>

<template>
  <AppShell>
    <h1 class="visually-hidden">页面不存在</h1>
    <StateMessage
      kind="EMPTY"
      title="页面不存在"
      description="你访问的页面不存在或已被移动。返回首页继续查找场所。"
      data-testid="not-found"
    >
      <template #action>
        <button class="primary" @click="router.push('/')">返回首页</button>
      </template>
    </StateMessage>
  </AppShell>
</template>
