<script setup lang="ts">
import { onMounted, ref } from "vue";
import { session } from "@petaccess/client-core";
import { REQUIRED_COPY } from "@petaccess/design-tokens";
import AppShell from "../components/AppShell.vue";

/**
 * Settings / About / Methodology (UI_UX_IMPLEMENTATION_SPEC §8, P1 item 11).
 *
 * This page exists to make the product's *limits* explicit. It states plainly
 * what the data can and cannot support, so a user never reads a neutral
 * "尚未核验" as a soft prohibition, or a published operator rule as a legal
 * verdict.
 */

const signedIn = ref(false);
onMounted(async () => {
  await session.restore();
  signedIn.value = session.signedIn;
});

const RULE_LAYERS = [
  {
    key: "LEGAL",
    label: "法定要求",
    note: "法律法规直接规定，具有强制效力；下层管理方规则不能削弱它。",
  },
  {
    key: "REGULATORY_GUIDANCE",
    label: "监管指引",
    note: "主管部门的指引性文件，非直接罚则，但具有指导意义。",
  },
  { key: "OPERATOR_POLICY", label: "管理方规则", note: "场所或物业自行制定并公布的规则。" },
  { key: "TEMPORARY_POLICY", label: "临时措施", note: "有明确起止时间的临时性安排。" },
];

const EVIDENCE = [
  { key: "OFFICIAL", label: "官方来源", note: "政府或场所官方渠道发布。" },
  { key: "VERIFIED_ON_SITE", label: "现场核验", note: "有人到场核对并记录。" },
  { key: "SIGNAGE", label: "现场告示", note: "有照片证据，需人工核对。" },
  { key: "USER_STATEMENT", label: "用户陈述", note: "由用户提供，与正式规则分开呈现。" },
];
</script>

<template>
  <AppShell>
    <h1>设置与说明</h1>

    <div class="panel">
      <strong>这是什么</strong>
      <p class="muted" style="margin-top: 4px">
        本产品整理「场所对动物通行」的已核验记录，帮助你在出行前了解明确的允许、限制与条件。
        它整理的是 <em>access</em>（能否通行），不是「友好度」评价。
      </p>
    </div>

    <div class="panel" data-testid="methodology">
      <strong>规则层级</strong>
      <p class="muted" style="margin-top: 4px">
        同一场所可能同时存在多个层级的规则。当它们冲突时，法定要求构成下限，不能被下层规则削弱。
      </p>
      <div v-for="l in RULE_LAYERS" :key="l.key" class="zone-row">
        <div>
          <strong>{{ l.label }}</strong> <span class="muted">（{{ l.key }}）</span>
        </div>
        <div class="muted">{{ l.note }}</div>
      </div>
    </div>

    <div class="panel" data-testid="evidence-strength">
      <strong>证据强度</strong>
      <p class="muted" style="margin-top: 4px">
        每条规则都标注来源与证据强度。强度只描述证据本身，不改变规则的法律效力。
      </p>
      <div v-for="e in EVIDENCE" :key="e.key" class="zone-row">
        <div>
          <strong>{{ e.label }}</strong> <span class="muted">（{{ e.key }}）</span>
        </div>
        <div class="muted">{{ e.note }}</div>
      </div>
    </div>

    <div class="panel" data-testid="limits">
      <strong>我们不做的事</strong>
      <div class="notice" style="margin-top: 6px">
        · {{ REQUIRED_COPY.noRankingDisclaimer }}<br />
        · 不给场所打「友好分」，也不预测「是否会遇到宠物」<br />
        · 不把 AI 识别结果直接写成已确认规则（AI 只作解析建议）<br />
        · 不把「尚未核验」当作允许或禁止<br />
        · 不记录小区住户信息，只收录公共空间规则<br />
        · 不长期保存位置轨迹，仅记录分桶后的现场核验结果
      </div>
    </div>

    <div class="panel">
      <strong>文案与状态约定</strong>
      <div class="muted" style="margin-top: 6px">
        · 状态始终以「图标 + 文字 + 颜色」三重表达，不单靠颜色<br />
        · 未收录时显示「{{ REQUIRED_COPY.unknownShort }}」，而非默认为允许<br />
        · 现场记录与场所正式政策分开呈现
      </div>
    </div>

    <div class="panel">
      <strong>相关页面</strong>
      <div class="row" style="margin-top: 8px">
        <RouterLink to="/boundary"><button class="pill">共处边界</button></RouterLink>
        <RouterLink to="/privacy"><button class="pill">隐私与数据</button></RouterLink>
        <RouterLink to="/notifications"><button class="pill">通知</button></RouterLink>
        <RouterLink v-if="signedIn" to="/pets">
          <button class="pill">宠物档案</button>
        </RouterLink>
      </div>
    </div>

    <div class="panel">
      <div class="muted">当前查询模式：{{ session.mode }}</div>
      <div class="muted" style="margin-top: 4px">
        {{
          signedIn ? `已登录：${session.user?.display_name ?? ""}` : "未登录（可浏览公开收录内容）"
        }}
      </div>
    </div>
  </AppShell>
</template>
