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
      <p class="settings-head__kicker">方法与偏好</p>
      <h1>设置与说明</h1>
      <p class="muted">
        PetAccess 只整理规则、现场事实和证据，不给场所打“友好分”，也不把信息不足解释成允许或禁止。
      </p>
    </header>

    <section class="settings-section" data-testid="methodology">
      <div class="settings-section__lead">
        <h2>规则如何组织</h2>
        <p class="muted">
          同一场所可能同时存在多个层级的规则。当前查询只展示真正适用于对象、动作与区域的结论。
        </p>
      </div>
      <div class="settings-section__body">
        <div v-for="layer in RULE_LAYERS" :key="layer.label" class="settings-row">
          <strong>{{ layer.label }}</strong>
          <span class="muted">{{ layer.note }}</span>
        </div>
      </div>
    </section>

    <section class="settings-section" data-testid="evidence-strength">
      <div class="settings-section__lead">
        <h2>证据如何呈现</h2>
        <p class="muted">来源强弱描述的是证据本身；它不会把一次现场观察自动变成正式准入规则。</p>
      </div>
      <div class="settings-section__body">
        <div v-for="evidence in EVIDENCE" :key="evidence.label" class="settings-row">
          <strong>{{ evidence.label }}</strong>
          <span class="muted">{{ evidence.note }}</span>
        </div>
      </div>
    </section>

    <section class="settings-section" data-testid="limits">
      <div class="settings-section__lead">
        <h2>产品边界</h2>
        <p class="muted">这些限制是产品的一部分，不会因为信息变多而取消。</p>
      </div>
      <div class="settings-section__body settings-points">
        <p>{{ REQUIRED_COPY.noRankingDisclaimer }}</p>
        <p>不预测现场一定会不会遇到动物。</p>
        <p>自动解析只能生成待审候选，不会直接改变正式规则结论。</p>
        <p>{{ REQUIRED_COPY.unknownShort }}表示当前依据不足，需要继续查看来源或补充信息。</p>
        <p>不记录小区住户信息；位置只用于当前附近查询或现场核验。</p>
      </div>
    </section>

    <section class="settings-section">
      <div class="settings-section__lead">
        <h2>相关设置</h2>
        <p class="muted">管理个人偏好、隐私、关注与查询对象。</p>
      </div>
      <nav class="settings-section__body settings-links" aria-label="相关设置">
        <RouterLink class="settings-link" to="/boundary">
          <span>共处边界</span><span aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink class="settings-link" to="/privacy">
          <span>隐私与数据</span><span aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink class="settings-link" to="/notifications">
          <span>通知</span><span aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink v-if="signedIn" class="settings-link" to="/pets">
          <span>宠物档案</span><span aria-hidden="true">→</span>
        </RouterLink>
      </nav>
    </section>

    <section class="settings-section" data-testid="about-section">
      <div class="settings-section__lead">
        <h2>关于 PetAccess</h2>
        <p class="muted">当前版本 v{{ appVersion }} · 上海试点 · 开发预览阶段</p>
      </div>
      <div class="settings-section__body settings-about">
        <p>城市公共空间动物通行规则与现场事实查询工具。去之前，先看规则与现场。</p>
        <RouterLink class="btn-inline" to="/about">查看产品原则 →</RouterLink>
      </div>
    </section>

    <footer class="settings-foot">
      <span>当前查询：{{ querySummaryLabel() }}</span>
      <span>
        {{ signedIn ? `已登录 · ${session.user?.display_name ?? ""}` : "未登录 · 可浏览公开内容" }}
      </span>
    </footer>
  </AppShell>
</template>

<style scoped src="./SettingsView.css"></style>
