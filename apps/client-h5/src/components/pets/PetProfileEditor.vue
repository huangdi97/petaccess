<script setup lang="ts">
import type { PetDraft } from "../../consumer/petProfileModel";

defineProps<{ isNew: boolean; busy: boolean }>();
const draft = defineModel<PetDraft>("draft", { required: true });
const emit = defineEmits<{ save: []; cancel: [] }>();
</script>

<template>
  <section class="profile-editor" data-testid="pet-editor">
    <div class="profile-editor__head">
      <h2>{{ isNew ? "新建宠物档案" : "编辑宠物档案" }}</h2>
      <p class="muted">名称只用于你自己区分多个档案；体重和肩高可以留空。</p>
    </div>

    <div class="profile-form-grid">
      <label class="profile-field">
        <span>名称</span>
        <input v-model="draft.display_name" data-testid="pet-name" placeholder="如：豆豆" />
      </label>
      <label class="profile-field">
        <span>物种</span>
        <select v-model="draft.species" data-testid="pet-species">
          <option value="dog">犬</option>
          <option value="cat">猫</option>
          <option value="other">其他</option>
        </select>
      </label>
      <label class="profile-field">
        <span>品种（可选）</span>
        <input v-model="draft.breed_text" data-testid="pet-breed" placeholder="如：柴犬" />
      </label>
      <label class="profile-field">
        <span>体重 kg（可选）</span>
        <input
          v-model="draft.weight_kg"
          type="number"
          step="0.1"
          min="0"
          max="300"
          data-testid="pet-weight"
        />
        <small>只有规则涉及体重限制时才会使用。</small>
      </label>
      <label class="profile-field">
        <span>肩高 cm（可选）</span>
        <input
          v-model="draft.shoulder_height_cm"
          type="number"
          step="1"
          min="0"
          max="250"
          data-testid="pet-shoulder"
        />
        <small>只有规则涉及体型限制时才会使用。</small>
      </label>
    </div>

    <fieldset class="profile-service" data-testid="pet-service-block">
      <legend>服务犬身份</legend>
      <p class="muted">仅由你自行声明。平台不凭照片、品种或体型认定服务犬身份。</p>
      <select v-model="draft.service_role" data-testid="pet-service-role">
        <option value="none">普通宠物</option>
        <option value="working">服务犬（在役）</option>
        <option value="in_training">服务犬（训练中）</option>
        <option value="retired">服务犬（已退役）</option>
      </select>
    </fieldset>

    <div class="profile-actions">
      <button
        class="primary"
        :disabled="!draft.display_name.trim() || busy"
        data-testid="pet-save"
        @click="emit('save')"
      >
        {{ busy ? "保存中…" : "保存" }}
      </button>
      <button :disabled="busy" @click="emit('cancel')">取消</button>
    </div>
  </section>
</template>

<style scoped>
.profile-editor {
  padding-top: var(--pa-space-5);
}

.profile-editor__head h2 {
  margin: 0;
  font-size: var(--pa-font-size-xl);
}

.profile-editor__head p {
  margin: var(--pa-space-1) 0 var(--pa-space-4);
}

.profile-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--pa-space-4);
}

.profile-field {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  font-size: var(--pa-font-size-md);
}

.profile-field input,
.profile-field select,
.profile-service select {
  margin: 0;
}

.profile-field small {
  color: var(--pa-color-text-muted);
}

.profile-service {
  margin: var(--pa-space-5) 0 0;
  padding: var(--pa-space-4) 0 0;
  border: 0;
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.profile-service legend {
  padding: 0;
  font-weight: var(--pa-font-weight-650);
}

.profile-service p {
  max-width: 620px;
  margin: var(--pa-space-1) 0 var(--pa-space-3);
}

.profile-service select {
  max-width: 320px;
}

.profile-actions {
  display: flex;
  gap: var(--pa-space-2);
  padding-top: var(--pa-space-5);
}

@media (max-width: 767px) {
  .profile-form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
