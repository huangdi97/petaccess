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
import type { AccessAnswer, RealityAnswer } from "@petaccess/client-core";
import { REALITY_STATE_LABELS } from "../reality";

export type ConsumerLens = "" | "presence" | "rules" | "indoor" | "dining";

/** One-line reality headline for a row. */
export function realityLineFor(reality: RealityAnswer | null | undefined): string {
  if (!reality) return "暂无足够现场记录（≠ 没有动物）";
  return REALITY_STATE_LABELS[reality.state] ?? reality.state;
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

/**
 * Lens projection for a row. Returns which layer is headlined and, for the
 * indoor / dining lenses, the observed zones to surface — all server facts.
 *
 *   presence → Reality-first (headline = reality line)
 *   rules    → Rule-first (headline = rule conclusion)
 *   indoor   → zone facts surfaced from reality_answer.observed_zones
 *   dining   → zone facts surfaced from reality_answer.observed_zones
 */
export interface LensProjection {
  headline: "rule" | "reality";
  realityLine: string;
  evidenceLine: string;
  /** Zones to surface under indoor / dining lenses (server facts only). */
  zoneFacts: string[];
}

export function lensProjection(
  lens: ConsumerLens,
  answer: AccessAnswer | null | undefined,
  reality: RealityAnswer | null | undefined,
): LensProjection {
  const ruleFirst = lens === "rules";
  const zoneFacts = lens === "indoor" || lens === "dining" ? (reality?.observed_zones ?? []) : [];
  return {
    headline: ruleFirst ? "rule" : "reality",
    realityLine: realityLineFor(reality),
    evidenceLine: evidenceLineFor(reality),
    zoneFacts,
  };
}

/**
 * Presentation-only sort score for a lens. Higher sorts earlier.
 *
 *   presence → most recent on-site record first (null recency = last)
 *   rules    → places with an answered rule conclusion first
 *   indoor / dining → places with observed zones first, then by name
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
      return (reality?.observed_zones.length ?? 0) > 0 ? 1 : 0;
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
