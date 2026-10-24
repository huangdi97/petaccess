import { ref } from "vue";
import { client, session, type RealityEventView } from "@petaccess/client-core";
import { presentDescription } from "../errors";

export type RealityConfirmationType =
  "still_present" | "facility_still_present" | "facility_removed";

/**
 * Shared lightweight confirmation flow for published Reality facts.
 *
 * Confirmation adds evidence; it never edits/deletes the historical claim and
 * never changes Rule. NOT_SEEN_NOW stays on the ObservationEffort route.
 */
export function useRealityConfirmation(placeId: () => string) {
  const message = ref("");
  const busyEventId = ref<string | null>(null);

  async function confirm(event: RealityEventView, type: RealityConfirmationType) {
    const currentPlaceId = placeId();
    if (!session.signedIn || !currentPlaceId || busyEventId.value) return;

    message.value = "";
    busyEventId.value = event.id;
    const observedAt = new Date().toISOString();

    try {
      await client.createRealityReport(currentPlaceId, {
        report: {
          origin: "on_site_now",
          place_id: currentPlaceId,
          subject_place_id: currentPlaceId,
          place_match_state: "exact_place",
          place_match_evidence_types: ["user_confirmation"],
          time_evidence_state: "live_device_time",
          observed_at: observedAt,
          time_certainty: "exact",
          fact_evidence_state: "first_hand_no_media",
          privacy_state: "private",
        },
        candidates: [],
        effort: null,
        confirmation: {
          confirmation_type: type,
          place_id: currentPlaceId,
          target_claim_id: event.id,
          observed_at: observedAt,
        },
        external_content: null,
      });
      message.value =
        type === "facility_removed"
          ? "已记录设施撤除线索，等待核验；历史设施记录不会被直接删除。"
          : "已记录本次现场确认，等待核验。";
    } catch (error) {
      message.value = `确认未提交：${presentDescription(error)}`;
    } finally {
      busyEventId.value = null;
    }
  }

  function reset() {
    message.value = "";
    busyEventId.value = null;
  }

  return { message, busyEventId, confirm, reset };
}
