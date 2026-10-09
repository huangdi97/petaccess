<script setup lang="ts">
// PrivacyView — local controls + authenticated privacy-rights transactions.
import { computed, onMounted, ref } from "vue";
import { client, session, platformStorage } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

const cleared = ref(false);
const exportBusy = ref(false);
const deletionBusy = ref(false);
const rightsError = ref("");
const deletionStatus = ref<"none" | "submitted" | string>("none");
const deletionRequestedAt = ref<string | null>(null);
const confirmDeletion = ref(false);

const inventory = [
  { item: "账号", stored: "保存", detail: "邮箱与显示名，用于登录和会话。" },
  { item: "宠物档案", stored: "保存", detail: "仅使用你主动填写、且规则判断真正需要的信息。" },
  { item: "共处边界", stored: "保存", detail: "用于逐项比对你的出行偏好，不形成场所总分。" },
  { item: "连续位置轨迹", stored: "不保存", detail: "附近查询只使用当次位置，不建立持续轨迹。" },
  { item: "现场核验位置", stored: "最小化保存", detail: "只保留核验所需的距离或精度范围。" },
  {
    item: "上传证据",
    stored: "按许可处理",
    detail: "作为私有核验材料保存；不可公开再分发的内容不会直接向消费者展示。",
  },
  { item: "变化关注", stored: "保存", detail: "仅保存你主动关注的规则变化或经核验现场更新。" },
];

const signedIn = computed(() => session.signedIn);

function clearLocalData() {
  platformStorage.remove("pa_token");
  session.logout();
  cleared.value = true;
}

async function loadRightsStatus() {
  rightsError.value = "";
  try {
    await session.restore();
    if (!session.signedIn) return;
    const row = await client.accountDeletionRequest();
    deletionStatus.value = row.status;
    deletionRequestedAt.value = row.requested_at;
  } catch (error) {
    rightsError.value = presentDescription(error);
  }
}

async function exportData() {
  if (!session.signedIn || exportBusy.value) return;
  exportBusy.value = true;
  rightsError.value = "";
  try {
    const payload = await client.exportMyData();
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `petaccess-data-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    rightsError.value = presentDescription(error);
  } finally {
    exportBusy.value = false;
  }
}

async function submitDeletionRequest() {
  if (!session.signedIn || deletionBusy.value) return;
  deletionBusy.value = true;
  rightsError.value = "";
  try {
    const row = await client.requestAccountDeletion();
    deletionStatus.value = row.status;
    deletionRequestedAt.value = row.requested_at;
    confirmDeletion.value = false;
  } catch (error) {
    rightsError.value = presentDescription(error);
  } finally {
    deletionBusy.value = false;
  }
}

onMounted(loadRightsStatus);
</script>

<template>
  <AppShell>
    <header class="privacy-head">
      <p class="privacy-head__kicker">数据与权限</p>
      <h1>隐私与数据</h1>
      <p class="muted">
        只收集完成查询、核验和账号功能所需要的数据；位置不会被默认保存为连续轨迹。
      </p>
    </header>

    <section class="privacy-section">
      <div class="privacy-section__lead">
        <h2>数据清单</h2>
        <p class="muted">每一类数据都说明是否保存以及用于什么。</p>
      </div>
      <div class="privacy-section__body privacy-inventory">
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
      <div class="privacy-section__lead">
        <h2>本机登录状态</h2>
        <p class="muted">本机凭据与服务器账号是两件不同的事。</p>
      </div>
      <div class="privacy-section__body">
        <p class="privacy-copy">
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
      </div>
    </section>

    <section class="privacy-section">
      <div class="privacy-section__lead">
        <h2>定位</h2>
        <p class="muted">按次使用，不建立后台轨迹。</p>
      </div>
      <div class="privacy-section__body">
        <p class="privacy-copy">
          定位只用于当前“附近”查询或现场核验，不持续记录、不在后台建立位置历史。你可以随时在系统设置中关闭定位权限。
        </p>
      </div>
    </section>

    <section class="privacy-section">
      <div class="privacy-section__lead">
        <h2>账号删除与数据导出</h2>
        <p class="muted">服务端操作会返回真实状态，不用本机按钮伪装完成。</p>
      </div>
      <div class="privacy-section__body">
        <StateMessage
          v-if="!signedIn"
          kind="PERMISSION_DENIED"
          description="登录后可以获取自己的数据副本，或提交可追踪的账号删除申请。"
        />
        <template v-else>
          <p class="privacy-copy">
            数据副本包含账号、宠物档案、共处边界、变化关注、贡献活动和上传媒体元数据；
            不包含密码哈希、对象存储内部路径或其他用户的数据。
          </p>
          <div class="privacy-rights-actions">
            <button
              type="button"
              class="privacy-action"
              data-testid="privacy-export"
              :disabled="exportBusy"
              @click="exportData"
            >
              {{ exportBusy ? "正在生成…" : "下载我的数据副本（JSON）" }}
            </button>
          </div>

          <div class="privacy-deletion">
            <p
              v-if="deletionStatus === 'submitted'"
              class="privacy-feedback"
              data-testid="deletion-status"
            >
              删除申请已提交{{
                deletionRequestedAt ? ` · ${deletionRequestedAt.slice(0, 10)}` : ""
              }}。
              当前账号不会在申请提交瞬间被物理删除；需要长期保留的贡献与证据会先进行保留义务和去标识化审核。
            </p>
            <template v-else>
              <button
                v-if="!confirmDeletion"
                type="button"
                class="privacy-action privacy-action--danger"
                data-testid="privacy-delete-request-open"
                @click="confirmDeletion = true"
              >
                申请删除账号
              </button>
              <div v-else class="privacy-confirm" data-testid="privacy-delete-confirm">
                <p>
                  这会提交真实的账号删除申请，但不会谎称已经完成删除。审核处理前账号仍可使用；
                  已发布贡献可能在去标识化后继续作为可追溯证据保留。
                </p>
                <div class="privacy-confirm__actions">
                  <button
                    type="button"
                    class="privacy-action privacy-action--danger"
                    data-testid="privacy-delete-request-submit"
                    :disabled="deletionBusy"
                    @click="submitDeletionRequest"
                  >
                    {{ deletionBusy ? "提交中…" : "确认提交删除申请" }}
                  </button>
                  <button type="button" class="privacy-action" @click="confirmDeletion = false">
                    取消
                  </button>
                </div>
              </div>
            </template>
          </div>
          <p v-if="rightsError" class="privacy-feedback privacy-feedback--error" role="alert">
            {{ rightsError }}
          </p>
        </template>
      </div>
    </section>

    <section class="privacy-section">
      <div class="privacy-section__lead">
        <h2>来源与许可</h2>
        <p class="muted">来源可追溯不等于所有原始材料都能公开。</p>
      </div>
      <div class="privacy-section__body">
        <p class="privacy-copy">
          每条规则和现场事实都保留来源与采集方式。不能公开再分发的材料只用于核验，不直接向消费者展示原文。
        </p>
      </div>
    </section>
  </AppShell>
</template>

<style scoped src="./PrivacyView.css"></style>
