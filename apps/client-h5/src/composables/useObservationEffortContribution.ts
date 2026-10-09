import { computed, ref, watch, type Ref } from "vue";
import { client } from "@petaccess/client-core";
import { presentDescription } from "../errors";
import { isoAt } from "../components/contribute/contributeSupport";

export type ObservationEffortSourceMode = "on_site_now" | "on_site_past";

export const OBSERVATION_EFFORT_OPTIONS = [
  { key: "lt_10_min", label: "不到 10 分钟" },
  { key: "min_10_30", label: "10–30 分钟" },
  { key: "min_30_120", label: "30 分钟 – 2 小时" },
  { key: "gt_120_min", label: "超过 2 小时" },
] as const;

interface EffortProps {
  placeId: string;
  online: boolean;
  signedIn: boolean;
  targetClaimId: string | null;
  initialZoneId: string | null;
  zones: { id: string; name: string }[];
}

export function useObservationEffortContribution(
  props: EffortProps,
  onDone: (message: string) => void,
): {
  sourceMode: Ref<ObservationEffortSourceMode>;
  occurredAt: Ref<string>;
  durationBucket: Ref<string>;
  zoneId: Ref<string>;
  busy: Ref<boolean>;
  error: Ref<string>;
  canSubmit: Readonly<Ref<boolean>>;
  submit: () => Promise<void>;
} {
  const sourceMode = ref<ObservationEffortSourceMode>("on_site_now");
  // A retrospective "not seen" report must never silently inherit today's
  // date. The time range is substantive evidence, not a UI convenience.
  const occurredAt = ref("");
  const today = new Date().toISOString().slice(0, 10);
  const durationBucket = ref("");
  const validInitialZone = () =>
    props.initialZoneId && props.zones.some((zone) => zone.id === props.initialZoneId)
      ? props.initialZoneId
      : "";
  const zoneId = ref(validInitialZone());
  const busy = ref(false);
  const error = ref("");
  watch(
    () => [props.placeId, props.initialZoneId, props.zones.map((zone) => zone.id).join("|")] as const,
    () => {
      // Route reuse is a transaction boundary. A zone from the previous place
      // is never a valid fallback scope for the new observation effort.
      zoneId.value = validInitialZone();
      durationBucket.value = "";
      occurredAt.value = "";
      error.value = "";
    },
  );

  const canSubmit = computed(
    () =>
      props.online &&
      props.signedIn &&
      !busy.value &&
      Boolean(durationBucket.value) &&
      (sourceMode.value !== "on_site_past" ||
        Boolean(occurredAt.value && occurredAt.value <= today)),
  );

  async function submit() {
    if (!canSubmit.value) return;
    const targetPlaceId = props.placeId;
    error.value = "";
    busy.value = true;
    try {
      const observedAt =
        sourceMode.value === "on_site_now" ? new Date().toISOString() : isoAt(occurredAt.value);
      await client.createRealityReport(targetPlaceId, {
        report: {
          origin: sourceMode.value,
          place_id: targetPlaceId,
          subject_place_id: targetPlaceId,
          place_match_state: "exact_place",
          place_match_evidence_types: ["user_confirmation"],
          observed_at: observedAt,
          time_evidence_state:
            sourceMode.value === "on_site_now" ? "live_device_time" : "exact_event_date",
          time_certainty: "exact",
          fact_evidence_state: "first_hand_no_media",
          privacy_state: "private",
        },
        candidates: [],
        effort: {
          place_id: targetPlaceId,
          duration_bucket: durationBucket.value,
          covered_zone_ids: zoneId.value ? [zoneId.value] : [],
          animal_observed: false,
          observed_at: observedAt,
        },
        confirmation: props.targetClaimId
          ? {
              confirmation_type: "not_seen_now",
              place_id: targetPlaceId,
              target_claim_id: props.targetClaimId,
              observed_at: observedAt,
            }
          : null,
        external_content: null,
      });
      if (props.placeId === targetPlaceId) {
        onDone(
          "已记录这次现场观察：本次停留没有看到动物。它不会删除较早记录，也不会生成“这里没有动物”的结论。",
        );
      }
    } catch (cause) {
      error.value = presentDescription(cause);
    } finally {
      busy.value = false;
    }
  }

  return { sourceMode, occurredAt, durationBucket, zoneId, busy, error, canSubmit, submit };
}
