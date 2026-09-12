<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { client, session } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";

const router = useRouter();
const pet = ref({ display_name: "", species: "dog", breed_text: "", weight_kg: "" });
const serviceRole = ref("none");
const error = ref("");
const aiMsg = ref("");
const aiFile = ref<File | null>(null);
const saving = ref(false);

async function onPickImage(e: Event) {
  const input = e.target as HTMLInputElement;
  aiFile.value = input.files?.[0] ?? null;
  if (!aiFile.value) return;
  // Mock VisionProvider suggestion → user confirms (design #5.2/#21):
  // never service dog, never confirmed weight/height from an image.
  const form = new FormData();
  form.append("image", aiFile.value);
  try {
    const res = await fetch("/api/v1/ai/pet-vision", {
      method: "POST",
      headers: { Authorization: `Bearer ${localStorage.getItem("pa_token")}` },
      body: form,
    });
    const data = await res.json();
    if (res.ok) {
      pet.value.species = data.species;
      pet.value.breed_text = data.breed_candidates[0] ?? "";
      aiMsg.value = `AI 建议：${data.species} · ${data.breed_candidates.join(" / ")}（请确认或修改）`;
    } else {
      aiMsg.value = `AI 建议不可用（${data.error?.message ?? "请手填"}），手填即可`;
    }
  } catch {
    aiMsg.value = "AI 建议不可用，手填即可";
  }
}

async function save() {
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
    <h1>新建宠物档案</h1>
    <p class="muted">档案仅用于规则匹配；AI 仅为建议，一切以你的确认为准。</p>
    <div class="panel">
      <label>宠物照片（可选 · AI 识别建议）</label>
      <input type="file" accept="image/*" data-testid="pet-photo" @change="onPickImage" />
      <div v-if="aiMsg" class="notice" data-testid="ai-suggestion">{{ aiMsg }}</div>

      <label>名字</label>
      <input v-model="pet.display_name" data-testid="pet-name" placeholder="如：豆豆" />
      <label>物种</label>
      <select v-model="pet.species" data-testid="pet-species">
        <option value="dog">犬</option>
        <option value="cat">猫</option>
        <option value="other">其他</option>
      </select>
      <label>品种</label>
      <input v-model="pet.breed_text" placeholder="如：柴犬" />
      <label>体重 kg（规则涉及体重上限时必需；不填会返回"需补充"而非猜测）</label>
      <input v-model="pet.weight_kg" type="number" step="0.1" min="0" data-testid="pet-weight" />
      <label>服务犬身份（仅用户声明；平台不凭照片认定）</label>
      <select v-model="serviceRole" data-testid="pet-service-role">
        <option value="none">普通宠物</option>
        <option value="working">服务犬（在役）</option>
        <option value="in_training">服务犬（训练中）</option>
      </select>

      <button
        class="primary block"
        style="margin-top: 16px"
        :disabled="!pet.display_name || saving"
        data-testid="pet-save"
        @click="save"
      >
        保存并设为本次对象
      </button>
      <div v-if="error" class="notice" style="color: var(--restricted)">{{ error }}</div>
    </div>
  </AppShell>
</template>
