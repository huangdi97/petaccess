<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { session } from "@petaccess/client-core";

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
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="page">
    <h1>开始使用</h1>
    <p class="muted">
      查询任何场所对动物的准入规则：带宠出行 · 普通宠物限制 · 服务犬通行 · 规则地图。
      规则来自官方/管理方/现场核验，一切可追溯。
    </p>
    <div class="panel">
      <div class="row">
        <button class="pill" :class="{ active: mode === 'login' }" @click="mode = 'login'">
          登录
        </button>
        <button class="pill" :class="{ active: mode === 'register' }" @click="mode = 'register'">
          注册
        </button>
      </div>
      <div v-if="error" class="notice" style="color: var(--restricted)">{{ error }}</div>
      <form @submit.prevent="submit">
        <label v-if="mode === 'register'">昵称</label>
        <input v-if="mode === 'register'" v-model="displayName" required />
        <label>邮箱</label>
        <input v-model="email" type="email" required autocomplete="username" />
        <label>密码（≥8 位）</label>
        <input
          v-model="password"
          type="password"
          required
          minlength="8"
          autocomplete="current-password"
        />
        <button class="primary block" style="margin-top: 14px" :disabled="busy">
          {{ mode === "login" ? "登录" : "注册并开始" }}
        </button>
      </form>
      <div class="notice">
        位置仅用于附近查询与现场核验，不建立连续轨迹；小区只展示公共空间规则。
      </div>
    </div>
    <button class="block" @click="router.push({ name: 'home' })">先随便看看（免登录）</button>
  </div>
</template>
