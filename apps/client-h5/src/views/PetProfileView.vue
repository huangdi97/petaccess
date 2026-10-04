<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { client, session, ApiError, type PetView } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import PetProfileEditor from "../components/pets/PetProfileEditor.vue";
import PetProfileHeader from "../components/pets/PetProfileHeader.vue";
import PetProfileList from "../components/pets/PetProfileList.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { useOnline } from "../composables/useOnline";
import { emptyPetDraft, type PetDraft } from "../consumer/petProfileModel";

const pets = ref<PetView[]>([]);
const loading = ref(true);
const loaded = ref(false);
const error = ref("");
const notice = ref("");
const busy = ref(false);
const editing = ref<string | null>(null);
const draft = ref<PetDraft>(emptyPetDraft());
const { online } = useOnline();

const isNew = computed(() => editing.value === "new");
const activeId = computed(() => session.activePet?.id ?? null);
async function load() {
  error.value = "";
  loading.value = true;
  try {
    await session.restore();
    if (!session.signedIn) return;
    pets.value = await client.myPets();
    if (session.activePet && !pets.value.some((p) => p.id === session.activePet?.id)) {
      session.activePet = null;
    }
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    loaded.value = true;
    loading.value = false;
  }
}

function startNew() {
  editing.value = "new";
  notice.value = "";
  draft.value = emptyPetDraft();
}

function startEdit(pet: PetView) {
  editing.value = pet.id;
  notice.value = "";
  draft.value = {
    display_name: pet.display_name,
    species: pet.species,
    breed_text: pet.breed_text ?? "",
    weight_kg: pet.weight_kg != null ? String(pet.weight_kg) : "",
    shoulder_height_cm: pet.shoulder_height_cm != null ? String(pet.shoulder_height_cm) : "",
    service_role: pet.service_role,
  };
}

async function save() {
  error.value = "";
  notice.value = "";
  if (!online.value) {
    error.value = "当前无网络连接，保存已暂停。";
    return;
  }
  busy.value = true;
  const body = {
    display_name: draft.value.display_name.trim(),
    species: draft.value.species,
    breed_text: draft.value.breed_text.trim() || null,
    weight_kg: draft.value.weight_kg ? Number(draft.value.weight_kg) : null,
    shoulder_height_cm: draft.value.shoulder_height_cm
      ? Number(draft.value.shoulder_height_cm)
      : null,
    service_role: draft.value.service_role,
  };
  try {
    if (isNew.value) {
      const created = await client.createPet(body);
      pets.value = [...pets.value, created];
      notice.value = `已创建「${created.display_name}」`;
    } else if (editing.value) {
      const updated = await client.updatePet(editing.value, body);
      pets.value = pets.value.map((p) => (p.id === updated.id ? updated : p));
      if (session.activePet?.id === updated.id) session.activePet = updated;
      notice.value = `已更新「${updated.display_name}」`;
    }
    editing.value = null;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : e instanceof Error ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function remove(pet: PetView) {
  if (!confirm(`删除宠物档案「${pet.display_name}」？此操作不可撤销。`)) return;
  error.value = "";
  busy.value = true;
  try {
    await client.deletePet(pet.id);
    pets.value = pets.value.filter((p) => p.id !== pet.id);
    if (session.activePet?.id === pet.id) session.activePet = null;
    notice.value = `已删除「${pet.display_name}」`;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

function setActive(pet: PetView) {
  session.activePet = pet;
  session.mode = "with_pet";
  notice.value = `本次查询对象已设为「${pet.display_name}」`;
}

onMounted(load);
</script>

<template>
  <AppShell>
    <PetProfileHeader
      :online="online"
      :signed-in="session.signedIn"
      :editing="Boolean(editing)"
      @create="startNew"
    />

    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage
      v-else-if="!session.signedIn"
      kind="PERMISSION_DENIED"
      description="宠物档案与账号绑定。登录后可新建、修改或删除档案。"
    >
      <template #action>
        <RouterLink class="btn primary" to="/onboarding">登录 / 注册</RouterLink>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="error && !loaded"
      kind="ERROR"
      :description="`未能取得宠物档案：${error}`"
    >
      <template #action><button class="primary" @click="load">重试</button></template>    </StateMessage>
    <template v-else>
      <p v-if="error" class="profile-feedback" data-testid="pet-error">{{ error }}</p>
      <p v-if="notice" class="profile-feedback" data-testid="pet-notice">{{ notice }}</p>

      <PetProfileEditor
        v-if="editing"
        v-model:draft="draft"
        :is-new="isNew"
        :busy="busy"
        @save="save"
        @cancel="editing = null"
      />
      <template v-else>
        <StateMessage
          v-if="!pets.length"
          kind="EMPTY"
          description="还没有宠物档案。没有档案也可以浏览公开规则；只有需要个体条件时才需要补充。"
        >
          <template #action>
            <button class="primary" data-testid="pet-empty-new" @click="startNew">新建档案</button>
          </template>
        </StateMessage>
        <PetProfileList
          v-else
          :pets="pets"
          :active-id="activeId"
          :busy="busy"
          @activate="setActive"
          @edit="startEdit"
          @remove="remove"
        />
        <p class="profile-note muted">
          服务犬使用独立通行规则。需要查询时，直接在“当前查询”中切换到服务犬视角。
        </p>
      </template>
    </template>
  </AppShell>
</template>

<style scoped>
.profile-feedback {
  margin: var(--pa-space-3) 0 0;
  color: var(--pa-color-text-secondary);
}

.profile-note {
  margin: var(--pa-space-5) 0 0;
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
</style>
