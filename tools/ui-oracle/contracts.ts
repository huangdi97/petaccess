/**
 * UI Oracle — shared contract types.
 *
 * The machine-readable contracts live in docs/ui/contracts/json/*.json. This
 * module types them and provides a tiny loader (plain TS, no deps) so both the
 * Playwright probe spec and the standalone compare step read one schema.
 *
 * Rule shape (contract/compare):
 *   - elements:  geometry/computed-style checks on one or a set of elements;
 *   - structure: DOM class/text/count checks (pill walls, forbidden classes,
 *                required texts, disclosure defaults);
 *   - density:   aggregate metrics measured over a region (gaps, line counts,
 *                block counts, overflow);
 *   - hierarchy: relative font-size ratios between two selectors (O3);
 *   - budget:    content-budget line / block counts in a region (O4);
 *   - composition: occupancy / max gap / status-repeat / first-viewport block
 *                counts (O5);
 *   - state:     capture-state integrity expectations (O6);
 *   - language:  visible-text scan flags (uuid / enums / invariants / ALL_CAPS
 *                / refs).
 */
export type Severity = "FAIL" | "WARN";

export interface RangeSpec {
  min?: number;
  max?: number;
  equals?: string | number;
  warnAt?: number;
  /** String prefix match (e.g. grid-template-columns fixed columns). */
  startsWith?: string;
}

export interface ElementRule {
  id: string;
  /** Data-ui attribute value, e.g. "search-results-pane". */
  ui?: string;
  fallbacks?: string[];
  props: Record<string, RangeSpec>;
  severity: Severity;
  /** "rows" = aggregate over every match; otherwise first match. */
  aggregate?: "rows";
  /** Restrict this rule to specific page ids (probe artifact pages[].pageId). */
  pages?: string[];
}

export interface StructureRule {
  id: string;
  selector: string;
  fallbackSelector?: string;
  min?: number;
  max?: number;
  forbiddenClass?: string[];
  forbiddenText?: string[];
  mustContainText?: string;
  mustContainTexts?: string[];
  containsArrows?: boolean;
  surfaceRowCount?: RangeSpec;
  disclosureDefault?: "collapsed";
  minVisibleAfterClick?: number;
  uuidForbidden?: boolean;
  /** O2: all matched elements share the same horizontal x (timeline time col / marker col). */
  xConsistent?: boolean;
  severity: Severity;
  /** Restrict this rule to specific page ids (probe artifact pages[].pageId). */
  pages?: string[];
}

export interface DensityRule {
  id: string;
  selector?: string;
  metric:
    | "largestVerticalGap"
    | "horizontalOverflow"
    | "infoBlockCount"
    | "firstViewportVisibleTextLines"
    | "contentHeightInViewport";
  min?: number;
  max?: number;
  warnAt?: number;
  severity: Severity;
  hasOnePrimaryAction?: boolean;
  /** Restrict this rule to specific page ids (probe artifact pages[].pageId). */
  pages?: string[];
}

/* --- v0.2.3 Oracle v2 新增四层 ------------------------------------------- */

/** O3 相对层级：两个选择器命中元素的计算 font-size 之比。 */
export interface HierarchyRule {
  id: string;
  /** 上层元素选择器（分子）。 */
  a: string;
  /** 基线元素选择器（分母，通常是 body 文本）。 */
  b: string;
  minRatio?: number;
  maxRatio?: number;
  severity: Severity;
  pages?: string[];
}

export type BudgetMetric = "rowTextLines" | "firstViewportBlocks" | "firstViewportTextLines";

/** O4 内容预算：区域内可见文本行数 / 首屏语义块数。 */
export interface BudgetRule {
  id: string;
  metric: BudgetMetric;
  /** 限定的区域选择器（不填 = body）。 */
  selector?: string;
  min?: number;
  max?: number;
  severity: Severity;
  pages?: string[];
}

export type CompositionMetric =
  | "contentOccupancy"
  | "inspectorOccupancy"
  | "largestVerticalGap"
  | "primaryStatusRepeatCount"
  | "semanticBlockCount";

/** O5 构图：占有率 / 最大竖直 gap / 状态重复计数 / 首屏语义块数。 */
export interface CompositionRule {
  id: string;
  metric: CompositionMetric;
  /** 被测量区域（content/inspector 的容器，gap 与 block 的扫描根）。 */
  selector?: string;
  /** occupancy 的容器（通常是 pane / workspace）。 */
  container?: string;
  /** primaryStatusRepeatCount 需要计数的完整文本。 */
  text?: string;
  min?: number;
  max?: number;
  severity: Severity;
  pages?: string[];
}

/** O6 状态完整性：截图前必须断言的真实页面状态（expected）。 */
export interface StateExpectation {
  page?: string;
  state?: string;
  fixture?: string;
  h1?: string;
  entityId?: string;
  resultCount?: number;
  selectedId?: string;
  componentCounts?: Array<{ selector: string; min: number }>;
}

export interface LanguageFlags {
  uuid?: boolean;
  enums?: boolean;
  invariants?: boolean;
  allcapsTokens?: boolean;
  /** ADR-/RFC-/TD-/AC-/PR- refs forbidden on consumer DOM（§17）。 */
  refs?: boolean;
}

export interface PageDef {
  id: string;
  route: string;
  /** The page requires a signed-in consumer: the oracle registers + logs in and
   * stores the token (same flow as the contribute-wizard e2e) before visiting. */
  auth?: boolean;
  /** Extra route manipulation for interaction (mobile filter click etc.). */
  interactions?: Array<{
    /** Playwright-ish: open sheet via filter toggle. */
    clickSelectors?: string[];
    waitForSelector?: string;
  }>;
  /** O6 capture-state integrity: expected real page state before capture. */
  expect?: StateExpectation;
}

export interface ContractSchema {
  id: string;
  title: string;
  viewport: { width: number; height: number };
  pages: PageDef[];
  elements?: ElementRule[];
  structure?: StructureRule[];
  density?: DensityRule[];
  hierarchy?: HierarchyRule[];
  budget?: BudgetRule[];
  composition?: CompositionRule[];
  language: LanguageFlags;
  notes?: string;
}

export interface ElementMeasurement {
  bbox: { x: number; y: number; width: number; height: number } | null;
  computed: Record<string, string>;
  count: number;
  ariaLabel: string;
  maxChildWidth: number | null;
  contentHeightInViewport: number | null;
  leftRelative: number | null;
  sectionGapAvg: number | null;
  rows: Array<{ height: number | null; borderRadius: string | null }>;
}

export interface StructureMeasurement {
  count: number;
  sampleClasses: string[];
  sampleText: string;
  surfaceRows: number;
  hasArrows: boolean;
  collapsed: boolean;
  visibleCountAfterClick: number | null;
  details: { forbiddenTextHits: string[]; missingRequiredTexts: string[] };
  /** O2: x spread (px) across all matched elements — 0 when every element shares one x. */
  xSpread: number | null;
}

export interface DensityMeasurement {
  largestVerticalGap: number | null;
  horizontalOverflowPx: number;
  infoBlockCount: number | null;
  firstViewportVisibleTextLines: number;
  contentHeightInViewport: number | null;
  primaryActionCount: number | null;
}

export interface HierarchyMeasurement {
  aFontSize: number | null;
  bFontSize: number | null;
  ratio: number | null;
}

export interface BudgetMeasurement {
  value: number | null;
}

export interface CompositionMeasurement {
  value: number | null;
}

export interface StateMeasurement {
  route: string;
  page: string | null;
  state: string | null;
  fixture: string | null;
  h1: string | null;
  entityId: string | null;
  resultCount: number | null;
  selectedId: string | null;
  componentCounts: Record<string, number>;
}

export interface LanguageMeasurement {
  uuidHits: string[];
  enumHits: string[];
  invariantHits: string[];
  allcapsHits: string[];
  refHits: string[];
}

export interface PageProbe {
  pageId: string;
  route: string;
  elements: Record<string, ElementMeasurement>;
  structure: Record<string, StructureMeasurement>;
  density: Record<string, DensityMeasurement>;
  hierarchy: Record<string, HierarchyMeasurement>;
  budget: Record<string, BudgetMeasurement>;
  composition: Record<string, CompositionMeasurement>;
  state: StateMeasurement;
  language: LanguageMeasurement;
  screenshot: string | null;
}

export interface ProbeArtifact {
  contractId: string;
  viewport: { width: number; height: number };
  generatedAt: string;
  pages: PageProbe[];
}

export interface CompareRow {
  id: string;
  kind:
    | "element"
    | "structure"
    | "density"
    | "hierarchy"
    | "budget"
    | "composition"
    | "state"
    | "language";
  target: RangeSpec | string | number;
  actual: unknown;
  result: "PASS" | "WARN" | "FAIL";
  detail: string;
}

export interface CompareArtifact {
  contractId: string;
  viewport: { width: number; height: number };
  generatedAt: string;
  rows: CompareRow[];
  summary: { PASS: number; WARN: number; FAIL: number };
}
