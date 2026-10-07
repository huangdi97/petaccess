/**
 * Row view helpers — M3.1 corrective closure (UI_RECONSTRUCTION_GOAL §8.5).
 *
 * Presentation strings for a result row's Rule / Reality 摘要, plus the Lens
 * projection (§8.5). Everything here reads ONLY from server-provided values
 * (the CoexistenceSnapshot's rule_answer / reality_answer) and the shared
 * vocabulary in `reality.ts`; no domain semantics are invented.
 *
 * A lens changes CONSUMER PRESENTATION only — which layer is headlined and in
 * what order rows sort — never the facts the server returned and never the
 * request. "暂无记录 ≠ 没有动物" is preserved verbatim.
 */
import type { AccessAnswer, CoexistenceSnapshot, RealityAnswer } from "@petaccess/client-core";
import { REALITY_STATE_LABELS } from "../reality";

export type ConsumerLens = "" | "presence" | "rules" | "indoor" | "dining";

/** One-line reality headline for a row (v0.2.4 §11: 列表缩写成「暂无足够现场记录」，
 * 完整核验措辞（≠ 没有动物）留给详情页）。 */
export function realityLineFor(reality: RealityAnswer | null | undefined): string {
  if (!reality) return "暂无足够现场记录";
  const label = REALITY_STATE_LABELS[reality.state] ?? reality.state;
  return label === "暂无足够现场记录（≠ 没有动物）" ? "暂无足够现场记录" : label;
}

/**
 * Canonical coexistence headline for compact consumer rows.
 *
 * Presence is one Reality dimension, not the whole layer. When presence itself
 * is insufficient but published StaffResponse / Facility facts exist, keep
 * those facts visible instead of collapsing the row to a misleading generic
 * empty-looking state. The wording still preserves the semantic boundary:
 * staff/facility facts do not imply policy or access.
 */
export function coexistenceRealityLine(
  snapshot: CoexistenceSnapshot | null | undefined,
  fallback?: RealityAnswer | null,
): string {
  const reality = snapshot?.reality_answer ?? fallback ?? null;
  if (!reality) return "暂无足够现场记录";

  const factualDisputes = [
    ...(snapshot?.staff_response_summary ?? reality.staff_response_summary ?? []),
    ...(snapshot?.facility_summary ?? reality.facility_summary ?? []),
  ].reduce((sum, item) => sum + (item.disputed_count ?? 0), 0);
  if (reality.state === "DISPUTED" || factualDisputes > 0) {
    return factualDisputes > 0
      ? `现场事实存在异议（${factualDisputes} 条处理中）`
      : realityLineFor(reality);
  }

  const presenceInformative = !["NO_RECENT_RECORD", "INSUFFICIENT_OBSERVATION"].includes(
    reality.state,
  );
  if (presenceInformative) return realityLineFor(reality);

  const staffCount = (
    snapshot?.staff_response_summary ??
    reality.staff_response_summary ??
    []
  ).reduce((sum, item) => sum + item.count, 0);
  const facilityCount = (snapshot?.facility_summary ?? reality.facility_summary ?? []).reduce(
    (sum, item) => sum + item.count,
    0,
  );

  if (staffCount > 0 && facilityCount > 0) {
    return "有经核验工作人员处理与设施记录；动物出现记录不足";
  }
  if (staffCount > 0) return "有经核验工作人员处理；动物出现记录不足";
  if (facilityCount > 0) return "有经核验动物设施记录；动物出现记录不足";
  return realityLineFor(reality);
}

/** Evidence / freshness metadata line; empty when there is genuinely nothing. */
export function evidenceLineFor(reality: RealityAnswer | null | undefined): string {
  if (!reality) return "";
  const parts: string[] = [];
  if (reality.evidence_count > 0) parts.push(`${reality.evidence_count} 条现场依据`);
  if (reality.distinct_source_count > 0) parts.push(`${reality.distinct_source_count} 个来源`);
  if (reality.days_since_last_seen != null) {
    parts.push(`${reality.days_since_last_seen} 天前最近记录`);
  }
  return parts.join(" · ");
}

/** Evidence/freshness for the complete Reality layer, not presence alone. */
export function coexistenceEvidenceLine(
  snapshot: CoexistenceSnapshot | null | undefined,
  fallback?: RealityAnswer | null,
): string {
  if (!snapshot) return evidenceLineFor(fallback);
  const parts: string[] = [];
  const evidence = snapshot.evidence_summary;
  if (evidence.reality_evidence_count > 0) {
    parts.push(`${evidence.reality_evidence_count} 条现场依据`);
  }
  if (evidence.reality_distinct_source_count > 0) {
    parts.push(`${evidence.reality_distinct_source_count} 个现场来源`);
  }
  const reality = snapshot.reality_answer ?? fallback ?? null;
  if (reality?.days_since_last_seen != null) {
    parts.push(`${reality.days_since_last_seen} 天前最近动物现场`);
  }
  return parts.join(" · ");
}

/** Compact recency line for a result row's right side — "N 天前记录". */
export function recentLineFor(reality: RealityAnswer | null | undefined): string {
  if (!reality || reality.days_since_last_seen == null) return "";
  return `${reality.days_since_last_seen} 天前记录`;
}

/**
 * Lens projection for a row. Returns which layer is headlined and, for the
 * indoor / dining lenses, the observed zones to surface — all server facts.
 *
 *   presence → Reality-first (headline = reality line)
 *   rules    → Rule-first (headline = rule conclusion)
 *   indoor   → only verified facts whose Zone is INDOOR
 *   dining   → only verified facts whose ZoneType is DINING_AREA
 */
export interface LensProjection {
  headline: "rule" | "reality";
  realityLine: string;
  evidenceLine: string;
  /** Zones to surface under indoor / dining lenses (server facts only). */
  zoneFacts: string[];
}

function exactZoneFacts(lens: ConsumerLens, reality: RealityAnswer | null | undefined): string[] {
  const rows = reality?.observed_zone_facts ?? [];
  if (lens === "indoor") {
    return rows.filter((item) => item.indoor_outdoor === "indoor").map((item) => item.name);
  }
  if (lens === "dining") {
    return rows.filter((item) => item.zone_type === "dining_area").map((item) => item.name);
  }
  return [];
}

function hasExactZoneFacet(lens: ConsumerLens, reality: RealityAnswer | null | undefined): boolean {
  if (!reality) return false;
  if (exactZoneFacts(lens, reality).length > 0) return true;
  // Backward-compatible aggregate facets are allowed only as a yes/no signal.
  // We never guess a Zone name from independent arrays.
  if (lens === "indoor") return (reality.observed_indoor_outdoor ?? []).includes("indoor");
  if (lens === "dining") return (reality.observed_zone_types ?? []).includes("dining_area");
  return false;
}

function spatialLensLine(
  lens: ConsumerLens,
  reality: RealityAnswer | null | undefined,
): string | null {
  if (lens !== "indoor" && lens !== "dining") return null;
  const zones = exactZoneFacts(lens, reality);
  const matched = hasExactZoneFacet(lens, reality);
  const label = lens === "indoor" ? "室内区域" : "餐饮区域";
  if (!matched) return `暂无经核验的${label}动物出现记录`;
  return zones.length
    ? `${label}有经核验动物出现 · ${zones.slice(0, 2).join("、")}`
    : `${label}有经核验动物出现记录`;
}

export function lensProjection(
  lens: ConsumerLens,
  answer: AccessAnswer | null | undefined,
  reality: RealityAnswer | null | undefined,
  snapshot?: CoexistenceSnapshot | null,
): LensProjection {
  const ruleFirst = lens === "rules";
  const zoneFacts = exactZoneFacts(lens, reality);
  return {
    headline: ruleFirst ? "rule" : "reality",
    realityLine: spatialLensLine(lens, reality) ?? coexistenceRealityLine(snapshot, reality),
    evidenceLine: coexistenceEvidenceLine(snapshot, reality),
    zoneFacts,
  };
}

/**
 * Presentation-only sort score for a lens. Higher sorts earlier.
 *
 *   presence → most recent on-site record first (null recency = last)
 *   rules    → places with an answered rule conclusion first
 *   indoor / dining → only places with matching structured Zone facets first
 *   (default) → no reordering (server order)
 */
export function lensOrderScore(
  lens: ConsumerLens,
  answer: AccessAnswer | null | undefined,
  reality: RealityAnswer | null | undefined,
): number {
  switch (lens) {
    case "presence": {
      const days = reality?.days_since_last_seen;
      if (days == null) return 0;
      // newest record (smallest days) sorts first within the presence group
      return 1000 - Math.min(days, 1000);
    }
    case "rules":
      return answer ? 1 : 0;
    case "indoor":
    case "dining":
      return hasExactZoneFacet(lens, reality) ? 1 : 0;
    default:
      return 0;
  }
}

/** Human-readable freshness line for a stale / cached entry (C4). */
export function freshnessLineFor(
  stale: boolean,
  fetchedAtMs: number | null,
  offline: boolean,
): string {
  if (offline) return "当前离线 · 显示最近一次成功获取的结果";
  if (stale && fetchedAtMs != null) {
    const d = new Date(fetchedAtMs);
    const hh = `${d.getHours()}`.padStart(2, "0");
    const mm = `${d.getMinutes()}`.padStart(2, "0");
    return `内容可能不是最新 · 上次获取 ${hh}:${mm}`;
  }
  return "";
}
