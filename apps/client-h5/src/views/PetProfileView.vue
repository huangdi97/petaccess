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

    <SkeletonList v-if="loading" :rows="3" />

    <StateMessage
      v-else-if="!session.signedIn"
      kind="PERMISSION_DENIED"
      description="宠物档案与账号绑定。登录后可新建、修改或删除档案。"
    >
      <template #action>
        <RouterLink to="/onboarding"><button class="primary">登录 / 注册</button></RouterLink>
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
      <div v-if="error" class="panel" data-testid="pet-error">{{ error }}</div>
      <div v-if="notice" class="panel" data-testid="pet-notice">{{ notice }}</div>

      <!-- ---------------------------------------------------------- editor -->
      <div v-if="editing" class="panel" data-testid="pet-editor">
        <h1>{{ isNew ? "新建宠物档案" : "编辑宠物档案" }}</h1>
        <p class="muted" style="margin-top: 4px">
          档案仅用于规则匹配。空缺字段保持未知，不会被视为满足或不满足条件。
        </p>

        <label>名称（可选，便于你区分多个档案）</label>
        <input v-model="draft.display_name" data-testid="pet-name" placeholder="如：豆豆" />

        <label>物种</label>
        <select v-model="draft.species" data-testid="pet-species">
          <option value="dog">犬</option>
          <option value="cat">猫</option>
          <option value="other">其他</option>
        </select>

        <label>品种（可选）</label>
        <input v-model="draft.breed_text" data-testid="pet-breed" placeholder="如：柴犬" />

        <label>体重 kg（规则涉及体重上限时必需；留空则返回「需补充」而非猜测）</label>
        <input
          v-model="draft.weight_kg"
          type="number"
          step="0.1"
          min="0"
          max="300"
          data-testid="pet-weight"
        />

        <label>肩高 cm（规则涉及肩高限制时必需；留空则保持未知）</label>
        <input
          v-model="draft.shoulder_height_cm"
          type="number"
          step="1"
          min="0"
          max="250"
          data-testid="pet-shoulder"
        />

        <!-- service role lives in its own block: it is a declaration, not an attribute -->
        <div class="panel" style="margin-top: 12px" data-testid="pet-service-block">
          <div style="font-weight: 600">服务犬身份</div>
          <p class="muted" style="margin-top: 4px">
            仅由你自行声明。平台不凭照片、品种或体型认定服务犬身份，也不据此改变场所规则。
          </p>
          <select v-model="draft.service_role" data-testid="pet-service-role">
            <option value="none">普通宠物</option>
            <option value="working">服务犬（在役）</option>
            <option value="in_training">服务犬（训练中）</option>
            <option value="retired">服务犬（已退役）</option>
          </select>
        </div>

        <div class="row" style="margin-top: 16px">
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
      </div>

      <!-- ------------------------------------------------------------ list -->
      <template v-else>
        <div class="panel">
          <div class="row" style="justify-content: space-between">
            <h1 style="margin: 0">宠物档案</h1>
            <button class="pill" data-testid="pet-new" @click="startNew">新建</button>
          </div>
        </div>

        <StateMessage
          v-if="!pets.length"
          kind="EMPTY"
          description="还没有宠物档案。没有档案时，涉及体重/体型条件的规则会返回「需补充」。"
        >
          <template #action>
            <button class="primary" data-testid="pet-empty-new" @click="startNew">新建档案</button>
          </template>
        </StateMessage>

        <div v-for="p in pets" :key="p.id" class="panel" data-testid="pet-card">
          <div class="row" style="justify-content: space-between">
            <strong>{{ p.display_name }}</strong>
            <span v-if="activeId === p.id" class="pill active" data-testid="pet-active">
              本次对象
            </span>
          </div>
          <div class="muted" style="margin-top: 6px">
            {{ SPECIES_LABELS[p.species] ?? p.species }}
            <template v-if="p.breed_text"> · {{ p.breed_text }}</template>
            <template v-if="p.weight_kg != null"> · {{ p.weight_kg }}kg</template>
            <template v-if="p.shoulder_height_cm != null">
              · 肩高 {{ p.shoulder_height_cm }}cm</template
            >
          </div>
          <div
            v-if="p.service_role !== 'none'"
            class="muted"
            style="margin-top: 4px"
            data-testid="pet-service-declared"
          >
            服务犬（用户声明）· {{ SERVICE_LABELS[p.service_role] ?? p.service_role }}
          </div>
          <div
            v-if="p.weight_kg == null || p.shoulder_height_cm == null"
            class="muted"
            style="margin-top: 4px"
          >
            尚未填写{{ p.weight_kg == null ? "体重" : ""
            }}{{ p.weight_kg == null && p.shoulder_height_cm == null ? "与" : ""
            }}{{ p.shoulder_height_cm == null ? "肩高" : "" }}：相关规则将返回「需补充」。
          </div>
          <div class="row" style="margin-top: 10px">
            <button
              v-if="activeId !== p.id"
              class="pill"
              :data-testid="`pet-use-${p.id}`"
              @click="setActive(p)"
            >
              设为本次对象
            </button>
            <button class="pill" :data-testid="`pet-edit-${p.id}`" @click="startEdit(p)">
              编辑
            </button>
            <button
              class="pill"
              :disabled="busy"
              :data-testid="`pet-delete-${p.id}`"
              @click="remove(p)"
            >
              删除
            </button>
          </div>
        </div>

        <div class="panel">
          <div class="muted">
            服务犬适用独立通行规则（服务犬 ≠ 普通宠物），判定不在此档案内合并；
            请在地图页切换到「服务犬」查询模式查看。
          </div>
        </div>
      </template>
    </template>
  </AppShell>
</template>
