<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login, ApiError } from "../api";

const router = useRouter();
const email = ref("admin@demo-petaccess.com");
const password = ref("");
const error = ref("");
const busy = ref(false);

async function submit() {
  error.value = "";
  busy.value = true;
  try {
    await login(email.value, password.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : "登录失败";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div style="max-width: 380px; margin: 12vh auto">
    <div class="panel">
      <h1>管理后台登录</h1>
      <div v-if="error" class="error-banner">{{ error }}</div>
      <form @submit.prevent="submit">
        <!-- `for`/`id` pairs, not floating labels: an unassociated <label> looks
             correct on screen but leaves the input with no accessible name, so
             a screen reader announces "edit text" for both fields. -->
        <label for="login-email">邮箱</label>
        <input id="login-email" v-model="email" type="email" required autocomplete="username" />
        <label for="login-password">密码</label>
        <input
          id="login-password"
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
        />
        <button
          class="primary"
          type="submit"
          style="margin-top: 16px; width: 100%"
          :disabled="busy"
        >
          {{ busy ? "登录中…" : "登录" }}
        </button>
      </form>
      <p class="muted" style="margin-top: 12px">
        演示环境：种子管理员 admin@demo-petaccess.com 需先设置密码（见 README）。
      </p>
    </div>
  </div>
</template>
