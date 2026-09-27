/**
 * Row view helpers — M3 (V020_M3_CONSUMER_CORE).
 *
 * The presentation strings for a result row's Reality 摘要 / Evidence 元数据.
 * They read ONLY from the server-provided RealityAnswer (or the snapshot's
 * reality_answer) and reuse the shared vocabulary in `reality.ts`; no domain
 * semantics are invented here. Null answer → the honest "暂无记录 ≠ 没有动物"
 * line, never a fabricated "没有动物".
 */
import type { RealityAnswer } from "@petaccess/client-core";
import { REALITY_STATE_LABELS } from "../reality";

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
