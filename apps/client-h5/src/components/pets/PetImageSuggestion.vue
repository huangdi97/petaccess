<script setup lang="ts">
import { ref } from "vue";
import { animalScopeLabel } from "../../consumer/labels";

const emit = defineEmits<{ suggest: [species: string, breed: string] }>();
const message = ref("");

async function onPickImage(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;

  const form = new FormData();
  form.append("image", file);
  try {
    const response = await fetch("/api/v1/ai/pet-vision", {
      method: "POST",
      headers: { Authorization: `Bearer ${localStorage.getItem("pa_token")}` },
      body: form,
    });
    const data = await response.json();
    if (!response.ok) {
      message.value = "图片建议暂不可用，直接手填即可";
      return;
    }

    const breed = data.breed_candidates?.[0] ?? "";
    const breedText = (data.breed_candidates ?? []).join(" / ");
    emit("suggest", data.species, breed);
    message.value = `图片建议：${animalScopeLabel(data.species)}${breedText ? ` · ${breedText}` : ""}（请确认或修改）`;
  } catch {
    message.value = "图片建议暂不可用，直接手填即可";
  }
}
</script>

<template>
  <section class="pet-image-section">
    <h2>图片建议（可选）</h2>
    <p class="muted">上传照片后可以获得物种/品种填写建议；你仍可以直接手填并修改。</p>
    <input type="file" accept="image/*" data-testid="pet-photo" @change="onPickImage" />
    <p v-if="message" class="pet-image-feedback" data-testid="ai-suggestion">{{ message }}</p>
  </section>
</template>

<style scoped>
.pet-image-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.pet-image-section h2 {
  margin: 0 0 var(--pa-space-3);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.pet-image-section p {
  margin: 0 0 var(--pa-space-3);
}

.pet-image-feedback {
  margin-top: var(--pa-space-3) !important;
  color: var(--pa-color-text-secondary);
}
</style>
