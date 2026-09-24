<script setup lang="ts">
/**
 * PlaceListItem — 场所列表行 (search / home results).
 *
 * Wraps PaListRow with place facts. The rule verdict comes from the answer
 * adapter (`../../answer`), never from raw rule rows.
 */
import { computed } from "vue";
import { placeTypeLabel, type AccessAnswer, type PlaceSummary } from "@petaccess/client-core";
import { answerStatusKey } from "../../answer";
import PaListRow from "../ui/PaListRow.vue";
import RuleStatus from "./RuleStatus.vue";
import FreshnessStatus from "./FreshnessStatus.vue";

const props = withDefaults(
  defineProps<{
    place: PlaceSummary;
    to?: string;
    answer?: AccessAnswer | null;
    showRuleStatus?: boolean;
  }>(),
  { to: undefined, answer: null, showRuleStatus: true },
);

defineOptions({ name: "PlaceListItem" });

const description = computed(() => {
  const address = props.place.canonical_address ?? "地址待补充";
  return `${placeTypeLabel(props.place.place_type)} · ${address}`;
});

const meta = computed(() =>
  props.place.rule_count > 0 ? `生效规则 ${props.place.rule_count} 条` : "尚未收录规则",
);

const showRule = computed(() => props.showRuleStatus && Boolean(props.answer));
const showFreshness = computed(() => Boolean(props.place.last_verified_at));
</script>

<template>
  <PaListRow :title="place.canonical_name" :description="description" :meta="meta" :to="to">
    <template #trailing>
      <span v-if="showRule || showFreshness" class="place-list-item__trailing">
        <RuleStatus v-if="showRule" :semantic="answerStatusKey(answer)" />
        <FreshnessStatus v-if="showFreshness" :last-verified-at="place.last_verified_at" />
      </span>
    </template>
  </PaListRow>
</template>

<style scoped>
.place-list-item__trailing {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--pa-space-1);
}
</style>
