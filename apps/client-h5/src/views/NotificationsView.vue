<script setup lang="ts">
/**
 * Notification center (P1).
 *
 * There is no push channel yet (the notification provider is a mock), so this
 * screen shows the *subscriptions* that will drive notifications plus the
 * honest status of the delivery channel. It never claims a message was sent.
 */
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { client, session, type WatchView } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";

const router = useRouter();
const watches = ref<WatchView[]>([]);
const loading = ref(true);
const error = ref("");
const signedIn = ref(false);

const TARGET_LABELS: Record<string, string> = {
  place: "场所",
  zone: "区域",
  rule: "规则",
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
    error.value = e instanceof Error ? e.message : String(e);
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
    error.value = e instanceof Error ? e.message : String(e);
  }
}
</script>

<template>
  <AppShell>
    <h1>通知中心</h1>

    <div class="panel">
      <div class="muted">
        规则变化提醒：当关注的场所/区域规则更新（新版本、supersession、回滚）时通知你。
      </div>
      <StateMessage
        kind="PARTIAL"
        description="当前版本通知通道为 Mock（尚未接入真实推送通道）。这里展示的是订阅列表，不代表已发送过消息。"
      />
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
      description="登录后可查看你的规则变化订阅。"
    >
      <template #action>
        <button class="primary" @click="router.push({ name: 'mine' })">去登录</button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="!watches.length"
      kind="EMPTY"
      description="还没有订阅任何场所的规则变化。"
    >
      <template #action>
        <button class="primary" @click="router.push({ name: 'home' })">去地图关注场所</button>
      </template>
    </StateMessage>
    <template v-else>
      <div v-for="w in watches" :key="w.id" class="panel">
        <div class="row" style="justify-content: space-between">
          <span>
            <span class="tag">{{ TARGET_LABELS[w.target_type] ?? w.target_type }}</span>
            <span class="muted">{{ w.target_id.slice(0, 8) }}</span>
          </span>
          <button @click="unsubscribe(w)">取消订阅</button>
        </div>
        <div class="muted">
          通道：{{ w.channels?.join("、") || "默认" }} · 状态：{{ w.status ?? "active" }}
        </div>
      </div>
    </template>
  </AppShell>
</template>
