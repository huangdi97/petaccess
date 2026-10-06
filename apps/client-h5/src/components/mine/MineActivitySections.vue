<script setup lang="ts">
import { client } from "@petaccess/client-core";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";

type Watch = Awaited<ReturnType<typeof client.myWatches>>[number];
type Contribution = Awaited<ReturnType<typeof client.myContributionActivity>>[number];

defineProps<{ watches: Watch[]; contributions: Contribution[] }>();

const WATCH_TARGET_LABELS: Record<string, string> = {
  place: "场所",
  zone: "区域",
  rule: "具体规则",
  regulation: "法规",
};

function watchLabel(watch: Watch): string {
  const target = WATCH_TARGET_LABELS[watch.target_type] ?? "关注对象";
  return watch.watch_domain === "reality" ? `${target} · 现场更新` : `${target} · 规则变化`;
}

function watchHint(watch: Watch): string {
  return watch.watch_domain === "reality"
    ? "等待新的经核验现场事实、工作人员处理或设施变化"
    : "等待经过 Review 的正式规则版本变化";
}
</script>

<template>
  <section class="mine-section">
    <div class="mine-section__head">
      <div>
        <h2>关注的变化</h2>
        <p class="muted">规则变化与现场更新分开关注；任何提醒都不会被自动解释成新的准入结论。</p>
      </div>
      <RouterLink class="btn-inline" to="/notifications" data-testid="open-notifications">
        通知中心 →
      </RouterLink>
    </div>

    <div v-for="watch in watches" :key="watch.id" class="mine-row">
      <div class="mine-row__body">
        <strong>{{ watchLabel(watch) }}</strong>
        <span class="muted">{{ watchHint(watch) }}</span>
      </div>
    </div>
    <p v-if="!watches.length" class="mine-empty">暂无关注。</p>
  </section>

  <section class="mine-section">
    <div class="mine-section__head">
      <div>
        <h2>我的贡献</h2>
        <p class="muted">提交内容与正式规则分开保存，只有经过核验后才进入相应记录。</p>
      </div>
    </div>

    <div
      v-for="item in contributions"
      :key="item.kind + item.id"
      class="mine-contribution"
      data-testid="contribution-row"
    >
      <time class="mine-contribution__date">
        {{ new Date(item.created_at ?? 0).toLocaleDateString("zh-CN") }}
      </time>
      <div class="mine-contribution__facts">
        <strong>{{ item.summary }}</strong>
        <span v-if="item.place_name" class="muted">{{ item.place_name }}</span>
        <span>{{ item.status }}</span>
      </div>
    </div>

    <p v-if="!contributions.length" class="mine-empty" data-testid="contributions-empty">
      {{ EMPTY_STATE_COPY.CONTRIBUTION_HISTORY.title }} —
      {{ EMPTY_STATE_COPY.CONTRIBUTION_HISTORY.description }}
    </p>
  </section>
</template>

<style scoped>
.mine-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-section__head,
.mine-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
}

.mine-section__head {
  margin-bottom: var(--pa-space-3);
}

.mine-section h2 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.mine-section__head p {
  margin: var(--pa-space-1) 0 0;
}

.mine-row {
  min-height: 56px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.mine-empty {
  margin: 0;
  color: var(--pa-color-text-secondary);
}

.mine-contribution {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-contribution__date {
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-md);
}

.mine-contribution__facts {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

@media (max-width: 767px) {
  .mine-section__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .mine-contribution {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }
}
</style>
