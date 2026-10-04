<script setup lang="ts">
// @ui-static OnboardingView — 登录/注册流程页，自有表单状态（M3 E1 静态声明）。
import { ref } from "vue";
import { useRouter } from "vue-router";
import { session } from "@petaccess/client-core";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import { presentDescription } from "../errors";

const router = useRouter();
const mode = ref<"login" | "register">("login");
const displayName = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);

async function submit() {
  error.value = "";
  busy.value = true;
  try {
    if (mode.value === "login") {
      await session.login(email.value, password.value);
    } else {
      await session.register(displayName.value, email.value, password.value);
    }
    router.push({ name: "home" });
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <DesktopContentContainer mode="single-column">
    <main class="auth-page">
      <header class="auth-head">
        <p class="auth-brand">PetAccess</p>
        <h1>开始使用</h1>
        <p class="muted">
          登录后可以保存宠物档案、关注规则变化和查看自己的贡献；查询公开场所信息不要求登录。
        </p>
      </header>

      <div class="auth-mode" role="tablist" aria-label="账号操作">
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'login'"
          :class="{ 'auth-mode__item--active': mode === 'login' }"
          @click="mode = 'login'"
        >
          登录
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'register'"
          :class="{ 'auth-mode__item--active': mode === 'register' }"
          @click="mode = 'register'"
        >
          注册
        </button>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <label v-if="mode === 'register'" class="auth-field">
          <span>昵称</span>
          <input v-model="displayName" required autocomplete="name" />
        </label>

        <label class="auth-field">
          <span>邮箱</span>
          <input v-model="email" type="email" required autocomplete="username" />
        </label>

        <label class="auth-field">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            required
            minlength="8"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          />
          <small v-if="mode === 'register'">至少 8 位。</small>
        </label>

        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>

        <button class="primary auth-submit" type="submit" :disabled="busy">
          {{ busy ? "处理中…" : mode === "login" ? "登录" : "注册并开始" }}
        </button>
      </form>

      <p class="auth-privacy muted">
        位置只用于当前附近查询与现场核验，不建立连续轨迹；服务犬身份只由用户自行声明。
      </p>

      <button class="auth-skip" type="button" @click="router.push({ name: 'home' })">
        先浏览公开内容 →
      </button>
    </main>
  </DesktopContentContainer>
</template>

<style scoped>
.auth-page {
  width: min(100%, 520px);
  margin: 0 auto;
  padding: var(--pa-space-8) 0;
}

.auth-head {
  padding-bottom: var(--pa-space-5);
}

.auth-brand {
  margin: 0 0 var(--pa-space-3);
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-650);
  letter-spacing: var(--pa-letter-spacing-wide);
}

.auth-head p:last-child {
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.auth-mode {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.auth-mode button {
  min-height: 48px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--pa-color-text-secondary);
  cursor: pointer;
}

.auth-mode__item--active {
  border-bottom-color: var(--pa-color-accent) !important;
  color: var(--pa-color-text-primary) !important;
  font-weight: var(--pa-font-weight-650);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-4);
  padding-top: var(--pa-space-5);
}

.auth-field {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  font-size: var(--pa-font-size-md);
}

.auth-field input {
  margin: 0;
}

.auth-field small {
  color: var(--pa-color-text-muted);
}

.auth-error {
  margin: 0;
  color: var(--pa-color-status-restricted);
  font-size: var(--pa-font-size-md);
}

.auth-submit {
  min-height: 48px;
}

.auth-privacy {
  margin: var(--pa-space-5) 0 0;
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

.auth-skip {
  margin-top: var(--pa-space-4);
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  padding: 0;
  cursor: pointer;
}

@media (max-width: 767px) {
  .auth-page {
    padding: var(--pa-space-5) var(--pa-space-4);
  }
}
</style>
