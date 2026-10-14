<script setup lang="ts">
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import NotificationsSummary from "../components/notifications/NotificationsSummary.vue";
import { useNotificationsCenter } from "../composables/useNotificationsCenter";

const {
  watches,
  events,
  loading,
  error,
  actionError,
  unsubscribing,
  signedIn,
  activeRuleCount,
  activeRealityCount,
  domainLabel,
  targetLabel,
  eventPlaceLabel,
  eventTypeLabel,
  eventDetail,
  eventTime,
  openEvent,
  load,
  unsubscribe,
  goLogin,
  goHome,
} = useNotificationsCenter();
</script>

<template>
  <AppShell :show-query-context="false"
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

      <NotificationsSummary
        v-if="signedIn && !loading && !error"
        :rule-count="activeRuleCount"
        :reality-count="activeRealityCount"
        :total-count="watches.length"
      />
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
        <button class="primary" @click="goLogin">去登录</button>
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
            <button class="primary" @click="goHome">查找场所</button>
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
                  w.watch_domain === "reality" ? "等待新的经核验现场事实" : "等待新的正式规则版本"
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
