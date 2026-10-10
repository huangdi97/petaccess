<script setup lang="ts">
import { client, session } from "@petaccess/client-core";
import { animalScopeLabel } from "../../consumer/labels";

type Pet = Awaited<ReturnType<typeof client.myPets>>[number];

defineProps<{ pets: Pet[] }>();
const emit = defineEmits<{ activate: [pet: Pet] }>();

function petMeta(pet: Pet): string {
  const parts = [animalScopeLabel(pet.species), pet.breed_text ?? ""].filter(Boolean);
  if (pet.weight_kg) parts.push(`${pet.weight_kg} kg`);
  if (pet.service_role === "working") parts.push("服务犬（在役 · 用户声明）");
  else if (pet.service_role === "in_training") parts.push("服务犬（训练中 · 用户声明）");
  else if (pet.service_role === "unknown") parts.push("服务犬身份未确认");
  return parts.join(" · ");
}
</script>

<template>
  <section class="mine-section">
    <div class="mine-section__head">
      <div>
        <h2>宠物档案</h2>
        <p class="muted">用于当前查询中真正需要的物种、体重或角色条件。</p>
      </div>
      <RouterLink class="btn-inline" to="/pets" data-testid="open-pet-profile">
        管理档案 →
      </RouterLink>
    </div>

    <div v-for="pet in pets" :key="pet.id" class="mine-row">
      <div class="mine-row__body">
        <strong>{{ pet.display_name }}</strong>
        <span class="muted">{{ petMeta(pet) }}</span>
      </div>
      <button
        type="button"
        class="mine-row__action"
        :aria-pressed="session.activePet?.id === pet.id"
        @click="emit('activate', pet)"
      >
        {{ session.activePet?.id === pet.id ? "本次使用中" : "设为本次对象" }}
      </button>
    </div>

    <p v-if="!pets.length" class="mine-empty">
      还没有宠物档案。没有必要为了浏览公开规则先建立档案。
    </p>
  </section>
</template>

<style scoped>
.mine-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-section__head,
.mine-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
}

.mine-section__head {
  margin-bottom: var(--pa-space-3);
}

.mine-section h2 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.mine-section__head p {
  margin: var(--pa-space-1) 0 0;
}

.mine-row {
  align-items: center;
  min-height: 56px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.mine-row__action {
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  min-height: var(--pa-size-control-md);
  cursor: pointer;
}

.mine-empty {
  margin: 0;
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .mine-section__head,
  .mine-row {
    flex-direction: column;
    gap: var(--pa-space-2);
  }
}
</style>
