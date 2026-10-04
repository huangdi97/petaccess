<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { client, session, ApiError, type PetView } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { useOnline } from "../composables/useOnline";

/**
 * Pet Profile (UI_UX_IMPLEMENTATION_SPEC §6).
 *
 * Field notes that are product rules, not styling:
 * - `service_role` is user-declared only. The platform never infers it from a
 *   photo or from a breed, and it is edited in a visually separate block so it
 *   is never mixed with ordinary attributes (design #19).
 * - weight / shoulder height are only collected because some rules are
 *   conditional on them. Leaving them empty keeps those rules UNKNOWN rather
 *   than guessing, so we never prefill a default.
 * - AI photo recognition produces a *suggestion* the user confirms; it never
 *   writes a confirmed value on its own (ADR-005).
 */

const pets = ref<PetView[]>([]);
const loading = ref(true);
const loaded = ref(false);
const error = ref("");
const notice = ref("");
const busy = ref(false);
const { online } = useOnline();

const editing = ref<string | null>(null); // pet id, or "new"
const draft = ref({
  display_name: "",
  species: "dog",
  breed_text: "",
  weight_kg: "",
  shoulder_height_cm: "",
  service_role: "none",
});

const SPECIES_LABELS: Record<string, string> = { dog: "犬", cat: "猫", other: "其他" };
const SERVICE_LABELS: Record<string, string> = {
  none: "普通宠物",
  working: "服务犬（在役）",
  trained: "服务犬（训练中）",
  in_training: "服务犬（训练中）",
  retired: "服务犬（已退役）",
};

const isNew = computed(() => editing.value === "new");
const activeId = computed(() => session.activePet?.id ?? null);

async function load() {
  error.value = "";
  loading.value = true;
  try {
    await session.restore();
    if (!session.signedIn) return;
    pets.value = await client.myPets();
    // keep the active pet fresh if it still exists
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
  draft.value = {
    display_name: "",
    species: "dog",
    breed_text: "",
    weight_kg: "",
    shoulder_height_cm: "",
    service_role: "none",
  };
}

function startEdit(p: PetView) {
  editing.value = p.id;
  notice.value = "";
  draft.value = {
    display_name: p.display_name,
    species: p.species,
    breed_text: p.breed_text ?? "",
    weight_kg: p.weight_kg != null ? String(p.weight_kg) : "",
    shoulder_height_cm: p.shoulder_height_cm != null ? String(p.shoulder_height_cm) : "",
    service_role: p.service_role,
  };
}

function cancel() {
  editing.value = null;
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
      if (session.activePet?.id === updated.id) {
        session.activePet = updated;
      }
      notice.value = `已更新「${updated.display_name}」`;
    }
    editing.value = null;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : e instanceof Error ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function remove(p: PetView) {
  if (!confirm(`删除宠物档案「${p.display_name}」？此操作不可撤销。`)) return;
  error.value = "";
  busy.value = true;
  try {
    await client.deletePet(p.id);
    pets.value = pets.value.filter((x) => x.id !== p.id);
    if (session.activePet?.id === p.id) session.activePet = null;
    notice.value = `已删除「${p.display_name}」`;
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

function setActive(p: PetView) {
  session.activePet = p;
  session.mode = "with_pet";
  notice.value = `本次查询对象已设为「${p.display_name}」`;
}

onMounted(load);
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：可查看已加载档案，保存操作已暂停。</span>
    </div>

    <header class="profile-head">
      <div>
        <h1>宠物档案</h1>
        <p class="muted">
          只填写规则判断真正需要的信息；留空字段保持未知，不会被系统猜测。
        </p>
      </div>
      <button
        v-if="session.signedIn && !editing"
        type="button"
        class="profile-head__action"
        data-testid="pet-new"
        @click="startNew"
      >
        新建档案
      </button>
    </header>

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
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>

    <template v-else>
      <p v-if="error" class="profile-feedback" data-testid="pet-error">{{ error }}</p>
      <p v-if="notice" class="profile-feedback" data-testid="pet-notice">{{ notice }}</p>

      <section v-if="editing" class="profile-editor" data-testid="pet-editor">
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
          <p class="muted">
            仅由你自行声明。平台不凭照片、品种或体型认定服务犬身份。
          </p>
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
            :disabled="!draft.display_name.trim() || busy || !online"
            data-testid="pet-save"
            @click="save"
          >
            {{ busy ? "保存中…" : "保存" }}
          </button>
          <button :disabled="busy" @click="cancel">取消</button>
        </div>
      </section>

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

        <section v-else class="profile-list" aria-label="宠物档案列表">
          <article v-for="p in pets" :key="p.id" class="profile-row" data-testid="pet-card">
            <div class="profile-row__head">
              <div>
                <strong class="profile-row__name">{{ p.display_name }}</strong>
                <span v-if="activeId === p.id" class="profile-row__active" data-testid="pet-active">
                  本次使用中
                </span>
              </div>
              <div class="profile-row__actions">
                <button
                  v-if="activeId !== p.id"
                  :data-testid="`pet-use-${p.id}`"
                  @click="setActive(p)"
                >
                  设为本次对象
                </button>
                <button :data-testid="`pet-edit-${p.id}`" @click="startEdit(p)">编辑</button>
                <button
                  :disabled="busy"
                  :data-testid="`pet-delete-${p.id}`"
                  @click="remove(p)"
                >
                  删除
                </button>
              </div>
            </div>

            <p class="muted profile-row__meta">
              {{ SPECIES_LABELS[p.species] ?? "其他" }}
              <template v-if="p.breed_text"> · {{ p.breed_text }}</template>
              <template v-if="p.weight_kg != null"> · {{ p.weight_kg }} kg</template>
              <template v-if="p.shoulder_height_cm != null">
                · 肩高 {{ p.shoulder_height_cm }} cm
              </template>
            </p>

            <p
              v-if="p.service_role !== 'none'"
              class="muted profile-row__meta"
              data-testid="pet-service-declared"
            >
              {{ SERVICE_LABELS[p.service_role] ?? "服务犬（用户声明）" }}
            </p>

            <p
              v-if="p.weight_kg == null || p.shoulder_height_cm == null"
              class="profile-row__missing"
            >
              尚未填写{{ p.weight_kg == null ? "体重" : "" }}{{
                p.weight_kg == null && p.shoulder_height_cm == null ? "与" : ""
              }}{{ p.shoulder_height_cm == null ? "肩高" : "" }}；相关规则需要时再补充即可。
            </p>
          </article>
        </section>

        <p class="profile-note muted">
          服务犬使用独立通行规则。需要查询时，直接在“当前查询”中切换到服务犬视角。
        </p>
      </template>
    </template>
  </AppShell>
</template>

<style scoped>
.profile-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.profile-head p {
  max-width: 620px;
  margin: var(--pa-space-2) 0 0;
}

.profile-head__action {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  min-height: var(--pa-size-control-md);
  cursor: pointer;
}

.profile-feedback {
  margin: var(--pa-space-3) 0 0;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
  color: var(--pa-color-text-secondary);
}

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
.profile-field select {
  margin: 0;
}

.profile-field small {
  color: var(--pa-color-text-muted);
  line-height: var(--pa-line-height-20);
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
  margin: 0;
}

.profile-actions {
  display: flex;
  gap: var(--pa-space-2);
  padding-top: var(--pa-space-5);
}

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

.profile-note {
  margin: var(--pa-space-5) 0 0;
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

@media (max-width: 767px) {
  .profile-head {
    flex-direction: column;
  }

  .profile-form-grid {
    grid-template-columns: 1fr;
  }

  .profile-row__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .profile-row__actions {
    gap: var(--pa-space-3);
  }
}
</style>
