<script setup lang="ts">
/**
 * PlaceUnknownPane — Unknown Overview（v0.2.5 §15）。
 *
 * Unknown Overview 只允许：Identity（PlaceView header 担任）/ Tabs（PlaceSectionNav 担任）/
 * Current Query / Information Insufficient / Known Facts / Contribute Actions。
 * Space/Evidence 有真数据才显示 summary row；没有就不显示空 summary（§27 收口）。
 * Consumer copy 自然语言：不再出现「未知 ≠ 允许」这类工程不变量。
 */
import { computed } from "vue";

const props = defineProps<{
  placeId: string;
  hasRules: boolean;
  hasObservations: boolean;
  zoneCount: number;
  hasSources: boolean;
}>();

interface FactRow {
  label: string;
  value: string;
}
const knownFacts = computed<FactRow[]>(() => {
  const rows: FactRow[] = [];
  if (!props.hasRules) rows.push({ label: "规则", value: "暂无正式规则" });
  if (!props.hasObservations) rows.push({ label: "现场记录", value: "暂无足够现场记录" });
  if (props.zoneCount > 0) rows.push({ label: "空间", value: `${props.zoneCount} 个已收录区域` });
  if (props.hasSources) rows.push({ label: "来源", value: "已有来源信息" });
  return rows;
});
</script>

<template>
  <section class="place-unknown" data-testid="place-unknown" data-ui="place-unknown">
    <h2 class="place-unknown__title">当前查询</h2>
    <p class="place-unknown__headline">信息不足</p>
    <p class="place-unknown__body">目前没有足够可靠信息，无法确认是否允许进入。</p>
    <p class="muted place-unknown__note">不要把“信息不足”理解为允许。</p>

    <template v-if="knownFacts.length">
      <h3 class="place-unknown__subtitle">已有信息</h3>
      <ul class="place-unknown__facts">
        <li v-for="f in knownFacts" :key="f.label" class="place-unknown__fact">
          <span class="place-unknown__fact-label">{{ f.label }}</span>
          <span class="muted">{{ f.value }}</span>
        </li>
      </ul>
    </template>

    <div class="place-unknown__actions">
      <RouterLink
        class="btn primary"
        :to="`/contribute/${placeId}`"
        data-testid="place-unknown-contribute"
      >
        提交规则线索
      </RouterLink>
      <RouterLink class="btn" :to="`/place/${placeId}/reality`" data-testid="place-unknown-reality">
        记录现场情况
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.place-unknown {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  padding-top: var(--pa-space-2);
}
.place-unknown__title {
  margin: 0;
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}
.place-unknown__headline {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-decision);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-decision);
  color: var(--pa-color-text-primary);
}
.place-unknown__body {
  margin: var(--pa-space-2) 0 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
  color: var(--pa-color-text-primary);
}
.place-unknown__note {
  margin: 0;
}
.place-unknown__subtitle {
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
.place-unknown__facts {
  list-style: none;
  margin: var(--pa-space-1) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}
.place-unknown__fact {
  display: flex;
  gap: var(--pa-space-2);
  font-size: var(--pa-font-size-base);
}
.place-unknown__fact-label {
  flex: 0 0 4.5rem;
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}
.place-unknown__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
}
</style>
