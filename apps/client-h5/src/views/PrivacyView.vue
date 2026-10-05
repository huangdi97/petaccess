<script setup lang="ts">
// @ui-static PrivacyView — static privacy and local-data controls.
import { computed, ref } from "vue";
import { session, platformStorage } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";

const cleared = ref(false);

const inventory = [
  { item: "账号", stored: "保存", detail: "邮箱与显示名，用于登录和会话。" },
  { item: "宠物档案", stored: "保存", detail: "仅使用你主动填写、且规则判断真正需要的信息。" },
  { item: "共处边界", stored: "保存", detail: "用于逐项比对你的出行偏好，不形成场所总分。" },
  { item: "连续位置轨迹", stored: "不保存", detail: "附近查询只使用当次位置，不建立持续轨迹。" },
  { item: "现场核验位置", stored: "最小化保存", detail: "只保留核验所需的距离或精度范围。" },
  { item: "上传证据", stored: "按许可处理", detail: "作为私有核验材料保存；不可公开再分发的内容不会直接向消费者展示。" },
  { item: "规则关注", stored: "保存", detail: "仅保存你主动关注的规则变化。" },
];

const signedIn = computed(() => session.signedIn);

function clearLocalData() {
  platformStorage.remove("pa_token");
  session.logout();
  cleared.value = true;
}
</script>

<template>
  <AppShell>
    <header class="privacy-head">
      <h1>隐私与数据</h1>
      <p class="muted">
        只收集完成查询、核验和账号功能所需要的数据；位置不会被默认保存为连续轨迹。
      </p>
    </header>

    <section class="privacy-section">
      <h2>数据清单</h2>
      <div class="privacy-inventory">
        <div v-for="row in inventory" :key="row.item" class="privacy-row">
          <div class="privacy-row__body">
            <strong>{{ row.item }}</strong>
            <span class="muted">{{ row.detail }}</span>
          </div>
          <span class="privacy-row__state">{{ row.stored }}</span>
        </div>
      </div>
    </section>

    <section class="privacy-section">
      <h2>本机登录状态</h2>
      <p class="muted">
        {{ signedIn ? "当前设备已登录。" : "当前设备未登录。" }}
        清除本机状态不会删除服务器上的账号数据。
      </p>
      <button
        class="privacy-action"
        type="button"
        data-testid="clear-local"
        :disabled="!signedIn"
        @click="clearLocalData"
      >
        清除本机登录状态
      </button>
      <p v-if="cleared" class="privacy-feedback" data-testid="cleared-msg">
        已清除本机登录状态；服务器上的账号数据未改变。
      </p>
    </section>

    <section class="privacy-section">
      <h2>定位</h2>
      <p class="muted">
        定位只用于当前“附近”查询或现场核验，不持续记录、不在后台建立位置历史。你可以随时在系统设置中关闭定位权限。
      </p>
    </section>

    <section class="privacy-section">
      <h2>账号删除与数据导出</h2>
      <StateMessage
        kind="PARTIAL"
        description="当前开发预览版尚未接入应用内账号删除与数据导出申请。这里不会用本机按钮假装已经向服务器提交请求；正式开放前会提供可核验的申请与处理状态。"
      />
    </section>

    <section class="privacy-section">
      <h2>来源与许可</h2>
      <p class="muted">
        每条规则和现场事实都保留来源与采集方式。不能公开再分发的材料只用于核验，不直接向消费者展示原文。
      </p>
    </section>
  </AppShell>
</template>

<style scoped>
.privacy-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.privacy-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.privacy-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.privacy-section h2 {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.privacy-section > p {
  max-width: 680px;
  margin: 0;
  line-height: var(--pa-line-height-23);
}

.privacy-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.privacy-row:last-child {
  border-bottom: none;
}

.privacy-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.privacy-row__state {
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-md);
  text-align: right;
}

.privacy-action {
  margin-top: var(--pa-space-3);
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  padding: 0;
  cursor: pointer;
}

.privacy-action:disabled {
  color: var(--pa-color-text-muted);
  cursor: default;
}

.privacy-feedback {
  margin-top: var(--pa-space-3) !important;
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .privacy-row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }

  .privacy-row__state {
    text-align: left;
  }
}
</style>
