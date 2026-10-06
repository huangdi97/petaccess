<script setup lang="ts">
// @ui-form PetNewView — 表单页：提交流错误内联呈现，无列表加载（M3 E1 表单声明）。
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { client, session } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import PetImageSuggestion from "../components/pets/PetImageSuggestion.vue";
import StateMessage from "../components/StateMessage.vue";

const router = useRouter();
const pet = ref({ display_name: "", species: "dog", breed_text: "", weight_kg: "" });
const serviceRole = ref("none");
const error = ref("");
const saving = ref(false);
const loadingSession = ref(true);
const signedIn = ref(false);

onMounted(async () => {
  await session.restore();
  signedIn.value = session.signedIn;
  loadingSession.value = false;
});

async function save() {
  if (!signedIn.value) return;
  error.value = "";
  saving.value = true;
  try {
    const created = await client.createPet({
      display_name: pet.value.display_name,
      species: pet.value.species,
      breed_text: pet.value.breed_text || null,
      weight_kg: pet.value.weight_kg ? Number(pet.value.weight_kg) : null,
      service_role: serviceRole.value,
    });
    session.activePet = {
      id: created.id,
      display_name: pet.value.display_name,
      species: pet.value.species,
      breed_text: pet.value.breed_text || null,
      weight_kg: pet.value.weight_kg ? Number(pet.value.weight_kg) : null,
      service_role: serviceRole.value,
    };
    router.push({ name: "home" });
  } catch (e) {
    error.value = e instanceof Error ? `保存失败（需登录）：${e.message}` : String(e);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <AppShell>
    <header class="pet-new-head">
      <h1>新建宠物档案</h1>
      <p class="muted">
        只填写规则判断真正需要的信息。图片识别只提供可修改的建议，不会自动确认物种、体型或服务犬身份。
      </p>
    </header>

    <p v-if="loadingSession" class="muted pet-new-loading">正在确认登录状态…</p>
    <StateMessage
      v-else-if="!signedIn"
      kind="PERMISSION_DENIED"
      title="登录后新建宠物档案"
      description="宠物档案属于你的私有查询上下文。公开场所规则与现场事实仍可免登录浏览。"
    >
      <template #action>
        <RouterLink
          class="btn primary"
          :to="{ name: 'onboarding', query: { next: '/pet/new' } }"
        >
          登录 / 注册
        </RouterLink>
      </template>
    </StateMessage>

    <form v-else class="pet-new-form" @submit.prevent="save">
      <section class="pet-new-section">
        <h2>基本信息</h2>
        <label class="pet-new-field">
          <span>名字</span>
          <input v-model="pet.display_name" data-testid="pet-name" placeholder="如：豆豆" />
        </label>
        <label class="pet-new-field">
          <span>物种</span>
          <select v-model="pet.species" data-testid="pet-species">
            <option value="dog">犬</option>
            <option value="cat">猫</option>
            <option value="other">其他</option>
          </select>
        </label>
        <label class="pet-new-field">
          <span>品种（可选）</span>
          <input v-model="pet.breed_text" placeholder="如：柴犬" />
        </label>
        <label class="pet-new-field">
          <span>体重 kg（可选）</span>
          <input
            v-model="pet.weight_kg"
            type="number"
            step="0.1"
            min="0"
            data-testid="pet-weight"
          />
          <small>只有规则涉及体重限制时才会使用；不填写就保持未知。</small>
        </label>
      </section>

      <section class="pet-new-section">
        <h2>服务犬身份</h2>
        <p class="muted">仅由你自行声明；平台不会通过照片或品种推断。</p>
        <select v-model="serviceRole" data-testid="pet-service-role">
          <option value="none">普通宠物</option>
          <option value="working">服务犬（在役）</option>
          <option value="in_training">服务犬（训练中）</option>
        </select>
      </section>

      <PetImageSuggestion
        @suggest="
          (species, breed) => {
            pet.species = species;
            pet.breed_text = breed;
          }
        "
      />

      <div class="pet-new-actions">
        <button
          class="primary"
          type="submit"
          :disabled="!pet.display_name || saving"
          data-testid="pet-save"
        >
          {{ saving ? "保存中…" : "保存并设为本次对象" }}
        </button>
        <RouterLink class="btn-inline" to="/pets">取消</RouterLink>
      </div>

      <p v-if="error" class="pet-new-feedback">{{ error }}</p>
    </form>
  </AppShell>
</template>

<style scoped>
.pet-new-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.pet-new-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.pet-new-form {
  max-width: 680px;
}

.pet-new-loading {
  margin: var(--pa-space-5) 0 0;
}

.pet-new-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.pet-new-section h2 {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.pet-new-section > p {
  margin: 0 0 var(--pa-space-3);
}

.pet-new-field {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  margin-bottom: var(--pa-space-3);
  font-size: var(--pa-font-size-md);
}

.pet-new-field:last-child {
  margin-bottom: 0;
}

.pet-new-field input,
.pet-new-field select,
.pet-new-section select {
  margin: 0;
}

.pet-new-field small {
  color: var(--pa-color-text-muted);
  line-height: var(--pa-line-height-20);
}

.pet-new-actions {
  display: flex;
  align-items: center;
  gap: var(--pa-space-4);
  padding-top: var(--pa-space-5);
}

.pet-new-feedback {
  margin: var(--pa-space-3) 0 0;
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .pet-new-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .pet-new-actions .btn-inline {
    min-height: var(--pa-size-control-md);
    display: inline-flex;
    align-items: center;
  }
}
</style>
