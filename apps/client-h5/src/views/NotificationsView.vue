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
      <strong>关注类型</strong>
      <p class="muted">
        规则变化只跟踪经过 Review 的正式规则版本；现场更新只跟踪新发布的经核验 Reality
        事实、工作人员处理与设施变化。两类关注互不替代。
      </p>
      <p v-if="signedIn" class="muted notifications-channel__counts">
        当前：规则变化 {{ activeRuleCount }} · 现场更新 {{ activeRealityCount }}
      </p>
      <p class="muted">
        当前版本尚未接入系统推送；这里展示应用内关注列表，不代表任何外部提醒已经发送。
      </p>
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
          <strong>{{ targetLabel(w) }}</strong>
          <span>{{ domainLabel(w) }}</span>
          <span class="muted">
            {{ w.watch_domain === "reality" ? "等待新的经核验现场事实" : "等待新的正式规则版本" }}
          </span>
        </div>
        <button class="notification-row__action" type="button" @click="unsubscribe(w)">
          取消关注
        </button>
      </div>
    </section>
  </AppShell>
</template>

<style scoped src="./NotificationsView.css"></style>
