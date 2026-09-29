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
 *   - language:  visible-text scan flags (uuid / enums / invariants / ALL_CAPS).
 */
export type Severity = "FAIL" | "WARN";

export interface RangeSpec {
  min?: number;
  max?: number;
  equals?: string | number;
  warnAt?: number;
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
}

export interface LanguageFlags {
  uuid?: boolean;
  enums?: boolean;
  invariants?: boolean;
  allcapsTokens?: boolean;
}

export interface ContractSchema {
  id: string;
  title: string;
  viewport: { width: number; height: number };
  pages: PageDef[];
  elements?: ElementRule[];
  structure?: StructureRule[];
  density?: DensityRule[];
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
}

export interface DensityMeasurement {
  largestVerticalGap: number | null;
  horizontalOverflowPx: number;
  infoBlockCount: number | null;
  firstViewportVisibleTextLines: number;
  contentHeightInViewport: number | null;
  primaryActionCount: number | null;
}

export interface LanguageMeasurement {
  uuidHits: string[];
  enumHits: string[];
  invariantHits: string[];
  allcapsHits: string[];
}

export interface PageProbe {
  pageId: string;
  route: string;
  elements: Record<string, ElementMeasurement>;
  structure: Record<string, StructureMeasurement>;
  density: Record<string, DensityMeasurement>;
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
  kind: "element" | "structure" | "density" | "language";
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
