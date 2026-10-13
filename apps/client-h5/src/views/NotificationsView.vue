<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  client,
  session,
  type WatchEventView,
  type WatchView,
} from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

const router = useRouter();
const watches = ref<WatchView[]>([]);
const events = ref<WatchEventView[]>([]);
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

function eventPlaceLabel(event: WatchEventView): string {
  return event.place_id ? (targetNames.value[event.place_id] ?? "场所变化") : "规则变化";
}

function eventTypeLabel(event: WatchEventView): string {
  switch (event.event_type) {
    case "rule_version_published":
      return "正式规则已更新";
    case "rule_exception_published":
      return "规则适用边界已更新";
    case "reality_observed_presence_published":
      return "新增经核验的动物出现记录";
    case "reality_staff_response_published":
      return "新增经核验的工作人员处理记录";
    case "reality_animal_facility_published":
      return "动物设施事实已更新";
  }
}

function eventDetail(event: WatchEventView): string {
  if (event.watch_domain === "reality") {
    return "这是一条经人工核验后发布的现场事实，不代表正式准入规则发生变化。";
  }
  return "这是一条经过审核并发布的规则变化；可进入详情查看适用对象、区域与来源。";
}

function eventTime(event: WatchEventView): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(event.occurred_at));
}

async function openEvent(event: WatchEventView) {
  if (!event.read_at) {
    void client
      .markWatchEventRead(event.id)
      .then((updated) => {
        const index = events.value.findIndex((item) => item.id === updated.id);
        if (index >= 0) events.value[index] = updated;
      })
      .catch(() => {
        // Reading the published fact must never be blocked by a read-receipt failure.
      });
  }
  if (!event.place_id) return;
  if (event.watch_domain === "reality") {
    await router.push({ name: "reality-trace", params: { id: event.place_id } });
    return;
  }
  await router.push({
    name: "place",
    params: { id: event.place_id },
    query: { view: "rules" },
  });
}

async function load() {
  loading.value = true;
  error.value = "";
  actionError.value = "";
  // Private account data is a fresh transaction. Never keep previous counts
  // or venue names visible while the current account refresh is unresolved.
  watches.value = [];
  events.value = [];
  targetNames.value = {};
  try {
    await session.restore();
    signedIn.value = session.signedIn;
    if (signedIn.value) {
      const [nextWatches, nextEvents] = await Promise.all([
        client.myWatches(),
        client.myWatchEvents(),
      ]);
      watches.value = nextWatches;
      events.value = nextEvents;
    }
    const placeIds = [
      ...new Set([
        ...watches.value
          .filter((watch) => watch.target_type === "place")
          .map((watch) => watch.target_id),
        ...events.value
          .map((event) => event.place_id)
          .filter((id): id is string => Boolean(id)),
      ]),
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
  <AppShell
    data-testid="notifications-page"
    data-ui-page="notifications"
    :data-ui-state="
      loading ? 'loading' : error ? 'error' : signedIn ? 'ready' : 'permission-denied'
    "
  >
    <header class="notifications-head">
      <p class="notifications-head__kicker">我的关注</p>
      <h1>通知中心</h1>
      <p class="muted">
        只显示你主动关注的变化。规则版本变化与经核验现场更新始终分开，不会互相替代。
      </p>

      <div
        v-if="signedIn && !loading && !error"
        class="notifications-summary"
        aria-label="关注摘要"
      >
        <div>
          <span>规则变化</span>
          <strong>{{ activeRuleCount }}</strong>
        </div>
        <div>
          <span>现场更新</span>
          <strong>{{ activeRealityCount }}</strong>
        </div>
        <div>
          <span>总关注</span>
          <strong>{{ watches.length }}</strong>
        </div>
      </div>
    </header>

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
    <template v-else>
      <section class="watch-events" aria-label="最近变化">
        <div class="notifications-list__head">
          <div>
            <p class="notifications-list__kicker">最近变化</p>
            <h2>经核验后发布的更新</h2>
          </div>
          <span>{{ events.length }} 条</span>
        </div>

        <StateMessage
          v-if="!events.length"
          kind="EMPTY"
          title="暂无新的经核验变化"
          description="关注已经生效；只有正式规则版本或经人工核验的现场事实发布后，才会出现在这里。"
        />

        <div v-else class="watch-events__list">
          <button
            v-for="event in events"
            :key="event.id"
            type="button"
            class="watch-event"
            :class="{ 'watch-event--unread': !event.read_at }"
            :disabled="!event.place_id"
            @click="openEvent(event)"
          >
            <span class="watch-event__dot" :data-domain="event.watch_domain" aria-hidden="true" />
            <span class="watch-event__body">
              <span class="watch-event__meta">
                <strong>{{ eventPlaceLabel(event) }}</strong>
                <time :datetime="event.occurred_at">{{ eventTime(event) }}</time>
              </span>
              <span class="watch-event__title">{{ eventTypeLabel(event) }}</span>
              <span class="muted watch-event__detail">{{ eventDetail(event) }}</span>
            </span>
            <span v-if="event.place_id" class="watch-event__arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </section>

      <section class="notifications-list" aria-label="已关注的变化">
        <div class="notifications-list__head">
          <div>
            <p class="notifications-list__kicker">正在关注</p>
            <h2>你的变化订阅</h2>
          </div>
          <span>{{ watches.length }} 项</span>
        </div>

        <p v-if="actionError" class="notifications-action-error" role="alert">
          取消关注失败，原有订阅仍保留：{{ actionError }}
        </p>

        <StateMessage
          v-if="!watches.length"
          kind="EMPTY"
          description="还没有关注任何规则变化或现场更新。"
        >
          <template #action>
            <button class="primary" @click="router.push({ name: 'home' })">查找场所</button>
          </template>
        </StateMessage>

        <div v-else>
          <div v-for="w in watches" :key="w.id" class="notification-row">
            <div
              class="notification-row__marker"
              :data-domain="w.watch_domain"
              aria-hidden="true"
            />
            <div class="notification-row__body">
              <strong>{{ targetLabel(w) }}</strong>
              <span>{{ domainLabel(w) }}</span>
              <span class="muted">
                {{
                  w.watch_domain === "reality"
                    ? "等待新的经核验现场事实"
                    : "等待新的正式规则版本"
                }}
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
        </div>
      </section>
    </template>

    <section class="notifications-channel" aria-label="关注如何工作">
      <div class="notifications-channel__lead">
        <p class="notifications-list__kicker">工作方式</p>
        <h2>关注如何工作</h2>
        <p class="muted">只对已经发布且可追溯的变化产生应用内记录。</p>
      </div>
      <div class="notifications-channel__body">
        <div class="channel-row">
          <div>
            <strong>规则变化</strong>
            <p class="muted">只跟踪经过人工核验并发布的正式规则版本。</p>
          </div>
          <span class="channel-row__badge">Rule</span>
        </div>
        <div class="channel-row">
          <div>
            <strong>现场更新</strong>
            <p class="muted">跟踪新发布且经核验的动物出现、工作人员处理与设施事实。</p>
          </div>
          <span class="channel-row__badge">Reality</span>
        </div>
        <p class="notifications-channel__delivery muted">
          当前版本尚未接入系统推送；这里是应用内关注列表，不代表外部提醒已经发送。
        </p>
      </div>
    </section>
  </AppShell>
</template>

<style scoped src="./NotificationsView.css"></style>
