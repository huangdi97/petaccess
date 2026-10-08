<script setup lang="ts">
const props = defineProps<{ mode: "login" | "register" }>();
const emit = defineEmits<{ change: [mode: "login" | "register"] }>();

function choose(mode: "login" | "register") {
  if (mode !== props.mode) emit("change", mode);
}

function onKeydown(event: KeyboardEvent) {
  if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const next =
    event.key === "Home" || event.key === "ArrowLeft"
      ? "login"
      : "register";
  choose(next);
  requestAnimationFrame(() => {
    document.getElementById(`auth-tab-${next}`)?.focus();
  });
}
</script>

<template>
  <div class="auth-mode" role="tablist" aria-label="账号操作">
    <button
      id="auth-tab-login"
      type="button"
      role="tab"
      aria-controls="auth-panel"
      :tabindex="mode === 'login' ? 0 : -1"
      :aria-selected="mode === 'login'"
      :class="{ 'auth-mode__item--active': mode === 'login' }"
      @keydown="onKeydown"
      @click="choose('login')"
    >
      登录
    </button>
    <button
      id="auth-tab-register"
      type="button"
      role="tab"
      aria-controls="auth-panel"
      :tabindex="mode === 'register' ? 0 : -1"
      :aria-selected="mode === 'register'"
      :class="{ 'auth-mode__item--active': mode === 'register' }"
      @keydown="onKeydown"
      @click="choose('register')"
    >
      注册
    </button>
  </div>
</template>

<style scoped>
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
  border-bottom-color: var(--pa-color-accent);
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-650);
}
</style>
