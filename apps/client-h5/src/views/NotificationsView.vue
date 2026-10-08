<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { client, session, type WatchView } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

const router = useRouter();
const watches = ref<WatchView[]>([]);
const targetNames = ref<Record<string, string>>({});
const loading = ref(true);
const error = ref("");
const actionError = ref("");
const unsubscribing = ref<string | null>(null);
const signedIn = ref(false);

const TARGET_LABELS: Record<string, string> = {
  place: "场所",
  zone: "区域",
  rule: "具体规则",
};

const activeRuleCount = computed(
  () => watches.value.filter((watch) => watch.watch_domain === "rule").length,
);
const activeRealityCount = computed(
  () => watches.value.filter((watch) => watch.watch_domain === "reality").length,
);

function domainLabel(watch: WatchView): string {
  return watch.watch_domain === "reality" ? "现场更新" : "规则变化";
}

function targetLabel(watch: WatchView): string {
  return targetNames.value[watch.target_id] ?? TARGET_LABELS[watch.target_type] ?? "关注对象";
}

async function load() {
  loading.value = true;
  error.value = "";
  actionError.value = "";
  try {
    await session.restore();
    signedIn.value = session.signedIn;
    watches.value = signedIn.value ? await client.myWatches() : [];
    const placeIds = [
      ...new Set(
        watches.value
          .filter((watch) => watch.target_type === "place")
          .map((watch) => watch.target_id),
      ),
    ];
    const names = await Promise.all(
      placeIds.map(async (id) => {
        const place = await client.place(id).catch(() => null);
        return [id, place?.canonical_name ?? "场所名称待补充"] as const;
      }),
    );
    targetNames.value = Object.fromEntries(names);
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

async function unsubscribe(w: WatchView) {
  if (unsubscribing.value) return;
  unsubscribing.value = w.id;
  actionError.value = "";
  try {
    await client.unwatch(w.id);
    // Only remove after a server-confirmed response; a failed call retains
    // the existing subscription and its control for a retry.
    watches.value = watches.value.filter((x) => x.id !== w.id);
  } catch (e) {
    actionError.value = presentDescription(e);
  } finally {
    unsubscribing.value = null;
  }
}
</script>

<template>
  <AppShell>
    <header class="notifications-head">
      <h1>通知中心</h1>
      <p class="muted">
        这里管理你主动关注的变化。规则版本变化与经核验现场更新是两条独立订阅，不会相互替代。
      </p>
    </header>

    <section class="notifications-channel" aria-label="关注类型">
      <div class="notifications-channel__lead">
        <h2>关注类型</h2>
        <p class="muted">规则变化与现场更新是两条独立订阅；一个变化不会替代另一个。</p>
      </div>
      <div class="notifications-channel__body">
        <div class="channel-row">
          <div>
            <strong>规则变化</strong>
            <p class="muted">只跟踪经过人工核验并发布的正式规则版本。</p>
          </div>
          <span v-if="signedIn" class="channel-row__count">{{ activeRuleCount }} 项</span>
        </div>
        <div class="channel-row">
          <div>
            <strong>现场更新</strong>
            <p class="muted">跟踪新发布且经核验的动物出现、工作人员处理与设施事实。</p>
          </div>
          <span v-if="signedIn" class="channel-row__count">{{ activeRealityCount }} 项</span>
        </div>
        <p class="notifications-channel__delivery muted">
          当前版本尚未接入系统推送；这里是应用内关注列表，不代表外部提醒已经发送。
        </p>
      </div>
    </section>

    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" :description="error">
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="!signedIn"
      kind="PERMISSION_DENIED"
      description="登录后可查看和管理你的规则变化与现场更新关注。"
    >
      <template #action>
        <button
          class="primary"
          @click="router.push({ name: 'onboarding', query: { next: '/notifications' } })"
        >
          去登录
        </button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="!watches.length"
      kind="EMPTY"
      description="还没有关注任何规则变化或现场更新。"
    >
      <template #action>
        <button class="primary" @click="router.push({ name: 'home' })">查找场所</button>
      </template>
    </StateMessage>

    <section v-else class="notifications-list" aria-label="已关注的变化">
      <p v-if="actionError" class="notifications-action-error" role="alert">
        取消关注失败，原有订阅仍保留：{{ actionError }}
      </p>
      <div v-for="w in watches" :key="w.id" class="notification-row">
        <div class="notification-row__body">
          <strong>{{ targetLabel(w) }}</strong>
          <span>{{ domainLabel(w) }}</span>
          <span class="muted">
            {{ w.watch_domain === "reality" ? "等待新的经核验现场事实" : "等待新的正式规则版本" }}
          </span>
        </div>
        <button
          class="notification-row__action"
          type="button"
          :disabled="Boolean(unsubscribing)"
          :aria-label="`取消关注 ${targetLabel(w)}的${domainLabel(w)}`"
          @click="unsubscribe(w)"
        >
          {{ unsubscribing === w.id ? "取消中…" : "取消关注" }}
        </button>
      </div>
    </section>
  </AppShell>
</template>

<style scoped src="./NotificationsView.css"></style>
