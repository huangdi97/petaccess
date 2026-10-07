/**
 * Consumer query-context presentation.
 *
 * One place-level query is shared across Home / Search / Map / Place. These
 * labels intentionally mirror currentQueryContext(): service-dog mode is
 * always a dog query and a declared role is user-provided, never inferred.
 */
import { session } from "@petaccess/client-core";

const SERVICE_ROLE_LABELS: Record<string, string> = {
  guide_dog: "导盲犬",
  hearing_dog: "助听犬",
  assistance_dog: "辅助犬",
  other_service_dog: "其他服务犬",
};

export function queryAnimalLabel(): string {
  if (session.mode === "service_dog") {
    const role = session.declaredRole ?? session.activePet?.declared_role ?? "";
    return SERVICE_ROLE_LABELS[role] ?? "服务犬";
  }
  const species = session.activePet?.species ?? "dog";
  return species === "dog" ? "普通犬" : species === "cat" ? "猫" : "其他宠物";
}

export function querySubjectLabel(): string {
  if (session.mode === "service_dog") {
    const role = session.declaredRole ?? session.activePet?.declared_role ?? "";
    return SERVICE_ROLE_LABELS[role] ?? "服务犬（角色未细分）";
  }

  const animal = queryAnimalLabel();
  if (session.mode === "with_pet" && session.activePet) {
    return `${session.activePet.display_name}（${animal}）`;
  }
  if (session.mode === "rules_only") return `规则视角 · ${animal}`;
  if (session.mode === "restrictions") return `限制视角 · ${animal}`;
  return animal;
}

export function querySummaryLabel(): string {
  return `${querySubjectLabel()} · 进入 · 公共区域`;
}
