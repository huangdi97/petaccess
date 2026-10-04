<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { client, session, type WatchView } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

const router = useRouter();
const watches = ref<WatchView[]>([]);
const loading = ref(true);
const error = ref("");
const signedIn = ref(false);

const TARGET_LABELS: Record<string, string> = {
  place: "场所规则",
  zone: "区域规则",
  rule: "具体规则",
  regulation: "法规",
};

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await session.restore();
    signedIn.value = session.signedIn;
    watches.value = signedIn.value ? await client.myWatches() : [];
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function unsubscribe(w: WatchView) {
  try {
    await client.unwatch(w.id);
    watches.value = watches.value.filter((x) => x.id !== w.id);
  } catch (e) {
    error.value = presentDescription(e);
  }
}
</script>

<template>
  <AppShell>
    <header class="notifications-head">
      <h1>通知中心</h1>
      <p class="muted">
        关注规则变化后，这里会列出你的订阅。规则出现新版本、被替代或恢复旧版本时，才有可能产生提醒。
      </p>
    </header>

    <div class="notifications-channel">
      <strong>提醒通道</strong>
      <p class="muted">当前版本尚未接入系统推送；这里展示关注列表，不代表任何提醒已经发送。</p>
    </div>

    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" :description="error">
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="!signedIn"
      kind="PERMISSION_DENIED"
      description="登录后可查看和管理你的规则变化关注。"
    >
      <template #action>
        <button class="primary" @click="router.push({ name: 'mine' })">去登录</button>
      </template>
    </StateMessage>
    <StateMessage v-else-if="!watches.length" kind="EMPTY" description="还没有关注任何规则变化。">
      <template #action>
        <button class="primary" @click="router.push({ name: 'home' })">查找场所</button>
      </template>
    </StateMessage>

    <section v-else class="notifications-list" aria-label="已关注的规则变化">
      <div v-for="w in watches" :key="w.id" class="notification-row">
        <div class="notification-row__body">
          <strong>{{ TARGET_LABELS[w.target_type] ?? "规则变化" }}</strong>
          <span class="muted">已关注 · 等待后续变化</span>
        </div>
        <button class="notification-row__action" type="button" @click="unsubscribe(w)">
          取消关注
        </button>
      </div>
    </section>
  </AppShell>
</template>

<style scoped>
.notifications-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.notifications-head p,
.notifications-channel p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.notifications-channel {
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.notifications-list {
  margin-top: var(--pa-space-3);
}

.notification-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-4);
  min-height: 64px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.notification-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.notification-row__action {
  flex: 0 0 auto;
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  cursor: pointer;
}

.notification-row__action:hover,
.notification-row__action:focus-visible {
  text-decoration: underline;
  text-underline-offset: 3px;
}

@media (max-width: 767px) {
  .notification-row {
    align-items: flex-start;
  }
}
</style>
