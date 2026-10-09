<script setup lang="ts">
// @ui-form PetNewView — 表单页：提交流错误内联呈现，无列表加载（M3 E1 表单声明）。
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { client, session } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";
import { useOnline } from "../composables/useOnline";

const router = useRouter();
const pet = ref({
  display_name: "",
  species: "dog",
  breed_text: "",
  weight_kg: "",
  shoulder_height_cm: "",
});
const serviceRole = ref("none");
const error = ref("");
const saving = ref(false);
const loadingSession = ref(true);
const signedIn = ref(false);
const { online } = useOnline();
const canSave = computed(
  () => signedIn.value && online.value && !saving.value && pet.value.display_name.trim().length > 0,
);

onMounted(async () => {
  await session.restore();
  signedIn.value = session.signedIn;
  loadingSession.value = false;
});

async function save() {
  if (!signedIn.value) return;
  error.value = "";
  if (!online.value) {
    error.value = "当前无网络连接，宠物档案尚未保存。";
    return;
  }
  saving.value = true;
  try {
    const created = await client.createPet({
      display_name: pet.value.display_name.trim(),
      species: pet.value.species,
      breed_text: pet.value.breed_text || null,
      weight_kg: pet.value.weight_kg ? Number(pet.value.weight_kg) : null,
      shoulder_height_cm: pet.value.shoulder_height_cm
        ? Number(pet.value.shoulder_height_cm)
        : null,
      service_role: serviceRole.value,
    });
    session.setActivePet(created);
    session.setDeclaredRole(null);
    session.mode = created.service_role === "working" ? "service_dog" : "with_pet";
    router.push({ name: "home" });
  } catch (e) {
    error.value = presentDescription(e);
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
        只填写规则判断真正需要的信息。当前图片分析未接入真实服务；物种、体型与服务犬身份都由你确认。
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
        <RouterLink class="btn primary" :to="{ name: 'onboarding', query: { next: '/pet/new' } }">
          登录 / 注册
        </RouterLink>
      </template>
    </StateMessage>

    <form v-else class="pet-new-form" @submit.prevent="save">
      <p v-if="!online" class="pet-new-feedback" role="status">
        当前无网络连接：可以继续填写，恢复网络后再保存。
      </p>
      <section class="pet-new-section">
        <div class="pet-new-section__lead">
          <h2>基本信息</h2>
          <p class="muted">这些字段只在当前规则判断确实需要时参与查询。</p>
        </div>
        <div class="pet-new-grid">
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
          <label class="pet-new-field">
            <span>肩高 cm（可选）</span>
            <input
              v-model="pet.shoulder_height_cm"
              type="number"
              step="1"
              min="0"
              max="250"
              data-testid="pet-shoulder"
            />
            <small>只有规则涉及体型限制时才会使用；不填写就保持未知。</small>
          </label>
        </div>
      </section>

      <section class="pet-new-section">
        <h2>服务犬身份</h2>
        <p class="muted">仅由你自行声明；平台不会通过照片或品种推断。</p>
        <select v-model="serviceRole" data-testid="pet-service-role">
          <option value="none">普通宠物</option>
          <option value="working">服务犬（在役）</option>
          <option value="in_training">服务犬（训练中）</option>
          <option value="unknown">服务犬身份未确认</option>
        </select>
      </section>

      <div class="pet-new-actions">
        <button class="primary" type="submit" :disabled="!canSave" data-testid="pet-save">
          {{ saving ? "保存中…" : "保存并设为本次对象" }}
        </button>
        <RouterLink class="btn-inline" to="/pets">取消</RouterLink>
      </div>

      <p v-if="error" class="pet-new-feedback">{{ error }}</p>
    </form>
  </AppShell>
</template>

<style scoped src="./PetNewView.css"></style>
