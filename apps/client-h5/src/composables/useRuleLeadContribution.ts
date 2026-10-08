import { computed, ref, type Ref } from "vue";
import { client } from "@petaccess/client-core";
import { evidenceRefs, proximity } from "../components/contribute/contributeSupport";
import {
  ruleLeadConditionLabel,
  ruleLeadEffectLabel,
  ruleLeadSourceBasisLabel,
} from "../components/contribute/ruleLeadCopy";
import { presentDescription } from "../errors";

export type RuleIntent = "still_valid" | "changed" | "signage" | "new_lead";
export type RuleEffect = "allowed" | "restricted" | "conditional" | "";
export type RuleAnimalScope = "ordinary_pet" | "dog" | "cat" | "other";

interface RuleLeadProps {
  placeId: string;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
}

export interface RuleLeadController {
  intent: Ref<RuleIntent>;
  effect: Ref<RuleEffect>;
  animalScope: Ref<RuleAnimalScope>;
  zone: Ref<string>;
  conditions: Ref<string[]>;
  sourceBasis: Ref<string>;
  mediaId: Ref<string | null>;
  ocrText: Ref<string>;
  uploading: Ref<boolean>;
  busy: Ref<boolean>;
  error: Ref<string>;
  selectedRuleId: Ref<string>;
  canSubmit: Readonly<Ref<boolean>>;
  submit: () => Promise<void>;
}

export function useRuleLeadContribution(
  props: RuleLeadProps,
  onDone: (message: string) => void,
): RuleLeadController {
  const intent = ref<RuleIntent>("new_lead");
  const effect = ref<RuleEffect>("");
  const animalScope = ref<RuleAnimalScope>("ordinary_pet");
  const zone = ref("");
  const conditions = ref<string[]>([]);
  const sourceBasis = ref("");
  const mediaId = ref<string | null>(null);
  const ocrText = ref("");
  const uploading = ref(false);
  const busy = ref(false);
  const error = ref("");
  const selectedRuleId = ref("");

  const needsRuleDescription = computed(
    () => intent.value === "changed" || intent.value === "new_lead",
  );
  const needsExistingRule = computed(
    () => intent.value === "still_valid" || intent.value === "changed",
  );
  const canSubmit = computed(
    () =>
      props.online &&
      props.signedIn &&
      !busy.value &&
      !uploading.value &&
      (!needsExistingRule.value || Boolean(selectedRuleId.value)) &&
      (!needsRuleDescription.value || (Boolean(effect.value) && Boolean(sourceBasis.value))) &&
      (intent.value !== "signage" || Boolean(mediaId.value)),
  );

  async function submitSignage() {
    const rawText = ocrText.value.trim()
      ? `规则牌 / 公告证据；OCR 待人工核对：${ocrText.value.trim().slice(0, 500)}`
      : "规则牌 / 公告证据；OCR 未取得或未完成。";
    await client.contributeRuleLead(props.placeId, {
      zone_id: zone.value || null,
      raw_text: rawText,
      source_basis: "onsite_signage",
      media_id: mediaId.value,
      ...proximity(),
    });
    onDone(
      "规则牌证据已进入规则候选提取与人工审核流程。系统不会因为照片或 OCR 自动猜测允许 / 禁止，也不会自动发布正式规则。",
    );
  }

  async function submitExistingConfirmation() {
    await client.verify({
      place_id: props.placeId,
      zone_id: zone.value || null,
      rule_id: selectedRuleId.value || null,
      event_type: "rule_confirmed",
      result: "still_valid",
      note: "现场核验：页面规则仍然如此",
      evidence_refs: evidenceRefs(mediaId.value),
      ...proximity(),
    });
    onDone("核验已提交。它会补充该规则的核验记录，但不会改写规则内容。");
  }

  async function submitLead() {
    const canonicalEffect = effect.value === "restricted" ? "prohibited" : effect.value;
    if (!canonicalEffect) return;
    const zoneLabel = props.zones.find((item) => item.id === zone.value)?.name ?? "全场 / 不确定";
    const evidenceNote = ocrText.value.trim()
      ? `；OCR 待人工核对：${ocrText.value.trim().slice(0, 300)}`
      : "";
    await client.contributeRuleLead(props.placeId, {
      zone_id: zone.value || null,
      animal_scope: animalScope.value,
      effect: canonicalEffect,
      proposed_conditions: conditions.value,
      raw_text:
        `规则线索：${ruleLeadEffectLabel(effect.value)}；来源：${ruleLeadSourceBasisLabel(sourceBasis.value)}；` +
        `区域：${zoneLabel}；条件：${ruleLeadConditionLabel(conditions.value)}${evidenceNote}`,
      source_basis:
        ["onsite_signage", "staff_statement", "official_online", "other", "uncertain"].includes(
          sourceBasis.value,
        )
          ? (sourceBasis.value as
              | "onsite_signage"
              | "staff_statement"
              | "official_online"
              | "other"
              | "uncertain")
          : "uncertain",
      media_id: mediaId.value,
      current_rule_id: intent.value === "changed" ? selectedRuleId.value || null : null,
      ...proximity(),
    });
    onDone(
      intent.value === "changed"
        ? "规则变化线索已提交，进入人工复核；现有正式规则不会自动改写。"
        : "新规则线索已提交，进入人工复核；核验并进入正式候选流程前不会改变准入结论。",
    );
  }

  async function submit() {
    if (!canSubmit.value || !props.placeId) return;
    error.value = "";
    busy.value = true;
    try {
      if (needsExistingRule.value && !selectedRuleId.value) {
        error.value = "请选择这次要确认或修正的具体规则。";
        return;
      }
      if (intent.value === "signage" && !mediaId.value) {
        error.value = "请先上传规则牌或公告照片。";
        return;
      }
      if (intent.value === "signage") await submitSignage();
      else if (intent.value === "still_valid") await submitExistingConfirmation();
      else await submitLead();
    } catch (cause) {
      error.value = presentDescription(cause);
    } finally {
      busy.value = false;
    }
  }

  return {
    intent,
    effect,
    animalScope,
    zone,
    conditions,
    sourceBasis,
    mediaId,
    ocrText,
    uploading,
    busy,
    error,
    selectedRuleId,
    canSubmit,
    submit,
  };
}
