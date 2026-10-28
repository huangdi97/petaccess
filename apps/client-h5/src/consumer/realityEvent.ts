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
  const verified =
    event.verification_status === "human_verified_with_note" ? "人工核验（附注）" : "人工核验";
  return event.dispute_open ? `${verified} · 异议处理中` : verified;
}

const ORIGIN_LABELS: Record<string, string> = {
  on_site_now: "现场亲历",
  on_site_past: "过往现场亲历",
  external_online_content: "公开内容线索",
  operator_provided: "场所方提供",
  official_public_content: "官方公开内容",
};

export function realityOriginLabel(value: string | null | undefined): string {
  return value ? (ORIGIN_LABELS[value] ?? "其他来源方式") : "来源方式未记录";
}

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

export function factEvidenceLabel(value: string | null | undefined): string {
  return value ? (FACT_EVIDENCE_LABELS[value] ?? "证据类型未归类") : "证据类型未记录";
}

const MATERIAL_TYPE_LABELS: Record<string, string> = {
  url: "网页原始材料",
  page_snapshot: "网页快照",
  official_notice: "官方通知",
  signage_photo: "现场规则牌照片",
  uploaded_image: "上传图片",
  video_keyframe: "视频关键帧",
  phone_note: "人工核验记录",
};

const SOURCE_PLATFORM_LABELS: Record<string, string> = {
  official_web: "官方网站",
  operator_site: "场所方渠道",
  search_discovery: "搜索发现",
  social_platform: "社交平台线索",
  user_link: "用户提供链接",
  manual_verification: "人工核验",
  onsite: "现场采集",
  platform_upload: "平台上传",
};

const PUBLISHER_TYPE_LABELS: Record<string, string> = {
  government: "政府 / 主管部门",
  official_operator: "场所管理方",
  staff: "工作人员",
  trusted_verifier: "认证核验方",
  ordinary_user: "普通用户",
  unknown: "发布主体未确认",
};

export function evidenceMaterialLabel(event: RealityEventView): string {
  if (!event.evidence_bundle_id) return "暂无可追溯原始材料";
  const parts: string[] = [];
  if (event.evidence_material_type) {
    parts.push(MATERIAL_TYPE_LABELS[event.evidence_material_type] ?? "其他原始材料");
  }
  if (event.evidence_source_platform) {
    parts.push(SOURCE_PLATFORM_LABELS[event.evidence_source_platform] ?? "其他来源平台");
  }
  if (event.evidence_publisher_type) {
    parts.push(PUBLISHER_TYPE_LABELS[event.evidence_publisher_type] ?? "发布主体未归类");
  }
  if (event.evidence_class) {
    parts.push(event.evidence_class === "original" ? "原始证据" : "派生证据");
  }
  if (event.evidence_display_allowed === false) parts.push("原始内容受许可 / 隐私限制");
  else if (event.evidence_display_allowed === true) parts.push("允许公开展示原始材料");
  return parts.length ? parts.join(" · ") : "已有可追溯材料";
}

export function realityEventProvenance(event: RealityEventView): string {
  const parts: string[] = [];
  const origin = event.origin ? realityOriginLabel(event.origin) : "";
  const evidence = event.fact_evidence_state ? factEvidenceLabel(event.fact_evidence_state) : "";
  if (origin) parts.push(origin);
  if (evidence) parts.push(evidence);
  if (event.place_match_state === "exact_place") parts.push("地点已精确匹配");
  else if (event.place_match_state === "exact_subplace") parts.push("子区域已精确匹配");
  if ((event.confirmation_count ?? 0) > 0) {
    parts.push(`另有 ${event.confirmation_count} 条独立确认`);
  }
  if (event.evidence_bundle_id) parts.push(evidenceMaterialLabel(event));
  if (!parts.length && event.evidence_bundle_id) parts.push("已有可追溯材料");
  if (!parts.length && event.source_id) parts.push("已有来源记录");
  return parts.join(" · ");
}

export function realityEventEvidenceState(event: RealityEventView): EvidenceVisualState {
  if (event.dispute_open) return "disputed";
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
  const rawMaterialCount = events.filter((event) => Boolean(event.evidence_material_type)).length;

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
    if (event.source_id) sourceAnchors.add(event.source_id);
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
