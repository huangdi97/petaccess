<script setup lang="ts">
defineProps<{ online: boolean; signedIn: boolean; editing: boolean }>();
const emit = defineEmits<{ create: [] }>();
</script>

<template>
  <div v-if="!online" class="offline-banner" data-testid="offline-banner">
    <span aria-hidden="true">⊘</span>
    <span>当前无网络连接：可查看已加载档案，保存操作已暂停。</span>
  </div>

  <header class="profile-head">
    <div>
      <h1>宠物档案</h1>
      <p class="muted">只填写规则判断真正需要的信息；留空字段保持未知，不会被系统猜测。</p>
    </div>
    <button
      v-if="signedIn && !editing"
      type="button"
      class="profile-head__action"
      data-testid="pet-new"
      @click="emit('create')"
    >
      新建档案
    </button>
  </header>
</template>

<style scoped>
.profile-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.profile-head p {
  max-width: 620px;
  margin: var(--pa-space-2) 0 0;
}

.profile-head__action {
  flex: 0 0 auto;
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  cursor: pointer;
}

@media (max-width: 767px) {
  .profile-head {
    flex-direction: column;
  }
}
</style>
