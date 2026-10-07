<script setup lang="ts">
// @ui-static SettingsView — 设置入口页，无列表数据加载。
import { onMounted, ref } from "vue";
import { session } from "@petaccess/client-core";
import { REQUIRED_COPY } from "@petaccess/design-tokens";
import AppShell from "../components/AppShell.vue";
import { querySummaryLabel } from "../consumer/queryContext";

const appVersion = import.meta.env.VITE_APP_VERSION ?? "0.2.0-dev";
const signedIn = ref(false);

onMounted(async () => {
  await session.restore();
  signedIn.value = session.signedIn;
});

const RULE_LAYERS = [
  {
    label: "法定要求",
    note: "法律法规直接规定，具有强制效力；下层管理方规则不能削弱它。",
  },
  {
    label: "监管指引",
    note: "主管部门发布的指引性文件，用来说明适用边界与执行方式。",
  },
  { label: "管理方规则", note: "场所或物业自行制定并公开的通行与使用规则。" },
  { label: "临时措施", note: "有明确起止时间的临时性安排，过期后不继续作为当前规则。" },
];

const EVIDENCE = [
  { label: "官方来源", note: "政府或场所官方渠道公开发布。" },
  { label: "现场核验", note: "有人到场核对并留下可追溯记录。" },
  { label: "现场标识", note: "来自规则牌、公告等现场材料，需要保留来源与时间。" },
  {
    label: "用户线索",
    note: "用户提交先进入待核验队列；通过人工核验后，才进入相应的规则候选或现场事实层。",
  },
];
</script>

<template>
  <AppShell>
    <header class="settings-head">
      <h1>设置与说明</h1>
      <p class="muted">
        PetAccess 只整理规则、现场事实和证据，不给场所打“友好分”，也不把信息不足解释成允许或禁止。
      </p>
    </header>

    <section class="settings-section" data-testid="methodology">
      <h2>规则如何组织</h2>
      <p class="muted settings-section__intro">
        同一场所可能同时存在多个层级的规则。当前查询只展示真正适用于对象、动作与区域的结论。
      </p>
      <div v-for="l in RULE_LAYERS" :key="l.label" class="settings-row">
        <strong>{{ l.label }}</strong>
        <span class="muted">{{ l.note }}</span>
      </div>
    </section>

    <section class="settings-section" data-testid="evidence-strength">
      <h2>证据如何呈现</h2>
      <p class="muted settings-section__intro">
        来源强弱描述的是证据本身；它不会把一次现场观察自动变成正式准入规则。
      </p>
      <div v-for="e in EVIDENCE" :key="e.label" class="settings-row">
        <strong>{{ e.label }}</strong>
        <span class="muted">{{ e.note }}</span>
      </div>
    </section>

    <section class="settings-section" data-testid="limits">
      <h2>产品边界</h2>
      <div class="settings-points">
        <p>{{ REQUIRED_COPY.noRankingDisclaimer }}</p>
        <p>不预测现场一定会不会遇到动物。</p>
        <p>自动解析只能生成待审候选，不会直接改变正式规则结论。</p>
        <p>{{ REQUIRED_COPY.unknownShort }}表示当前依据不足，需要继续查看来源或补充信息。</p>
        <p>不记录小区住户信息；位置只用于当前附近查询或现场核验。</p>
      </div>
    </section>

    <section class="settings-section">
      <h2>相关设置</h2>
      <nav class="settings-links" aria-label="相关设置">
        <RouterLink class="btn-inline" to="/boundary">共处边界 →</RouterLink>
        <RouterLink class="btn-inline" to="/privacy">隐私与数据 →</RouterLink>
        <RouterLink class="btn-inline" to="/notifications">通知 →</RouterLink>
        <RouterLink v-if="signedIn" class="btn-inline" to="/pets">宠物档案 →</RouterLink>
      </nav>
    </section>

    <section class="settings-section" data-testid="about-section">
      <h2>关于 PetAccess</h2>
      <p class="settings-about">
        城市公共空间动物通行规则与现场事实查询工具。去之前，先看规则与现场。
      </p>
      <p class="muted">当前版本 v{{ appVersion }} · 上海试点 · 开发预览阶段</p>
    </section>

    <footer class="settings-foot">
      <span>当前查询：{{ querySummaryLabel() }}</span>
      <span>
        {{ signedIn ? `已登录 · ${session.user?.display_name ?? ""}` : "未登录 · 可浏览公开内容" }}
      </span>
    </footer>
  </AppShell>
</template>

<style scoped>
.settings-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.settings-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.settings-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.settings-section h2 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.settings-section__intro {
  margin: var(--pa-space-2) 0 var(--pa-space-3);
  max-width: 680px;
}

.settings-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.settings-row:last-child {
  border-bottom: none;
}

.settings-row strong {
  font-size: var(--pa-font-size-base);
}

.settings-points {
  margin-top: var(--pa-space-3);
}

.settings-points p {
  margin: 0;
  padding: var(--pa-space-2) 0;
  color: var(--pa-color-text-secondary);
}

.settings-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-4);
  margin-top: var(--pa-space-3);
}

.settings-about {
  margin: var(--pa-space-2) 0;
  max-width: 620px;
  line-height: var(--pa-line-height-23);
}

.settings-foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding-top: var(--pa-space-5);
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
}

@media (max-width: 767px) {
  .settings-row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }

  .settings-links {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--pa-space-2);
  }
}
</style>
