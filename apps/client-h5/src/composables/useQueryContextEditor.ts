import { computed, onMounted, ref } from "vue";
import { client, session, type PetView, type QueryMode } from "@petaccess/client-core";
import { presentDescription } from "../errors";
import { querySummaryLabel } from "../consumer/queryContext";

type EditableQueryMode = Extract<QueryMode, "with_pet" | "service_dog">;

export const QUERY_MODES: { key: EditableQueryMode; label: string; hint: string }[] = [
  { key: "with_pet", label: "普通携带", hint: "按当前宠物档案或默认普通犬查询" },
  { key: "service_dog", label: "服务犬通行", hint: "按用户声明的服务犬角色查询适用规则" },
];

export const SERVICE_ROLES = [
  { key: "", label: "角色未细分" },
  { key: "guide_dog", label: "导盲犬" },
  { key: "hearing_dog", label: "助听犬" },
  { key: "assistance_dog", label: "辅助犬" },
  { key: "other_service_dog", label: "其他服务犬" },
] as const;

export function useQueryContextEditor() {
  const open = ref(false);
  const pets = ref<PetView[]>([]);
  const petsLoaded = ref(false);
  const loadingPets = ref(false);
  const petError = ref("");
  const summary = computed(() => querySummaryLabel());

  // Query Context is global chrome. Restore persisted subject/role even on
  // secondary routes that do not otherwise need account data.
  onMounted(() => {
    void session.restore();
  });

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

  return {
    open,
    pets,
    loadingPets,
    petError,
    summary,
    selectMode,
    selectPet,
    selectServiceRole,
    openEditor,
  };
}
