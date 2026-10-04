<script setup lang="ts">
import { client } from "@petaccess/client-core";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import { CANDIDATE_TYPE_LABELS, contributionStatusLabel } from "../../reality";

type Watch = Awaited<ReturnType<typeof client.myWatches>>[number];
type Contribution = Awaited<ReturnType<typeof client.myRealityContributions>>[number];

defineProps<{ watches: Watch[]; contributions: Contribution[] }>();

const WATCH_LABELS: Record<string, string> = {
  place: "场所规则变化",
  zone: "区域规则变化",
  rule: "规则变化",
  regulation: "法规变化",
};
</script>

<template>
  <section class="mine-section">
    <div class="mine-section__head">
      <div>
        <h2>关注的规则变化</h2>
        <p class="muted">只显示你主动关注的变化，不把它们解释成新的准入结论。</p>
      </div>
      <RouterLink class="btn-inline" to="/notifications" data-testid="open-notifications">
        通知中心 →
      </RouterLink>
    </div>

    <div v-for="watch in watches" :key="watch.id" class="mine-row">
      <div class="mine-row__body">
        <strong>{{ WATCH_LABELS[watch.target_type] ?? "已关注的规则变化" }}</strong>
        <span class="muted">等待后续规则版本更新</span>
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
      :key="item.report_id"
      class="mine-contribution"
      data-testid="contribution-row"
    >
      <time class="mine-contribution__date">
        {{ new Date(item.created_at ?? 0).toLocaleDateString("zh-CN") }}
      </time>
      <div class="mine-contribution__facts">
        <span
          v-for="candidate in item.candidates"
          :key="candidate.candidate_type + (candidate.observed_at ?? '')"
        >
          {{ CANDIDATE_TYPE_LABELS[candidate.candidate_type] ?? "现场信息" }}
          · {{ contributionStatusLabel(candidate) }}
        </span>
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
