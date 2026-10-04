<script setup lang="ts">
import { ref } from "vue";
import { animalScopeLabel } from "../../consumer/labels";

const emit = defineEmits<{ suggest: [species: string, breed: string] }>();
const input = ref<HTMLInputElement | null>(null);
const fileName = ref("");
const message = ref("");

async function onPickImage(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  fileName.value = file.name;

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
    <input
      ref="input"
      class="pet-image-input"
      type="file"
      accept="image/*"
      data-testid="pet-photo"
      @change="onPickImage"
    />
    <div class="pet-image-picker">
      <button type="button" class="pet-image-button" @click="input?.click()">选择照片</button>
      <span class="muted">{{ fileName || "尚未选择照片" }}</span>
    </div>
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

.pet-image-input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
}

.pet-image-picker {
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
}

.pet-image-button {
  min-height: var(--pa-size-control-md);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
  padding: 0 var(--pa-space-3);
  cursor: pointer;
}

.pet-image-button:hover,
.pet-image-button:focus-visible {
  border-color: var(--pa-color-accent);
}

.pet-image-feedback {
  margin-top: var(--pa-space-3) !important;
  color: var(--pa-color-text-secondary);
}

@media (max-width: 767px) {
  .pet-image-picker {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--pa-space-2);
  }
}
</style>
