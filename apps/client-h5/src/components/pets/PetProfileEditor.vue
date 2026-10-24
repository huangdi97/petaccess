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
        <option value="unknown">服务犬身份未确认</option>
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

<style scoped src="./PetProfileEditor.css"></style>
