import type { RealityEventView } from "@petaccess/client-core";
import {
  animalFacilityLabel,
  animalScopeLabel,
  facilityAccessModeLabel,
  facilityStateLabel,
  observedActionLabel,
  staffActionLabel,
  staffRoleLabel,
} from "./labels";

export type EvidenceVisualState = "verified" | "pending" | "disputed" | "historical";

export function realityEventHeadline(event: RealityEventView): string {
  if (event.event_type === "staff_response") {
    return `${staffRoleLabel(event.staff_actor_role)} · ${staffActionLabel(event.staff_action)}`;
  }
  if (event.event_type === "animal_facility") {
    return `动物设施 · ${animalFacilityLabel(event.facility_type)}`;
  }
  return `${animalScopeLabel(event.animal_scope)} · ${observedActionLabel(event.observed_action)}`;
}

export function realityEventDetail(event: RealityEventView): string {
  if (event.event_type === "staff_response") {
    return event.staff_outcome || event.observed_context || "";
  }
  if (event.event_type === "animal_facility") {
    const parts = [
      facilityStateLabel(event.facility_state),
      facilityAccessModeLabel(event.facility_access_mode),
    ];
    if (event.facility_capacity != null) parts.push(`容量 ${event.facility_capacity}`);
    if (event.facility_size_limit) parts.push(`体型限制 ${event.facility_size_limit}`);
    return parts.join(" · ");
  }
  return event.observed_context || "";
}

export function realityEventTimeBasis(event: RealityEventView): string {
  if (event.time_basis === "verified") return "按核验时间记录";
  if (event.time_basis === "recorded") return "按收录时间记录";
  return "观察时间已记录";
}

export function realityEventVerification(event: RealityEventView): string {
  return event.verification_status === "human_verified_with_note" ? "人工核验（附注）" : "人工核验";
}

export function realityEventEvidenceState(event: RealityEventView): EvidenceVisualState {
  if (event.freshness_state === "historical" || event.freshness_state === "expired_for_summary") {
    return "historical";
  }
  if (
    event.verification_status === "human_verified" ||
    event.verification_status === "human_verified_with_note"
  ) {
    return "verified";
  }
  return "pending";
}

export function displayRealityTime(iso: string): string {
  return iso.length >= 16 ? `${iso.slice(0, 10)} ${iso.slice(11, 16)}` : iso;
}
