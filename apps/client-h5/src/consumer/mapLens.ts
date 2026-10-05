import {
  coverageHint,
  type MapMarker,
} from "@petaccess/client-core";

import { answerStatusKey, answerVerdictLabel } from "../answer";
import { divergenceLabel, realityStateLabel } from "../reality";
import type { RowFacts } from "./repository";

export type MapLensKey = "rule" | "reality" | "facility" | "divergence";

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
        return "UNKNOWN";
    }
  }

  if (lens === "facility") {
    const facilities = row.snapshot?.facility_summary ?? [];
    if (facilities.some((item) => item.operational_state === "active" && item.count > 0))
      return "ALLOWED";
    if (facilities.some((item) => item.count > 0)) return "CONDITIONAL";
    return "UNKNOWN";
  }

  const state = row.snapshot?.divergence?.state;
  if (state === "RULE_REALITY_ALIGNED") return "ALLOWED";
  if (state === "RULE_ALLOWS_BUT_NO_RECENT_RECORD") return "STALE";
  if (state && state !== "INSUFFICIENT_DATA") return "CONFLICT";
  return "UNKNOWN";
}

export function mapLensLabel(lens: MapLensKey, row: RowFacts | undefined): string {
  if (!row) return "信息不足";
  if (lens === "rule") return answerVerdictLabel(row.answer);
  if (lens === "reality") return realityStateLabel(row.reality);

  if (lens === "facility") {
    const facilities = row.snapshot?.facility_summary ?? [];
    const total = facilities.reduce((sum, item) => sum + item.count, 0);
    const active = facilities
      .filter((item) => item.operational_state === "active")
      .reduce((sum, item) => sum + item.count, 0);
    if (active > 0) return `${active} 处已核验动物设施`;
    if (total > 0) return `${total} 处动物设施记录`;
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

  if (lens === "reality") {
    const covered = [...facts.values()].filter((row) => (row.reality?.evidence_count ?? 0) > 0).length;
    return {
      covered,
      unknown: Math.max(0, markers.length - covered),
      text: `当前视野 ${markers.length} 个场所：${covered} 个有现场证据。暂无记录不代表现场没有动物。`,
    };
  }

  if (lens === "facility") {
    const covered = [...facts.values()].filter((row) =>
      (row.snapshot?.facility_summary ?? []).some((item) => item.count > 0),
    ).length;
    return {
      covered,
      unknown: Math.max(0, markers.length - covered),
      text: `当前视野 ${markers.length} 个场所：${covered} 个有动物设施记录。设施存在不等于允许进入。`,
    };
  }

  const covered = [...facts.values()].filter((row) => {
    const state = row.snapshot?.divergence?.state;
    return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
  }).length;
  return {
    covered,
    unknown: Math.max(0, markers.length - covered),
    text: `当前视野 ${markers.length} 个场所：${covered} 个存在规则与现场差异。`,
  };
}
