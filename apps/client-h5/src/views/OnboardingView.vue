<script setup lang="ts">
// @ui-static OnboardingView — login/register task workspace.
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { session } from "@petaccess/client-core";
import AuthModeTabs from "../components/auth/AuthModeTabs.vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import { presentDescription } from "../errors";

const router = useRouter();
const route = useRoute();
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
    const rawNext = typeof route.query.next === "string" ? route.query.next : "";
    const safeNext =
      rawNext.startsWith("/") && !rawNext.startsWith("//") && !rawNext.startsWith("/onboarding")
        ? rawNext
        : "";
    await router.replace(safeNext || { name: "home" });
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <DesktopContentContainer mode="wide">
    <main class="auth-page">
      <section class="auth-intro" aria-labelledby="auth-title">
        <p class="auth-brand">PetAccess</p>
        <h1 id="auth-title">开始使用</h1>
        <p class="auth-intro__lead">
          公开的场所规则、现场事实和证据无需登录即可查询。账号只用于保存与你有关的对象、关注与贡献。
        </p>

        <dl class="auth-facts">
          <div>
            <dt>公开查询</dt>
            <dd>不登录也能搜索场所、查看规则与经核验现场事实。</dd>
          </div>
          <div>
            <dt>保存上下文</dt>
            <dd>登录后可保存宠物档案、当前查询对象和变化关注。</dd>
          </div>
          <div>
            <dt>贡献待核验</dt>
            <dd>你提交的规则线索与现场事实先进入审核，不会直接改写正式结论。</dd>
          </div>
        </dl>

        <button class="auth-skip" type="button" @click="router.push({ name: 'home' })">
          先浏览公开内容 →
        </button>
      </section>

      <section class="auth-workspace" aria-label="登录或注册">
        <AuthModeTabs :mode="mode" @change="mode = $event" />

        <div
          id="auth-panel"
          class="auth-panel"
          role="tabpanel"
          :aria-labelledby="`auth-tab-${mode}`"
        >
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

          <p class="auth-privacy">
            位置只用于当前附近查询与现场核验，不建立连续轨迹；服务犬身份只由用户自行声明。
          </p>
        </div>
      </section>
    </main>
  </DesktopContentContainer>
</template>

<style scoped src="./OnboardingView.css"></style>
