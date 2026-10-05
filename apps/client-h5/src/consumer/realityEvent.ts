import type { RealityEventView } from "@petaccess/client-core";
import {
  animalFacilityLabel,
  animalScopeLabel,
  facilityAccessModeLabel,
  facilityPurposeIsConfirmed,
  facilityPurposeLabel,
  facilityStateLabel,
  observedActionLabel,
  staffActionLabel,
  staffAwarenessLabel,
  staffRoleLabel,
} from "./labels";

export type EvidenceVisualState = "verified" | "pending" | "disputed" | "historical";

export function realityEventHeadline(event: RealityEventView): string {
  if (event.event_type === "staff_response") {
    if (event.staff_action === "no_intervention_observed") {
      return event.staff_awareness_state === "awareness_confirmed"
        ? "工作人员已注意到 · 本次未观察到进一步处理"
        : "本次记录未观察到工作人员处理";
    }
    return `${staffRoleLabel(event.staff_actor_role)} · ${staffActionLabel(event.staff_action)}`;
  }
  if (event.event_type === "animal_facility") {
    return facilityPurposeIsConfirmed(event.facility_purpose_state)
      ? `动物设施 · ${animalFacilityLabel(event.facility_type)}`
      : `疑似动物相关设施 · ${facilityPurposeLabel(event.facility_purpose_state)}`;
  }
  return `${animalScopeLabel(event.animal_scope)} · ${observedActionLabel(event.observed_action)}`;
}

export function realityEventDetail(event: RealityEventView): string {
  if (event.event_type === "staff_response") {
    const parts = [staffAwarenessLabel(event.staff_awareness_state)];
    if (event.staff_outcome) parts.push(event.staff_outcome);
    else if (event.observed_context) parts.push(event.observed_context);
    return parts.join(" · ");
  }
  if (event.event_type === "animal_facility") {
    const parts = [
      facilityPurposeLabel(event.facility_purpose_state),
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
  if (event.time_evidence_state === "publication_time_only") {
    return "仅确认内容发布时间，未确认事件发生时间";
  }
  if (event.time_evidence_state === "exact_event_date") return "事件日期已确认，具体时刻未记录";
  if (event.time_evidence_state === "approximate_date") return "事件日期为约略时间";
  if (event.time_evidence_state === "live_device_time") return "现场设备时间已记录";
  if (event.time_evidence_state === "exact_event_time") return "事件时间已确认";
  if (event.time_basis === "verified") return "按核验时间记录";
  if (event.time_basis === "recorded") return "按收录时间记录";
  return "观察时间已记录";
}

export function realityEventDisplayDate(event: RealityEventView): string {
  const source =
    event.time_evidence_state === "publication_time_only" && event.content_published_at
      ? event.content_published_at
      : event.event_at;
  return source.slice(0, 10);
}

export function realityEventDisplayTime(event: RealityEventView): string {
  if (event.time_evidence_state === "publication_time_only") return "发布";
  if (event.time_evidence_state === "exact_event_date") return "日期";
  if (event.time_evidence_state === "approximate_date") return "约";
  return event.event_at.length >= 16 ? event.event_at.slice(11, 16) : "—";
}

export function displayRealityEventTime(event: RealityEventView): string {
  const date = realityEventDisplayDate(event);
  const time = realityEventDisplayTime(event);
  if (time === "日期") return date;
  if (time === "发布") return `${date} 发布`;
  if (time === "约") return `约 ${date}`;
  return time === "—" ? date : `${date} ${time}`;
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
