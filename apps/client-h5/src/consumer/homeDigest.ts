import type {
  AccessAnswer,
  PlaceSummary,
  RealityAnswer,
  CoexistenceSnapshot,
} from "@petaccess/client-core";
import { answerVerdictLabel } from "../answer";
import {
  coexistenceRealityLine,
  lensOrderScore,
  lensProjection,
  type ConsumerLens,
} from "./rowView";
import { divergenceLabel } from "../reality";

export interface HomeDigestCard {
  place: PlaceSummary;
  status: string;
  facts: {
    answer: AccessAnswer | null;
    answerError?: boolean;
    reality: RealityAnswer | null;
    realityError?: boolean;
    snapshot: CoexistenceSnapshot | null;
  };
}

export function homeDigestHasUsefulFact(card: HomeDigestCard): boolean {
  const presenceEvidence = card.facts.reality?.evidence_count ?? 0;
  const realityEvidence = card.facts.snapshot?.evidence_summary.reality_evidence_count ?? 0;
  const ruleEvidence = card.facts.snapshot?.evidence_summary.rule_evidence.length ?? 0;
  return (
    presenceEvidence > 0 || realityEvidence > 0 || ruleEvidence > 0 || card.status !== "UNKNOWN"
  );
}

export function compareHomeDigest(a: HomeDigestCard, b: HomeDigestCard, interest: ConsumerLens) {
  if (interest) {
    const byInterest =
      lensOrderScore(interest, b.facts.answer, b.facts.reality) -
      lensOrderScore(interest, a.facts.answer, a.facts.reality);
    if (byInterest) return byInterest;
  }
  const aDays = a.facts.reality?.days_since_last_seen ?? Number.POSITIVE_INFINITY;
  const bDays = b.facts.reality?.days_since_last_seen ?? Number.POSITIVE_INFINITY;
  if (aDays !== bDays) return aDays - bDays;
  const aEvidence = a.facts.snapshot?.evidence_summary.reality_evidence_count ?? 0;
  const bEvidence = b.facts.snapshot?.evidence_summary.reality_evidence_count ?? 0;
  if (aEvidence !== bEvidence) return bEvidence - aEvidence;
  return a.place.canonical_name.localeCompare(b.place.canonical_name, "zh-CN");
}

export function homeDigestHeadline(card: HomeDigestCard, interest: ConsumerLens): string {
  if (interest === "rules") {
    if (card.facts.answerError) return "规则结论暂时无法取得";
    return card.facts.answer ? answerVerdictLabel(card.facts.answer) : "信息不足";
  }

  if (interest === "presence" || interest === "indoor" || interest === "dining") {
    if (card.facts.realityError) return "现场信息暂时无法取得";
    return lensProjection(interest, card.facts.answer, card.facts.reality, card.facts.snapshot)
      .realityLine;
  }

  const reality = card.facts.reality;
  if (
    !card.facts.realityError &&
    ((card.facts.snapshot?.evidence_summary.reality_evidence_count ?? 0) > 0 || reality)
  ) {
    const line = coexistenceRealityLine(card.facts.snapshot, reality);
    if (line !== "暂无足够现场记录") return line;
  }
  if (!card.facts.answerError && card.facts.answer) return answerVerdictLabel(card.facts.answer);
  if (card.facts.answerError && card.facts.realityError) return "规则与现场暂时无法取得";
  if (card.facts.answerError) return "规则结论暂时无法取得";
  if (card.facts.realityError) return "现场信息暂时无法取得";
  return "信息不足";
}

export function homeDigestMeta(card: HomeDigestCard): string {
  const parts: string[] = [];
  const reality = card.facts.reality;
  if (reality?.days_since_last_seen != null)
    parts.push(`${reality.days_since_last_seen} 天前最近记录`);
  const realityEvidence = card.facts.snapshot?.evidence_summary.reality_evidence_count ?? 0;
  if (realityEvidence > 0) parts.push(`${realityEvidence} 条现场证据`);
  const ruleEvidence = card.facts.snapshot?.evidence_summary.rule_evidence.length ?? 0;
  if (!parts.length && ruleEvidence > 0) parts.push(`${ruleEvidence} 条规则依据`);
  return parts.join(" · ");
}

export function homeDigestDivergence(card: HomeDigestCard): string {
  return divergenceLabel(card.facts.snapshot?.divergence ?? null);
}
