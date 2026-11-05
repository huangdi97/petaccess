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
    <div v-if="!watches.length" class="mine-empty-state">
      <div>
        <strong>还没有关注变化</strong>
        <p>先从地图或场所详情找到真正关心的地点，再选择关注规则变化或现场更新。</p>
      </div>
      <RouterLink class="btn-inline" to="/map">去地图看看 →</RouterLink>
    </div>
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

    <div v-if="!contributions.length" class="mine-empty-state" data-testid="contributions-empty">
      <div>
        <strong>{{ EMPTY_STATE_COPY.CONTRIBUTION_HISTORY.title }}</strong>
        <p>{{ EMPTY_STATE_COPY.CONTRIBUTION_HISTORY.description }}</p>
      </div>
      <RouterLink class="btn-inline" to="/contribute">去补充事实 →</RouterLink>
    </div>
  </section>
</template>

<style scoped src="./MineActivitySections.css"></style>
