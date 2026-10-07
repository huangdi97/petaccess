<script setup lang="ts">
/**
 * QueryContextBar — one real query primitive shared by Home/Search/Map/Place.
 *
 * The editor only exposes fields that truly alter the CoexistenceSnapshot
 * request. Pet selection and service-dog role are real query inputs; action
 * and place-level scope are shown explicitly as fixed for the current
 * Consumer question instead of being fake controls.
 */
import { computed, ref } from "vue";
import { client, session, type PetView, type QueryMode } from "@petaccess/client-core";
import PaDialog from "../ui/PaDialog.vue";
import { presentDescription } from "../../errors";
import { querySummaryLabel } from "../../consumer/queryContext";

defineOptions({ name: "QueryContextBar" });

const open = ref(false);
const pets = ref<PetView[]>([]);
const petsLoaded = ref(false);
const loadingPets = ref(false);
const petError = ref("");

type EditableQueryMode = Extract<QueryMode, "with_pet" | "service_dog">;

const MODES: { key: EditableQueryMode; label: string; hint: string }[] = [
  { key: "with_pet", label: "普通携带", hint: "按当前宠物档案或默认普通犬查询" },
  { key: "service_dog", label: "服务犬通行", hint: "按用户声明的服务犬角色查询适用规则" },
];

const SERVICE_ROLES = [
  { key: "", label: "角色未细分" },
  { key: "guide_dog", label: "导盲犬" },
  { key: "hearing_dog", label: "助听犬" },
  { key: "assistance_dog", label: "辅助犬" },
  { key: "other_service_dog", label: "其他服务犬" },
] as const;

const summary = computed(() => querySummaryLabel());

async function openEditor() {
  open.value = true;
  petError.value = "";
  if (petsLoaded.value || loadingPets.value) return;
  loadingPets.value = true;
  try {
    await session.restore();
    pets.value = session.signedIn ? await client.myPets() : [];
    petsLoaded.value = true;
  } catch (error) {
    petError.value = presentDescription(error);
  } finally {
    loadingPets.value = false;
  }
}

function selectMode(mode: EditableQueryMode) {
  session.mode = mode;
  if (mode !== "service_dog") session.setDeclaredRole(null);
}

function selectPet(pet: PetView) {
  session.setActivePet(pet);
  session.setDeclaredRole(null);
  session.mode = pet.service_role === "working" ? "service_dog" : "with_pet";
}

function selectServiceRole(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  session.setDeclaredRole(value || null);
  session.mode = "service_dog";
}
</script>

<template>
  <div class="query-context" data-testid="query-context" data-ui="query-context">
    <span class="query-context__label" aria-hidden="true">当前查询</span>
    <span class="query-context__value" data-testid="query-context-summary">{{ summary }}</span>
    <button
      type="button"
      class="query-context__edit"
      data-testid="query-context-edit"
      aria-label="修改当前查询"
      @click="openEditor"
    >
      修改
    </button>

    <PaDialog
      :open="open"
      :title="'当前查询：' + summary"
      description="这里只修改真正参与规则判断的查询条件。改变后，当前页面会按新的上下文重新取得 Rule + Reality 快照。"
      width="sm"
      @close="open = false"
    >
      <div class="query-context__form">
        <section class="query-context__section">
          <h3>携带情境</h3>
          <div class="query-context__modes" role="group" aria-label="查询视角">
            <button
              v-for="mode in MODES"
              :key="mode.key"
              type="button"
              class="query-context__mode"
              :class="{ 'query-context__mode--active': session.mode === mode.key }"
              :aria-pressed="session.mode === mode.key"
              @click="selectMode(mode.key)"
            >
              <strong>{{ mode.label }}</strong>
              <span>{{ mode.hint }}</span>
            </button>
          </div>
        </section>

        <section v-if="session.mode === 'with_pet'" class="query-context__section">
          <div class="query-context__section-head">
            <h3>本次查询对象</h3>
            <RouterLink v-if="session.signedIn" class="btn-inline" to="/pets" @click="open = false">
              管理档案 →
            </RouterLink>
          </div>
          <p v-if="loadingPets" class="muted query-context__hint">正在读取宠物档案…</p>
          <p v-else-if="petError" class="query-context__error">{{ petError }}</p>
          <div
            v-else-if="pets.length"
            class="query-context__pets"
            role="group"
            aria-label="宠物档案"
          >
            <button
              v-for="pet in pets"
              :key="pet.id"
              type="button"
              class="query-context__pet"
              :class="{ 'query-context__pet--active': session.activePet?.id === pet.id }"
              :aria-pressed="session.activePet?.id === pet.id"
              @click="selectPet(pet)"
            >
              <strong>{{ pet.display_name }}</strong>
              <span class="muted">
                {{ pet.species === "dog" ? "犬" : pet.species === "cat" ? "猫" : "其他宠物" }}
                <template v-if="pet.breed_text"> · {{ pet.breed_text }}</template>
                <template v-if="pet.weight_kg != null"> · {{ pet.weight_kg }} kg</template>
              </span>
            </button>
          </div>
          <p v-else class="muted query-context__hint">
            没有宠物档案时按普通犬查询；只有规则真正需要体重等条件时才需要补充档案。
          </p>
        </section>

        <section v-if="session.mode === 'service_dog'" class="query-context__section">
          <label class="query-context__field" for="query-service-role">
            <span>服务犬角色（用户声明）</span>
            <select
              id="query-service-role"
              :value="session.declaredRole ?? ''"
              data-testid="query-service-role"
              @change="selectServiceRole"
            >
              <option v-for="role in SERVICE_ROLES" :key="role.key" :value="role.key">
                {{ role.label }}
              </option>
            </select>
          </label>
          <p class="muted query-context__hint">
            导盲犬、助听犬和其他服务犬的适用规则可能不同；平台不会从照片推断或认证身份。
          </p>
        </section>

        <section class="query-context__section" aria-label="当前固定查询范围">
          <h3>当前问题</h3>
          <dl class="query-context__facts">
            <div>
              <dt>动作</dt>
              <dd>进入</dd>
            </div>
            <div>
              <dt>范围</dt>
              <dd>场所公共区域</dd>
            </div>
          </dl>
          <p class="muted query-context__hint">
            具体楼层、餐饮区或其他 Zone 的规则在场所档案中单独查看，不会被 place-level 结论覆盖。
          </p>
        </section>
      </div>

      <template #actions>
        <button
          type="button"
          class="primary"
          data-testid="query-context-done"
          @click="open = false"
        >
          完成
        </button>
      </template>
    </PaDialog>
  </div>
</template>

<style scoped src="./QueryContextBar.css"></style>
