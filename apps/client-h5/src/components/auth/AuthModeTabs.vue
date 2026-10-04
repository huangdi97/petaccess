<script setup lang="ts">
defineProps<{ mode: "login" | "register" }>();
const emit = defineEmits<{ change: [mode: "login" | "register"] }>();
</script>

<template>
  <div class="auth-mode" role="tablist" aria-label="账号操作">
    <button
      type="button"
      role="tab"
      :aria-selected="mode === 'login'"
      :class="{ 'auth-mode__item--active': mode === 'login' }"
      @click="emit('change', 'login')"
    >
      登录
    </button>
    <button
      type="button"
      role="tab"
      :aria-selected="mode === 'register'"
      :class="{ 'auth-mode__item--active': mode === 'register' }"
      @click="emit('change', 'register')"
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
