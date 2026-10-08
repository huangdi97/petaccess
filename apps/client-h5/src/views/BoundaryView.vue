<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, ApiError, session, type BoundaryProfile } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import BoundaryPreferenceList from "../components/boundary/BoundaryPreferenceList.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { useOnline } from "../composables/useOnline";

const profileName = ref("我的共处边界");
const chosen = ref<Record<string, string>>({});
const error = ref("");
const msg = ref("");
const busy = ref(false);
const loaded = ref(false);
const loading = ref(true);
const signedIn = ref(false);
const { online } = useOnline();

function apply(profile: BoundaryProfile | null) {
  if (!profile) {
    chosen.value = {};
    return;
  }
  profileName.value = profile.name || "我的共处边界";
  chosen.value = Object.fromEntries(profile.preferences.map((p) => [p.attribute, p.stance]));
}

async function load() {
  error.value = "";
  loading.value = true;
  try {
    await session.restore();
    signedIn.value = session.signedIn;
    if (!signedIn.value) {
      apply(null);
      return;
    }
    apply((await client.defaultBoundaryProfile()).profile);
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    loaded.value = true;
    loading.value = false;
  }
}

function pick(attribute: string, stance: string) {
  const next = { ...chosen.value };
  if (!stance) delete next[attribute];
  else next[attribute] = stance;
  chosen.value = next;
}

async function save() {
  error.value = "";
  msg.value = "";
  if (!online.value) {
    error.value = "当前无网络连接，边界保存需要联网。";
    return;
  }
  busy.value = true;
  try {
    const preferences = Object.entries(chosen.value).map(([attribute, stance]) => ({
      attribute,
      stance,
      note: null,
    }));
    const saved = await client.saveBoundaryProfile({
      name: profileName.value || "我的共处边界",
      is_default: true,
      preferences,
    });
    apply(saved);
    msg.value = preferences.length
      ? `已保存 ${preferences.length} 项边界`
      : "已保存；未设置项目继续保持信息不足";
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：可查看已加载内容，保存操作已暂停。</span>
    </div>

    <SkeletonList v-if="loading" :rows="4" />

    <StateMessage
      v-else-if="error && !loaded"
      kind="ERROR"
      :description="`未能取得共处边界：${error}`"
    >
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>

    <StateMessage
      v-else-if="!signedIn"
      kind="PERMISSION_DENIED"
      title="登录后设置共处边界"
      description="共处边界属于你的私有出行偏好，需要登录后保存和同步。公开规则与现场事实仍可免登录查看。"
      data-testid="boundary-sign-in"
    >
      <template #action>
        <RouterLink class="btn primary" :to="{ name: 'onboarding', query: { next: '/boundary' } }"
          >登录 / 注册</RouterLink
        >
      </template>
    </StateMessage>

    <template v-else>
      <header class="boundary-head">
        <h1>共处边界</h1>
        <p class="muted">
          这些是你自己的出行偏好，只用于逐项比对场所公开记录，不形成场所总分。
          没有设置的项目会保持信息不足。
        </p>
      </header>

      <p v-if="error" class="boundary-feedback" data-testid="boundary-error">{{ error }}</p>
      <p v-if="msg" class="boundary-feedback" data-testid="boundary-msg">{{ msg }}</p>

      <label class="boundary-name">
        <span>方案名称</span>
        <input v-model="profileName" aria-label="共处边界名称" placeholder="我的共处边界" />
      </label>

      <BoundaryPreferenceList :chosen="chosen" @pick="pick" />

      <div class="boundary-actions">
        <button
          class="primary"
          :disabled="busy || !loaded || !online"
          data-testid="boundary-save"
          @click="save"
        >
          {{ busy ? "保存中…" : "保存边界" }}
        </button>
      </div>

      <p class="boundary-note muted">
        共处边界只改变“是否符合你的偏好”的逐项展示，不改变场所规则、现场事实或服务犬通行规则。
      </p>
    </template>
  </AppShell>
</template>

<style scoped src="./BoundaryView.css"></style>
