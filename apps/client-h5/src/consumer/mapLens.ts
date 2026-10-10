import { type MapMarker } from "@petaccess/client-core";

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
/**
 * Marker glyphs are lens semantics, not access verdict aliases.
 *
 * MarkerStatus is deliberately reused as a neutral shape/tone carrier, so an
 * ALLOWED carrier outside the Rule lens must never render a "permission" ✓.
 * Full human-readable meaning remains in mapLensLabel() and the results pane.
 */
export function mapLensGlyph(lens: string, status: MapMarker["status"]): string {
  if (lens === "reality") {
    const glyphs: Record<MapMarker["status"], string> = {
      ALLOWED: "●",
      CONDITIONAL: "◐",
      RESTRICTED: "—",
      UNKNOWN: "?",
      CONFLICT: "!",
      STALE: "↻",
    };
    return glyphs[status];
  }
  if (lens === "facility") {
    const glyphs: Record<MapMarker["status"], string> = {
      ALLOWED: "◆",
      CONDITIONAL: "◇",
      RESTRICTED: "—",
      UNKNOWN: "?",
      CONFLICT: "!",
      STALE: "↻",
    };
    return glyphs[status];
  }
  if (lens === "divergence") {
    const glyphs: Record<MapMarker["status"], string> = {
      ALLOWED: "=",
      CONDITIONAL: "△",
      RESTRICTED: "!",
      UNKNOWN: "?",
      CONFLICT: "!",
      STALE: "↻",
    };
    return glyphs[status];
  }
  const glyphs: Record<MapMarker["status"], string> = {
    ALLOWED: "✓",
    CONDITIONAL: "△",
    RESTRICTED: "▬",
    UNKNOWN: "?",
    CONFLICT: "!",
    STALE: "↻",
  };
  return glyphs[status];
}

export function mapLensTone(lens: MapLensKey, row: RowFacts | undefined): MapMarker["status"] {
  if (!row) return "STALE";
  // STALE is used only as a neutral visual carrier for a temporary transport
  // failure. Human-readable labels below say "暂时无法取得"; they never call
  // the failure a stale fact or an UNKNOWN domain answer.
  if (lens === "rule") return row.answerError ? "STALE" : answerStatusKey(row.answer);

  if (lens === "reality") {
    if (row.realityError) return "STALE";
    const factualDisputes = [
      ...(row.snapshot?.staff_response_summary ?? []),
      ...(row.snapshot?.facility_summary ?? []),
    ].reduce((sum, item) => sum + (item.disputed_count ?? 0), 0);
    if (factualDisputes > 0) return "CONFLICT";
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
    if (row.realityError) return "STALE";
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

  if (row.answerError || row.realityError) return "STALE";
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
  if (!row) return "信息暂时无法取得";
  if (lens === "rule") {
    return row.answerError ? "规则结论暂时无法取得" : answerVerdictLabel(row.answer);
  }
  if (lens === "reality") {
    return row.realityError
      ? "现场信息暂时无法取得"
      : coexistenceRealityLine(row.snapshot, row.reality);
  }

  if (lens === "facility") {
    if (row.realityError) return "设施信息暂时无法取得";
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

  if (row.answerError || row.realityError) return "规则与现场对照暂时无法取得";
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
  const rows = markers.map((marker) => facts.get(marker.id));
  const unavailable = rows.filter((row) => {
    if (!row) return true;
    if (lens === "rule") return row.answerError;
    if (lens === "reality" || lens === "facility") return row.realityError;
    return row.answerError || row.realityError;
  }).length;
  const availableRows = rows.filter((row): row is RowFacts => {
    if (!row) return false;
    if (lens === "rule") return !row.answerError;
    if (lens === "reality" || lens === "facility") return !row.realityError;
    return !row.answerError && !row.realityError;
  });

  if (lens === "rule") {
    const unknown = availableRows.filter((row) =>
      ["UNKNOWN", "CONFLICT"].includes(answerStatusKey(row.answer)),
    ).length;
    const covered = Math.max(0, markers.length - unknown - unavailable);
    const unavailableCopy = unavailable ? `，${unavailable} 个暂时无法取得规则结论` : "";
    return {
      covered,
      unknown,
      text:
        markers.length === 0
          ? "当前查询没有可显示的位置点。无地图点位不代表场所没有规则或现场事实。"
          : `当前查询中 ${markers.length} 个可定位场所：${covered} 个已有规则结论，${unknown} 个信息不足或来源不一致${unavailableCopy}。信息不足不等于允许。`,
    };
  }

  if (lens === "reality") {
    const covered = availableRows.filter(
      (row) => (row.snapshot?.evidence_summary.reality_evidence_count ?? 0) > 0,
    ).length;
    const unknown = Math.max(0, markers.length - covered - unavailable);
    const unavailableCopy = unavailable ? `，${unavailable} 个现场信息暂时无法取得` : "";
    return {
      covered,
      unknown,
      text: `当前查询中 ${markers.length} 个可定位场所：${covered} 个有经核验现场事实${unavailableCopy}。动物出现、工作人员处理与设施事实彼此独立；暂无动物记录不代表现场没有动物。`,
    };
  }

  if (lens === "facility") {
    const covered = availableRows.filter((row) =>
      (row.snapshot?.facility_summary ?? []).some((item) => item.count > 0),
    ).length;
    const unknown = Math.max(0, markers.length - covered - unavailable);
    const unavailableCopy = unavailable ? `，${unavailable} 个设施信息暂时无法取得` : "";
    return {
      covered,
      unknown,
      text: `当前查询中 ${markers.length} 个可定位场所：${covered} 个有动物设施记录${unavailableCopy}。设施存在不等于允许进入。`,
    };
  }

  const covered = availableRows.filter((row) => {
    const state = row.snapshot?.divergence?.state;
    return Boolean(state && !["RULE_REALITY_ALIGNED", "INSUFFICIENT_DATA"].includes(state));
  }).length;
  const unknown = Math.max(0, markers.length - covered - unavailable);
  const unavailableCopy = unavailable ? `，${unavailable} 个对照结果暂时无法取得` : "";
  return {
    covered,
    unknown,
    text: `当前查询中 ${markers.length} 个可定位场所：${covered} 个需要重点对照规则与现场${unavailableCopy}。`,
  };
}
