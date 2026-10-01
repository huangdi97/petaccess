/**
 * UI Oracle — compare.ts
 *
 * Reads probe artifacts (artifacts/blind-ui-recovery/probes/*.json) plus the
 * contract JSON (docs/ui/contracts/json/*.json) and emits PASS / WARN / FAIL
 * rows per rule. Purely node-side: no browser, no screenshots.
 *
 * Run: node --experimental-strip-types tools/ui-oracle/compare.ts <stage>
 *   stage = baseline | final | phase-a | phase-b | ...
 * Output: artifacts/blind-ui-recovery/reports/compare-<contractId>.json
 */
import { readdirSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type {
  CompareArtifact,
  CompareRow,
  ContractSchema,
  DensityRule,
  ElementRule,
  LanguageMeasurement,
  PageProbe,
  RangeSpec,
  StructureRule,
  BudgetRule,
  CompositionRule,
  HierarchyRule,
  StateExpectation,
} from "./contracts.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const CONTRACTS_DIR = path.join(ROOT, "docs/ui/contracts/json");
const PROBES_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/probes");
const REPORTS_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/reports");

const STAGE = process.argv[2] ?? "baseline";

export function loadContracts(): ContractSchema[] {
  const files = readdirSync(CONTRACTS_DIR).filter((f) => f.endsWith(".json"));
  return files.map(
    (f) => JSON.parse(readFileSync(path.join(CONTRACTS_DIR, f), "utf8")) as ContractSchema,
  );
}

export function loadProbe(contractId: string) {
  const f = path.join(PROBES_DIR, `${STAGE}-${contractId}.json`);
  try {
    return JSON.parse(readFileSync(f, "utf8")) as {
      contractId: string;
      viewport: { width: number; height: number };
      pages: PageProbe[];
    };
  } catch {
    return null;
  }
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function inRange(actual: number | null, spec: RangeSpec): boolean {
  if (actual === null) return false;
  if (spec.min !== undefined && actual < spec.min) return false;
  if (spec.max !== undefined && actual > spec.max) return false;
  return true;
}

function row(
  id: string,
  kind: CompareRow["kind"],
  target: CompareRow["target"],
  actual: unknown,
  ok: boolean,
  sev: "FAIL" | "WARN",
  detail: string,
): CompareRow {
  return {
    id,
    kind,
    target,
    actual,
    result: ok ? "PASS" : sev === "FAIL" ? "FAIL" : "WARN",
    detail,
  };
}
function px(s: string | null | undefined): number | null {
  if (!s) return null;
  const m = String(s).match(/^([\d.]+)px/);
  return m ? Number(m[1]) : null;
}
/** Compare a single element rule against one page probe. */
function compareElement(rule: ElementRule, probe: PageProbe, out: CompareRow[]): void {
  const m = probe.elements[rule.id];
  if (!m) {
    out.push({
      id: rule.id,
      kind: "element",
      target: rule.props,
      actual: null,
      result: "FAIL",
      detail: "no probe",
    });
    return;
  }
  const leaf = m.bbox;
  const cs = m.computed;
  for (const [prop, spec] of Object.entries(rule.props)) {
    let actual: number | null | string = null;
    switch (prop) {
      case "width":
        actual = num(leaf?.width);
        break;
      case "height":
        actual = num(leaf?.height);
        break;
      case "count":
        actual = num(m.count);
        break;
      case "fontSize":
        actual = px(cs.fontSize);
        break;
      case "fontWeight":
        actual = num(cs.fontWeight ? Number(cs.fontWeight) : null);
        break;
      case "lineHeight":
        actual = px(cs.lineHeight);
        break;
      case "padding":
        actual = px(cs.padding?.split(" ")[0]);
        break;
      case "margin":
        actual = px(cs.margin?.split(" ")[0]);
        break;
      case "borderRadius":
        actual = px(cs.borderRadius);
        break;
      case "boxShadow":
        actual = cs.boxShadow && cs.boxShadow !== "none" ? String(cs.boxShadow) : "none";
        break;
      case "backgroundColor":
        actual = cs.backgroundColor ?? "";
        break;
      case "position":
        actual = cs.position ?? "";
        break;
      case "overflow":
        actual = cs.overflow ?? "";
        break;
      case "gap":
        actual = px(cs.gap);
        break;
      case "borderBottomWidth":
        actual = px(cs.borderBottomWidth);
        break;
      case "gridTemplateColumns":
        actual = cs.gridTemplateColumns ?? "";
        break;
      case "ariaLabel":
        actual = m.ariaLabel.length > 0 ? 1 : 0;
        break;
      case "maxChildWidth":
        actual = num(m.maxChildWidth);
        break;
      case "contentHeightInViewport":
        actual = num(m.contentHeightInViewport);
        break;
      case "left":
        actual = num(m.leftRelative);
        break;
      case "top":
        actual = num(m.bbox?.y);
        break;
      case "sectionGap":
        actual = num(m.sectionGapAvg);
        break;
      default:
        actual = null;
    }
    const ok =
      spec.equals !== undefined
        ? String(actual) === String(spec.equals)
        : spec.startsWith !== undefined
          ? String(actual).startsWith(spec.startsWith)
          : inRange(num(actual), spec);
    const detail = `target=${spec.min ?? "-"}..${spec.max ?? "-"}${spec.equals !== undefined ? ` ==${spec.equals}` : spec.startsWith !== undefined ? ` startsWith=${spec.startsWith}` : ""} actual=${String(actual)} raw=${JSON.stringify(m.computed[prop] ?? (prop === "width" ? m.bbox?.width : prop === "height" ? m.bbox?.height : ""))}`;
    out.push(row(rule.id, "element", spec, actual, ok, rule.severity, detail));
  }
}

function compareStructure(rule: StructureRule, probe: PageProbe, out: CompareRow[]): void {
  const m = probe.structure[rule.id];
  if (!m) {
    out.push({
      id: rule.id,
      kind: "structure",
      target: rule,
      actual: null,
      result: "FAIL",
      detail: "no probe",
    });
    return;
  }
  if (rule.min !== undefined) {
    out.push(
      row(
        rule.id,
        "structure",
        `min=${rule.min}`,
        m.count,
        m.count >= rule.min,
        rule.severity,
        `count=${m.count}`,
      ),
    );
  }
  if (rule.max !== undefined) {
    out.push(
      row(
        rule.id,
        "structure",
        `max=${rule.max}`,
        m.count,
        m.count <= rule.max,
        rule.severity,
        `count=${m.count}`,
      ),
    );
  }
  if (rule.forbiddenText && rule.forbiddenText.length > 0) {
    const hits = m.details.forbiddenTextHits;
    out.push(
      row(
        rule.id,
        "structure",
        `forbidden=${rule.forbiddenText.join(",")}`,
        hits,
        hits.length === 0,
        rule.severity,
        `hits=${hits.join(",")}`,
      ),
    );
  }
  if (rule.mustContainText || rule.mustContainTexts) {
    out.push(
      row(
        rule.id,
        "structure",
        `must=${(rule.mustContainTexts ?? [rule.mustContainText ?? ""]).join(",")}`,
        m.details.missingRequiredTexts,
        m.details.missingRequiredTexts.length === 0,
        rule.severity,
        `missing=${m.details.missingRequiredTexts.join(",")}`,
      ),
    );
  }
  if (rule.uuidForbidden) {
    const hits = probe.language.uuidHits;
    out.push(
      row(
        rule.id,
        "structure",
        "uuid=0",
        hits,
        hits.length === 0,
        rule.severity,
        `uuidHits=${hits.join(",")}`,
      ),
    );
  }
  if (rule.forbiddenClass) {
    const bad = m.sampleClasses.filter((c) =>
      rule.forbiddenClass!.some((f) => c.split(/\s+/).includes(f)),
    );
    out.push(
      row(
        rule.id,
        "structure",
        `forbiddenClass=${rule.forbiddenClass.join(",")}`,
        bad,
        bad.length === 0,
        rule.severity,
        `classes=${m.sampleClasses.join(" | ")}`,
      ),
    );
  }
  if (rule.containsArrows) {
    out.push(
      row(
        rule.id,
        "structure",
        "arrows>=1",
        m.hasArrows ? 1 : 0,
        m.hasArrows,
        rule.severity,
        `hasArrows=${m.hasArrows}`,
      ),
    );
  }
  if (rule.surfaceRowCount) {
    out.push(
      row(
        rule.id,
        "structure",
        `surfaceRows=${rule.surfaceRowCount.min}-${rule.surfaceRowCount.max}`,
        m.surfaceRows,
        inRange(num(m.surfaceRows), rule.surfaceRowCount),
        rule.severity,
        `surfaceRows=${m.surfaceRows}`,
      ),
    );
  }
  if (rule.disclosureDefault === "collapsed") {
    out.push(
      row(
        rule.id,
        "structure",
        "collapsed-default",
        m.collapsed ? 1 : 0,
        m.collapsed,
        rule.severity,
        `collapsed=${m.collapsed}`,
      ),
    );
  }
  if (rule.minVisibleAfterClick !== undefined) {
    const v = m.visibleCountAfterClick;
    out.push(
      row(
        rule.id,
        "structure",
        `visibleAfterClick>=${rule.minVisibleAfterClick}`,
        v,
        v !== null && v >= rule.minVisibleAfterClick,
        rule.severity,
        `visible=${v}`,
      ),
    );
  }
  if (rule.minVisibleInViewport !== undefined) {
    const v = m.visibleInViewport;
    out.push(
      row(
        rule.id,
        "structure",
        `visibleInViewport>=${rule.minVisibleInViewport}`,
        v,
        v !== null && v >= rule.minVisibleInViewport,
        rule.severity,
        `visibleInViewport=${v}`,
      ),
    );
  }
  if (rule.xConsistent) {
    out.push(
      row(
        rule.id,
        "structure",
        "xConsistent<=1",
        m.xSpread,
        m.xSpread !== null && m.xSpread <= 1,
        rule.severity,
        `xSpread=${m.xSpread}`,
      ),
    );
  }
}

function densityActual(
  rule: DensityRule,
  probe: PageProbe,
  m: ProbeDensity,
  _spec: RangeSpec,
): number | null {
  switch (rule.metric) {
    case "largestVerticalGap":
      return num(m.largestVerticalGap);
    case "horizontalOverflow":
      return num(m.horizontalOverflowPx);
    case "infoBlockCount":
      return num(m.infoBlockCount);
    case "firstViewportVisibleTextLines":
      return num(m.firstViewportVisibleTextLines);
    case "contentHeightInViewport":
      return num(m.contentHeightInViewport);
    default:
      return null;
  }
}

interface ProbeDensity {
  largestVerticalGap: number | null;
  horizontalOverflowPx: number;
  infoBlockCount: number | null;
  firstViewportVisibleTextLines: number;
  contentHeightInViewport: number | null;
  primaryActionCount: number | null;
}

function compareDensity(rule: DensityRule, probe: PageProbe, out: CompareRow[]): void {
  const m = probe.density[rule.id] as unknown as ProbeDensity | undefined;
  if (!m) {
    out.push({
      id: rule.id,
      kind: "density",
      target: rule,
      actual: null,
      result: "FAIL",
      detail: "no probe",
    });
    return;
  }
  if (rule.hasOnePrimaryAction) {
    const n = num(m.primaryActionCount);
    out.push(
      row(
        rule.id,
        "density",
        "primaryAction>=1",
        n,
        n !== null && n >= 1,
        rule.severity,
        `primary=${n}`,
      ),
    );
    return;
  }
  const spec: RangeSpec = {};
  if (rule.min !== undefined) spec.min = rule.min;
  if (rule.max !== undefined) spec.max = rule.max;
  const actual = densityActual(rule, probe, m, spec);
  const warnAt = rule.warnAt;
  const sev: "FAIL" | "WARN" =
    warnAt !== undefined && num(actual) !== null && num(actual)! > warnAt ? "WARN" : rule.severity;
  out.push(
    row(
      rule.id,
      "density",
      spec,
      actual,
      inRange(num(actual), spec),
      sev,
      `actual=${actual} metric=${rule.metric}`,
    ),
  );
}

function compareLanguage(
  flags: ContractSchema["language"],
  probe: PageProbe,
  out: CompareRow[],
): void {
  const l: LanguageMeasurement = probe.language;
  if (flags.uuid) {
    out.push(
      row(
        `${probe.pageId}-UUID`,
        "language",
        "uuid=0",
        l.uuidHits,
        l.uuidHits.length === 0,
        "FAIL",
        `hits=${l.uuidHits.join(",")}`,
      ),
    );
  }
  if (flags.enums) {
    out.push(
      row(
        `${probe.pageId}-ENUM`,
        "language",
        "enum=0",
        l.enumHits,
        l.enumHits.length === 0,
        "FAIL",
        `hits=${l.enumHits.join(",")}`,
      ),
    );
  }
  if (flags.invariants) {
    out.push(
      row(
        `${probe.pageId}-INVARIANT`,
        "language",
        "invariant=0",
        l.invariantHits,
        l.invariantHits.length === 0,
        "FAIL",
        `hits=${l.invariantHits.join(",")}`,
      ),
    );
  }
  if (flags.allcapsTokens) {
    out.push(
      row(
        `${probe.pageId}-ALLCAPS`,
        "language",
        "allcaps=0",
        l.allcapsHits,
        l.allcapsHits.length === 0,
        "FAIL",
        `hits=${l.allcapsHits.join(",")}`,
      ),
    );
  }
  if (flags.refs) {
    out.push(
      row(
        `${probe.pageId}-REFS`,
        "language",
        "refs=0",
        l.refHits,
        l.refHits.length === 0,
        "FAIL",
        `hits=${l.refHits.join(",")}`,
      ),
    );
  }
}

function compareHierarchy(rule: HierarchyRule, probe: PageProbe, out: CompareRow[]): void {
  const m = probe.hierarchy[rule.id];
  if (!m) {
    out.push({
      id: rule.id,
      kind: "hierarchy",
      target: rule.id,
      actual: null,
      result: "FAIL",
      detail: "no probe",
    });
    return;
  }
  const ratio = num(m.ratio);
  if (rule.minRatio !== undefined) {
    out.push(
      row(
        rule.id,
        "hierarchy",
        `ratio>=${rule.minRatio}`,
        ratio,
        ratio !== null && ratio >= rule.minRatio,
        rule.severity,
        `ratio=${ratio} a=${m.aFontSize}px b=${m.bFontSize}px`,
      ),
    );
  }
  if (rule.maxRatio !== undefined) {
    out.push(
      row(
        rule.id,
        "hierarchy",
        `ratio<=${rule.maxRatio}`,
        ratio,
        ratio !== null && ratio <= rule.maxRatio,
        rule.severity,
        `ratio=${ratio} a=${m.aFontSize}px b=${m.bFontSize}px`,
      ),
    );
  }
}

function compareBudget(rule: BudgetRule, probe: PageProbe, out: CompareRow[]): void {
  const m = probe.budget[rule.id];
  if (!m) {
    out.push({
      id: rule.id,
      kind: "budget",
      target: rule.id,
      actual: null,
      result: "FAIL",
      detail: "no probe",
    });
    return;
  }
  const spec: RangeSpec = {};
  if (rule.min !== undefined) spec.min = rule.min;
  if (rule.max !== undefined) spec.max = rule.max;
  const actual = num(m.value);
  out.push(
    row(
      rule.id,
      "budget",
      spec,
      actual,
      inRange(actual, spec),
      rule.severity,
      `actual=${actual} metric=${rule.metric}`,
    ),
  );
}

function compareComposition(rule: CompositionRule, probe: PageProbe, out: CompareRow[]): void {
  const m = probe.composition[rule.id];
  if (!m) {
    out.push({
      id: rule.id,
      kind: "composition",
      target: rule.id,
      actual: null,
      result: "FAIL",
      detail: "no probe",
    });
    return;
  }
  const spec: RangeSpec = {};
  if (rule.min !== undefined) spec.min = rule.min;
  if (rule.max !== undefined) spec.max = rule.max;
  const actual = num(m.value);
  out.push(
    row(
      rule.id,
      "composition",
      spec,
      actual,
      inRange(actual, spec),
      rule.severity,
      `actual=${actual} metric=${rule.metric}`,
    ),
  );
}

function compareState(expect: StateExpectation, probe: PageProbe, out: CompareRow[]): void {
  const s = probe.state;
  const emit = (id: string, field: string, expected: unknown, actual: unknown): void => {
    out.push(
      row(
        `${probe.pageId}-${id}`,
        "state",
        field,
        expected,
        String(actual) === String(expected),
        "FAIL",
        `expected=${String(expected)} actual=${String(actual)} route=${s.route}`,
      ),
    );
  };
  if (expect.page !== undefined) emit("PAGE", "page", expect.page, s.page);
  if (expect.state !== undefined) emit("STATE", "state", expect.state, s.state);
  if (expect.fixture !== undefined) emit("FIXTURE", "fixture", expect.fixture, s.fixture);
  if (expect.h1 !== undefined) emit("H1", "h1", expect.h1, s.h1);
  if (expect.entityId !== undefined) emit("ENTITY", "entityId", expect.entityId, s.entityId);
  if (expect.resultCount !== undefined) {
    emit("COUNT", "resultCount", expect.resultCount, s.resultCount);
  }
  if (expect.selectedId !== undefined)
    emit("SELECTED", "selectedId", expect.selectedId, s.selectedId);
  for (const c of expect.componentCounts ?? []) {
    const actual = s.componentCounts[c.selector] ?? 0;
    out.push(
      row(
        `${probe.pageId}-COMP-${c.selector}`,
        "state",
        `count>=${c.min}`,
        actual,
        actual >= c.min,
        "FAIL",
        `selector=${c.selector} count=${actual}`,
      ),
    );
  }
}

/** Compare one contract (all its pages) and produce a single artifact. */
export function compareContract(contract: ContractSchema): CompareArtifact | null {
  const probe = loadProbe(contract.id);
  if (!probe || probe.pages.length === 0) return null;
  const rows: CompareRow[] = [];
  const applies = (pageId: string, pages?: string[]): boolean =>
    pages === undefined || pages.includes(pageId);
  // Merge all pages: element/structure/density probes keyed by rule id, last
  // page wins for first-match. Rules may scope to specific page ids (`pages`)
  // so state-specific assertions (entry vs guard, ready vs empty) stay precise.
  for (const pageProbe of probe.pages) {
    const pageDef = contract.pages.find((p) => p.id === pageProbe.pageId);
    for (const rule of contract.elements ?? []) {
      if (!applies(pageProbe.pageId, rule.pages)) continue;
      compareElement(rule, pageProbe, rows);
    }
    for (const rule of contract.structure ?? []) {
      if (!applies(pageProbe.pageId, rule.pages)) continue;
      compareStructure(rule, pageProbe, rows);
    }
    for (const rule of contract.density ?? []) {
      if (!applies(pageProbe.pageId, rule.pages)) continue;
      compareDensity(rule, pageProbe, rows);
    }
    for (const rule of contract.hierarchy ?? []) {
      if (!applies(pageProbe.pageId, rule.pages)) continue;
      compareHierarchy(rule, pageProbe, rows);
    }
    for (const rule of contract.budget ?? []) {
      if (!applies(pageProbe.pageId, rule.pages)) continue;
      compareBudget(rule, pageProbe, rows);
    }
    for (const rule of contract.composition ?? []) {
      if (!applies(pageProbe.pageId, rule.pages)) continue;
      compareComposition(rule, pageProbe, rows);
    }
    if (pageDef?.expect) compareState(pageDef.expect, pageProbe, rows);
    compareLanguage(contract.language, pageProbe, rows);
  }
  // Dedup identical (id, kind, result) rows keeping the worst (FAIL > WARN > PASS).
  const seen = new Map<string, CompareRow>();
  for (const r of rows) {
    const key = `${r.kind}:${r.id}`;
    const cur = seen.get(key);
    if (
      !cur ||
      (r.result === "FAIL" && cur.result !== "FAIL") ||
      (r.result === "WARN" && cur.result === "PASS")
    ) {
      seen.set(key, r);
    }
  }
  const finalRows = [...seen.values()].sort((a, b) => a.id.localeCompare(b.id));
  const summary = { PASS: 0, WARN: 0, FAIL: 0 };
  for (const r of finalRows) summary[r.result] += 1;
  return {
    contractId: contract.id,
    viewport: contract.viewport,
    generatedAt: new Date().toISOString(),
    rows: finalRows,
    summary,
  };
}

export function runCompare(): void {
  mkdirSync(REPORTS_DIR, { recursive: true });
  const contracts = loadContracts();
  const artifacts: CompareArtifact[] = [];
  for (const c of contracts) {
    const art = compareContract(c);
    if (!art) {
      console.log(`[${STAGE}] ${c.id}: NO PROBE (skipped)`);
      continue;
    }
    artifacts.push(art);
    const outFile = path.join(REPORTS_DIR, `compare-${c.id}.json`);
    writeFileSync(outFile, JSON.stringify(art, null, 2));
    console.log(
      `[${STAGE}] ${c.id}: PASS=${art.summary.PASS} WARN=${art.summary.WARN} FAIL=${art.summary.FAIL}`,
    );
  }
  const all = { stage: STAGE, generatedAt: new Date().toISOString(), artifacts };
  writeFileSync(path.join(REPORTS_DIR, `${STAGE}-compare-all.json`), JSON.stringify(all, null, 2));
  const total = artifacts.reduce(
    (a, c) => ({
      PASS: a.PASS + c.summary.PASS,
      WARN: a.WARN + c.summary.WARN,
      FAIL: a.FAIL + c.summary.FAIL,
    }),
    { PASS: 0, WARN: 0, FAIL: 0 },
  );
  console.log(`[${STAGE}] TOTAL PASS=${total.PASS} WARN=${total.WARN} FAIL=${total.FAIL}`);
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]).replace(/\\/g, "/") ===
    fileURLToPath(import.meta.url).replace(/\\/g, "/")
) {
  runCompare();
}
