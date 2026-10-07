<script setup lang="ts">
import type { PetView } from "@petaccess/client-core";

const props = defineProps<{ pets: PetView[]; activeId: string | null; busy: boolean }>();
const emit = defineEmits<{
  activate: [pet: PetView];
  edit: [pet: PetView];
  remove: [pet: PetView];
}>();

const SPECIES_LABELS: Record<string, string> = { dog: "犬", cat: "猫", other: "其他" };
const SERVICE_LABELS: Record<string, string> = {
  working: "服务犬（在役 · 用户声明）",
  in_training: "服务犬（训练中 · 用户声明）",
  unknown: "服务犬身份未确认",
};
</script>

<template>
  <section class="profile-list" aria-label="宠物档案列表">
    <article v-for="pet in props.pets" :key="pet.id" class="profile-row" data-testid="pet-card">
      <div class="profile-row__head">
        <div>
          <strong class="profile-row__name">{{ pet.display_name }}</strong>
          <span v-if="activeId === pet.id" class="profile-row__active" data-testid="pet-active">
            本次使用中
          </span>
        </div>
        <div class="profile-row__actions">
          <button
            v-if="activeId !== pet.id"
            :data-testid="`pet-use-${pet.id}`"
            @click="emit('activate', pet)"
          >
            设为本次对象
          </button>
          <button :data-testid="`pet-edit-${pet.id}`" @click="emit('edit', pet)">编辑</button>
          <button
            :disabled="busy"
            :data-testid="`pet-delete-${pet.id}`"
            @click="emit('remove', pet)"
          >
            删除
          </button>
        </div>
      </div>

      <p class="muted profile-row__meta">
        {{ SPECIES_LABELS[pet.species] ?? "其他" }}
        <template v-if="pet.breed_text"> · {{ pet.breed_text }}</template>
        <template v-if="pet.weight_kg != null"> · {{ pet.weight_kg }} kg</template>
        <template v-if="pet.shoulder_height_cm != null">
          · 肩高 {{ pet.shoulder_height_cm }} cm
        </template>
      </p>

      <p v-if="pet.service_role !== 'none'" class="muted profile-row__meta">
        {{ SERVICE_LABELS[pet.service_role] ?? "服务犬身份未确认" }}
      </p>
      <p
        v-if="pet.weight_kg == null || pet.shoulder_height_cm == null"
        class="profile-row__missing"
      >
        尚未填写{{ pet.weight_kg == null ? "体重" : ""
        }}{{ pet.weight_kg == null && pet.shoulder_height_cm == null ? "与" : ""
        }}{{ pet.shoulder_height_cm == null ? "肩高" : "" }}；相关规则需要时再补充即可。
      </p>
    </article>
  </section>
</template>

<style scoped>
.profile-list {
  margin-top: var(--pa-space-3);
}

.profile-row {
  padding: var(--pa-space-4) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.profile-row__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
}

.profile-row__name {
  font-size: var(--pa-font-size-lg);
}

.profile-row__active {
  margin-left: var(--pa-space-2);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-accent);
}

.profile-row__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
}

.profile-row__actions button {
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  min-height: var(--pa-size-control-md);
  padding: 0 var(--pa-space-1);
  cursor: pointer;
}

.profile-row__meta,
.profile-row__missing {
  margin: var(--pa-space-1) 0 0;
}

.profile-row__missing {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .profile-row__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .profile-row__actions {
    gap: var(--pa-space-3);
  }
}
</style>
