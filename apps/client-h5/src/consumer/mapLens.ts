import { coverageHint, type MapMarker } from "@petaccess/client-core";

import { answerStatusKey, answerVerdictLabel } from "../answer";
import { divergenceLabel } from "../reality";
import { coexistenceRealityLine } from "./rowView";
import { facilityPurposeIsConfirmed } from "./labels";
import type { RowFacts } from "./repository";

export type MapLensKey = "rule" | "reality" | "facility" | "divergence";

const MAP_LENS_KEYS = new Set<MapLensKey>(["rule", "reality", "facility", "divergence"]);

export function parseMapLens(value: unknown): MapLensKey {
  return typeof value === "string" && MAP_LENS_KEYS.has(value as MapLensKey)
    ? (value as MapLensKey)
    : "rule";
}

/**
 * MarkerStatus is reused as a clustering/shape carrier. For non-rule lenses
 * these keys are NOT access verdicts; MockMap remaps them to Reality/Facility/
 * Divergence palette tokens and the visible text always comes from
 * mapLensLabel().
 */
export function mapLensTone(lens: MapLensKey, row: RowFacts | undefined): MapMarker["status"] {
  if (!row) return "UNKNOWN";
  if (lens === "rule") return answerStatusKey(row.answer);

  if (lens === "reality") {
    switch (row.reality?.state) {
      case "OBSERVED_RECENTLY":
      case "MULTI_EVIDENCE_OBSERVED":
        return "ALLOWED";
      case "OBSERVED_HISTORICALLY":
        return "STALE";
      case "DISPUTED":
        return "CONFLICT";
      default:
        // Reality includes verified StaffResponse / Facility facts as well as
        // animal presence. Presence-insufficient must not erase those facts.
        return (row.snapshot?.evidence_summary.reality_evidence_count ?? 0) > 0
          ? "ALLOWED"
          : "UNKNOWN";
    }
  }

  if (lens === "facility") {
    const facilities = row.snapshot?.facility_summary ?? [];
    if (facilities.some((item) => (item.disputed_count ?? 0) > 0)) return "CONFLICT";
    if (
      facilities.some(
        (item) =>
          facilityPurposeIsConfirmed(item.purpose_state) &&
          item.operational_state === "active" &&
          item.count > 0,
      )
    )
      return "ALLOWED";
    if (facilities.some((item) => item.count > 0)) return "CONDITIONAL";
    return "UNKNOWN";
  }

  const state = row.snapshot?.divergence?.state;
  if (state === "RULE_REALITY_ALIGNED") return "ALLOWED";
  if (state === "RULE_ALLOWS_BUT_NO_RECENT_RECORD") return "STALE";
  if (state === "RULE_PROHIBITS_BUT_OBSERVED") return "CONFLICT";
  if (state === "RULE_CONDITIONAL_AND_OBSERVED" || state === "RULE_UNKNOWN_BUT_OBSERVED") {
    return "CONDITIONAL";
  }
  return "UNKNOWN";
}

export function mapLensLabel(lens: MapLensKey, row: RowFacts | undefined): string {
  if (!row) return "信息不足";
  if (lens === "rule") return answerVerdictLabel(row.answer);
  if (lens === "reality") return coexistenceRealityLine(row.snapshot, row.reality);

  if (lens === "facility") {
    const facilities = row.snapshot?.facility_summary ?? [];
    const total = facilities.reduce((sum, item) => sum + item.count, 0);
    const confirmed = facilities
      .filter((item) => facilityPurposeIsConfirmed(item.purpose_state))
      .reduce((sum, item) => sum + item.count, 0);
    const activeConfirmed = facilities
      .filter(
        (item) =>
          facilityPurposeIsConfirmed(item.purpose_state) && item.operational_state === "active",
      )
      .reduce((sum, item) => sum + item.count, 0);
    const inferred = Math.max(0, total - confirmed);
    const disputed = facilities.reduce((sum, item) => sum + (item.disputed_count ?? 0), 0);
    if (disputed > 0) return `${disputed} 处设施记录存在异议`;
    if (activeConfirmed > 0) return `${activeConfirmed} 处已核验动物设施`;
    if (confirmed > 0) return `${confirmed} 处动物设施记录`;
    if (inferred > 0) return `${inferred} 处疑似动物相关设施 · 用途待核验`;
    return "暂无已核验动物设施";
  }

  return divergenceLabel(row.snapshot?.divergence ?? null);
}

export interface MapLensCoverage {
  covered: number;
  unknown: number;
  text: string;
}

export function mapLensCoverage(
  lens: MapLensKey,
  facts: Map<string, RowFacts>,
  markers: MapMarker[],
): MapLensCoverage {
  if (lens === "rule") return coverageHint(markers);

  // Coverage text describes the spatial canvas, so only rows that have a
  // marker in the current projection may contribute to the numerator.
  const markerIds = new Set(markers.map((marker) => marker.id));
  const visibleFacts = [...facts.entries()]
    .filter(([placeId]) => markerIds.has(placeId))
    .map(([, row]) => row);

  if (lens === "reality") {
    const covered = visibleFacts.filter(
      (row) => (row.snapshot?.evidence_summary.reality_evidence_count ?? 0) > 0,
    ).length;
    return {
      covered,
      unknown: Math.max(0, markers.length - covered),
      text: `当前视野 ${markers.length} 个场所：${covered} 个有经核验现场事实。动物出现、工作人员处理与设施事实彼此独立；暂无动物记录不代表现场没有动物。`,
    };
  }

  if (lens === "facility") {
    const covered = visibleFacts.filter((row) =>
      (row.snapshot?.facility_summary ?? []).some((item) => item.count > 0),
    ).length;
    return {
      covered,
      unknown: Math.max(0, markers.length - covered),
      text: `当前视野 ${markers.length} 个场所：${covered} 个有动物设施记录。设施存在不等于允许进入。`,
    };
  }

  const covered = visibleFacts.filter((row) => {
    const state = row.snapshot?.divergence?.state;
    return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
  }).length;
  return {
    covered,
    unknown: Math.max(0, markers.length - covered),
    text: `当前视野 ${markers.length} 个场所：${covered} 个需要重点对照规则与现场。`,
  };
}
