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

const ORIGIN_LABELS: Record<string, string> = {
  on_site_now: "现场亲历",
  on_site_past: "过往现场亲历",
  external_online_content: "公开内容线索",
  operator_provided: "场所方提供",
  official_public_content: "官方公开内容",
};

const FACT_EVIDENCE_LABELS: Record<string, string> = {
  direct_media: "附现场媒体证据",
  first_hand_no_media: "一手记录（无媒体）",
  external_media: "附外部媒体线索",
  text_only_external: "链接 / 文字线索",
  operator_statement: "场所方陈述",
  official_statement: "官方陈述",
  inferred_from_context: "上下文推断，已人工复核",
  insufficient: "证据材料有限",
};

export function realityEventProvenance(event: RealityEventView): string {
  const parts: string[] = [];
  const origin = event.origin ? ORIGIN_LABELS[event.origin] : "";
  const evidence = event.fact_evidence_state ? FACT_EVIDENCE_LABELS[event.fact_evidence_state] : "";
  if (origin) parts.push(origin);
  if (evidence) parts.push(evidence);
  if (event.place_match_state === "exact_place") parts.push("地点已精确匹配");
  else if (event.place_match_state === "exact_subplace") parts.push("子区域已精确匹配");
  if (!parts.length && event.evidence_bundle_id) parts.push("已有可追溯核验材料");
  if (!parts.length && event.source_id) parts.push("已有来源记录");
  return parts.join(" · ");
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


export interface RealityProvenanceCounts {
  rawMaterialCount: number;
  placeMatchedCount: number;
  timeConfirmedCount: number;
  sourceCount: number;
  reviewedCount: number;
}

/**
 * Five independent provenance dimensions for the Evidence rail.
 *
 * Do not infer one stage from another: a human-reviewed event can still have
 * weak place/time/source anchors. Counts deliberately come from published
 * event metadata instead of UI assumptions.
 */
export function realityProvenanceCounts(events: RealityEventView[]): RealityProvenanceCounts {
  const rawMaterialCount = events.filter(
    (event) =>
      Boolean(event.evidence_bundle_id) ||
      Boolean(event.source_id) ||
      Boolean(event.fact_evidence_state && event.fact_evidence_state !== "insufficient"),
  ).length;

  const placeMatchedCount = events.filter((event) =>
    ["exact_place", "exact_subplace"].includes(event.place_match_state ?? ""),
  ).length;

  const timeConfirmedCount = events.filter(
    (event) =>
      Boolean(event.time_evidence_state) &&
      !["publication_time_only", "unknown"].includes(event.time_evidence_state ?? ""),
  ).length;

  const sourceAnchors = new Set<string>();
  for (const event of events) {
    if (event.source_id) sourceAnchors.add(`source:${event.source_id}`);
    else if (event.evidence_bundle_id) sourceAnchors.add(`bundle:${event.evidence_bundle_id}`);
  }

  const reviewedCount = events.filter((event) =>
    ["human_verified", "human_verified_with_note"].includes(event.verification_status),
  ).length;

  return {
    rawMaterialCount,
    placeMatchedCount,
    timeConfirmedCount,
    sourceCount: sourceAnchors.size,
    reviewedCount,
  };
}
