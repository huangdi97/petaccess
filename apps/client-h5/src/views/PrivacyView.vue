<script setup lang="ts">
/**
 * Privacy / Data Controls (spec §2.4-adjacent; Master Goal §7 privacy).
 *
 * This screen is deliberately explicit about what the product does NOT do:
 *   - no default continuous location history (ADR-012);
 *   - field records are bucketed, never raw trajectories;
 *   - lead-only sources are never stored beyond the excerpt.
 *
 * Local controls below really work (they clear on-device data). Account
 * deletion / data export are shown with their true status — the backend flow is
 * not implemented yet, so the screen says so instead of pretending.
 */
import { computed, ref } from "vue";
import { session, platformStorage } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";

const cleared = ref(false);
const deletionRequested = ref(false);

const inventory = [
  { item: "账号（邮箱、显示名）", stored: "是", purpose: "登录与会话", basis: "履行服务所必需" },
  {
    item: "宠物档案（物种、体重、肩高、服务犬角色）",
    stored: "是",
    purpose: "准入判断输入",
    basis: "用户主动提供",
  },
  { item: "共处边界偏好", stored: "是", purpose: "逐条边界比对", basis: "用户主动提供" },
  {
    item: "位置轨迹",
    stored: "否（不默认保存）",
    purpose: "—",
    basis: "ADR-012：仅一次性附近查询",
  },
  { item: "现场记录位置", stored: "分桶（如 <100m）", purpose: "核验可信度", basis: "最小化" },
  {
    item: "上传证据（图片）",
    stored: "按来源许可",
    purpose: "规则溯源",
    basis: "lead-only 不存储",
  },
  { item: "关注订阅", stored: "是", purpose: "规则变化提醒", basis: "用户主动订阅" },
];

const signedIn = computed(() => session.signedIn);

function clearLocalData() {
  platformStorage.remove("pa_token");
  session.logout();
  cleared.value = true;
}

function requestDeletion() {
  deletionRequested.value = true;
}
</script>

<template>
  <AppShell>
    <h1>隐私与数据控制</h1>

    <h2>数据清单</h2>
    <div class="panel">
      <div v-for="row in inventory" :key="row.item" class="zone-row">
        <span>
          <strong style="font-size: 14px">{{ row.item }}</strong>
          <div class="muted">{{ row.purpose }} · {{ row.basis }}</div>
        </span>
        <span class="tag">{{ row.stored }}</span>
      </div>
      <div class="notice">
        我们不建立原始连续位置历史（ADR-012）；贡献位置以分桶方式保存；lead-only 来源不落库。
      </div>
    </div>

    <h2>本机数据</h2>
    <div class="panel">
      <div class="muted">
        {{ signedIn ? "当前设备已登录，令牌保存在本机。" : "当前设备未登录。" }}
      </div>
      <button
        class="block"
        style="margin-top: 8px"
        data-testid="clear-local"
        :disabled="!signedIn"
        @click="clearLocalData"
      >
        清除本机登录状态
      </button>
      <div v-if="cleared" class="notice" data-testid="cleared-msg">
        已清除本机登录状态。服务器上的账号数据不受影响。
      </div>
    </div>

    <h2>定位</h2>
    <div class="panel">
      <div class="muted">
        定位为一次性使用：仅用于“附近”查询，不持续记录、不后台采集。可在系统设置中关闭定位权限。
      </div>
    </div>

    <h2>账号删除与数据导出</h2>
    <div class="panel">
      <StateMessage
        kind="PARTIAL"
        description="账号删除与数据导出流程尚未开放（后端接口未实现）。当前版本可通过反馈渠道人工处理，我们不会声称已完成。"
      >
        <template #action>
          <button class="primary" data-testid="request-deletion" @click="requestDeletion">
            提交人工删除请求
          </button>
        </template>
      </StateMessage>
      <div v-if="deletionRequested" class="notice" data-testid="deletion-requested">
        已记录你的删除请求（本机标记）。请通过反馈渠道提供账号邮箱以完成人工核验。
      </div>
    </div>

    <h2>数据来源与许可</h2>
    <div class="panel">
      <div class="muted">
        每条规则都标注来源、采集方式与再分发许可；不可再分发的内容仅用于判断，不对外展示原文。
      </div>
    </div>
  </AppShell>
</template>
