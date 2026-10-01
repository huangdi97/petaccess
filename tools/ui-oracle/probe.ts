/**
 * UI Oracle 鈥?probe.ts
 *
 * In-page measurement functions. Each is a self-contained DOM function that is
 * passed to `page.evaluate(fn, arg)` 鈥?no imports, no outer closures, so
 * Playwright can serialize it into the page. All values come from
 * getBoundingClientRect() / getComputedStyle() / innerText. Screenshots are
 * never interpreted here; they are evidence artifacts only.
 *
 * The spec (tests/ui-oracle/oracle.spec.ts) drives these per contract page and
 * writes the raw probe JSON to artifacts/blind-ui-recovery/probes/.
 */

export interface ElementRuleArg {
  ui?: string;
  fallbacks?: string[];
  aggregate?: "rows";
}

export function resolveSelector(root: Element, ui?: string, fallbacks?: string[]): Element | null {
  if (ui && root.querySelector(`[data-ui="${ui}"]`)) {
    return root.querySelector(`[data-ui="${ui}"]`);
  }
  for (const fb of fallbacks ?? []) {
    const hit = root.querySelector(fb);
    if (hit) return hit;
  }
  return null;
}

export interface ElementMeasurementFlat {
  x: number | null;
  y: number | null;
  width: number | null;
  height: number | null;
  fontSize: string | null;
  fontWeight: string | null;
  lineHeight: string | null;
  padding: string | null;
  margin: string | null;
  borderRadius: string | null;
  boxShadow: string | null;
  backgroundColor: string | null;
  position: string | null;
  overflow: string | null;
  gap: string | null;
  borderBottomWidth: string | null;
  gridTemplateColumns: string | null;
  ariaLabel: string;
  count: number;
  maxChildWidth: number | null;
  contentHeightInViewport: number | null;
  leftRelative: number | null;
  sectionGapAvg: number | null;
  rows: Array<{ height: number | null; borderRadius: string | null }>;
}

export function measureElement(
  root: Element,
  ui?: string,
  fallbacks?: string[],
): ElementMeasurementFlat {
  const owned = resolveSelector(root, ui, fallbacks);
  const nodes = owned ? [owned] : [];
  const all: Element[] = [];
  if (ui) all.push(...Array.from(root.querySelectorAll(`[data-ui="${ui}"]`)));
  for (const fb of fallbacks ?? []) {
    if (all.length === 0) all.push(...Array.from(root.querySelectorAll(fb)));
  }
  const count = Math.max(nodes.length, all.length);
  const el = owned ?? all[0] ?? null;

  if (!el) {
    return {
      x: null,
      y: null,
      width: null,
      height: null,
      fontSize: null,
      fontWeight: null,
      lineHeight: null,
      padding: null,
      margin: null,
      borderRadius: null,
      boxShadow: null,
      backgroundColor: null,
      position: null,
      overflow: null,
      gap: null,
      borderBottomWidth: null,
      gridTemplateColumns: null,
      ariaLabel: "",
      count,
      maxChildWidth: null,
      contentHeightInViewport: null,
      leftRelative: null,
      sectionGapAvg: null,
      rows: [],
    };
  }

  const rect = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  const vpHeight = window.innerHeight;

  const maxChildWidth = (start: Element): number => {
    let maxW = start.getBoundingClientRect().width;
    const walker = document.createTreeWalker(start, NodeFilter.SHOW_ELEMENT);
    let depth = 0;
    let node: Node | null;
    while ((node = walker.nextNode()) && depth < 400) {
      depth += 1;
      if (node instanceof HTMLElement) {
        const r = node.getBoundingClientRect();
        if (r.width > 0 && r.width < 2000) maxW = Math.max(maxW, r.width);
      }
    }
    return maxW;
  };

  const topOfContent = el.getBoundingClientRect().top;
  const visibleH = Math.max(0, Math.min(rect.height, vpHeight - topOfContent));

  const sectionGap = (start: Element): number | null => {
    const blocks = Array.from(
      start.querySelectorAll("section, article, [class*='section'], h2, h3, [class*='row']"),
    )
      .map((b) => b.getBoundingClientRect())
      .filter((r) => r.height > 0 && r.top >= 0);
    if (blocks.length < 2) return null;
    blocks.sort((a, b) => a.top - b.top);
    const gaps: number[] = [];
    for (let i = 1; i < blocks.length; i += 1) {
      const gap = blocks[i]!.top - (blocks[i - 1]!.top + blocks[i - 1]!.height);
      if (gap > 0 && gap < 600) gaps.push(gap);
    }
    if (gaps.length === 0) return null;
    gaps.sort((a, b) => a - b);
    return gaps[Math.floor(gaps.length / 2)]!;
  };

  const rowEls =
    (ui ? Array.from(root.querySelectorAll(`[data-ui="${ui}"]`)) : []).length > 0
      ? Array.from(root.querySelectorAll(`[data-ui="${ui}"]`))
      : all;

  const rows = rowEls.slice(0, 6).map((r) => {
    const rr = r.getBoundingClientRect();
    const rcs = getComputedStyle(r);
    return { height: rr.height, borderRadius: rcs.borderRadius };
  });

  return {
    x: rect.x,
    y: rect.y,
    width: rect.width,
    height: rect.height,
    fontSize: cs.fontSize,
    fontWeight: cs.fontWeight,
    lineHeight: cs.lineHeight,
    padding: cs.padding,
    margin: cs.margin,
    borderRadius: cs.borderRadius,
    boxShadow: cs.boxShadow,
    backgroundColor: cs.backgroundColor,
    position: cs.position,
    overflow: cs.overflow,
    gap: cs.gap,
    borderBottomWidth: cs.borderBottomWidth,
    gridTemplateColumns: cs.gridTemplateColumns,
    ariaLabel: el.getAttribute("aria-label") ?? "",
    count,
    maxChildWidth: maxChildWidth(el),
    contentHeightInViewport: visibleH,
    leftRelative: leftRelativeToPane(el),
    sectionGapAvg: sectionGap(el),
    rows,
  };
}

export function leftRelativeToPane(el: Element): number | null {
  let node: Element | null = el.parentElement;
  while (node) {
    const ui = node.getAttribute("data-ui") ?? "";
    const cls = node.getAttribute("class") ?? "";
    if (ui.includes("-pane") || /inspector/i.test(ui) || /inspector/i.test(cls)) {
      return el.getBoundingClientRect().left - node.getBoundingClientRect().left;
    }
    node = node.parentElement;
  }
  return el.getBoundingClientRect().left;
}

export interface StructureRuleArg {
  selector: string;
  fallbackSelector?: string;
  forbiddenClass?: string[];
  forbiddenText?: string[];
  mustContainText?: string;
  mustContainTexts?: string[];
  containsArrows?: boolean;
  surfaceRowCount?: { min?: number; max?: number };
  disclosureDefault?: "collapsed";
  /** O2: every matched element must share the same x (timeline time col / marker col). */
  xConsistent?: boolean;
  /** O5-v4：首屏门 —— 命中元素的首屏可见数量下限。 */
  minVisibleInViewport?: number;
}

export interface StructureMeasurementFlat {
  count: number;
  sampleClasses: string[];
  sampleText: string;
  surfaceRows: number;
  forbiddenTextHits: string[];
  missingRequiredTexts: string[];
  hasArrows: boolean;
  collapsed: boolean;
  xSpread: number | null;
  /** O5-v4：命中元素中首屏可见的数量（top < viewport height）。 */
  visibleInViewport: number;
}

export function measureStructure(root: Element, arg: StructureRuleArg): StructureMeasurementFlat {
  const sel = root.querySelector(arg.selector)
    ? arg.selector
    : (arg.fallbackSelector ?? arg.selector);
  const nodes = Array.from(root.querySelectorAll(sel));
  const sample = nodes[0];

  const text = nodes
    .map((n) => (n as HTMLElement).innerText ?? "")
    .join("\n")
    .slice(0, 4000);

  const forbiddenTextHits: string[] = [];
  for (const t of arg.forbiddenText ?? []) {
    if (text.includes(t)) forbiddenTextHits.push(t);
  }
  const missingRequiredTexts: string[] = [];
  const must = [
    ...(arg.mustContainText ? [arg.mustContainText] : []),
    ...(arg.mustContainTexts ?? []),
  ];
  for (const t of must) {
    const bodyText = (root as HTMLElement).innerText ?? "";
    if (!bodyText.includes(t)) missingRequiredTexts.push(t);
  }

  const sampleClasses = nodes
    .slice(0, 3)
    .map((n) => n.getAttribute("class") ?? "")
    .filter((c) => c.length > 0);

  // A node "is a card" if it carries a forbidden class (sampled classes are
  // enough for pill-wall / card-wall gates).
  const surfaceRows = sample ? sample.querySelectorAll(".surface-row").length : 0;

  const hasArrows = arg.containsArrows
    ? nodes.some((n) => {
        const txt = (n as HTMLElement).innerText ?? "";
        return (
          txt.includes("→") ||
          txt.includes("›") ||
          (n as HTMLElement).querySelector("[class*='chevron'], [class*='arrow']") !== null
        );
      })
    : false;
  const collapsed = arg.disclosureDefault === "collapsed" ? checkCollapsed(nodes) : false;

  // O2 几何：全部命中元素共享同一 x（timeline time col / marker col 对齐）。
  const lefts = nodes.map((n) => n.getBoundingClientRect().left).filter((v) => Number.isFinite(v));
  const xSpread = lefts.length >= 2 ? Math.max(...lefts) - Math.min(...lefts) : null;
  // O5-v4 首屏门：命中元素中哪些顶部落在首屏内（top < viewport height）。
  const visibleInViewport = nodes.filter((n) => {
    const r = n.getBoundingClientRect();
    return r.top >= 0 && r.top < window.innerHeight && r.height > 0;
  }).length;

  return {
    count: nodes.length,
    sampleClasses,
    sampleText: sample ? ((sample as HTMLElement).innerText ?? "").slice(0, 200) : "",
    surfaceRows,
    forbiddenTextHits,
    missingRequiredTexts,
    hasArrows,
    collapsed,
    xSpread,
    visibleInViewport,
  };
}

export function checkCollapsed(nodes: Element[]): boolean {
  for (const n of nodes) {
    const c = n.getAttribute("aria-expanded");
    if (c === "false") return true;
    const inner = n.querySelector('[aria-expanded="false"]');
    if (inner) return true;
  }
  // Histories hidden by default: content not visible in viewport.
  return false;
}

export interface DensityRegionArg {
  selector: string;
  fallbackSelector?: string;
}

export interface DensityFlat {
  largestVerticalGap: number | null;
  horizontalOverflowPx: number;
  infoBlockCount: number;
  firstViewportVisibleTextLines: number;
  contentHeightInViewport: number | null;
  primaryActionCount: number;
}

export function measureDensity(root: Element, arg: DensityRegionArg | null): DensityFlat {
  const doc = root.ownerDocument ?? document;
  const vpHeight = window.innerHeight;

  let regionEl: Element | null = null;
  if (arg) {
    const sel = root.querySelector(arg.selector)
      ? arg.selector
      : (arg.fallbackSelector ?? arg.selector);
    regionEl = root.querySelector(sel);
  }

  const largestVerticalGap = ((): number | null => {
    if (!regionEl) return null;
    const kids = Array.from(regionEl.children)
      .map((k) => {
        const r = k.getBoundingClientRect();
        return { top: r.top, bottom: r.bottom, height: r.height };
      })
      .filter((r) => r.height > 0);
    if (kids.length < 2) return null;
    kids.sort((a, b) => a.top - b.top);
    let maxGap = 0;
    for (let i = 1; i < kids.length; i += 1) {
      const gap = kids[i]!.top - kids[i - 1]!.bottom;
      if (gap > maxGap) maxGap = gap;
    }
    return maxGap;
  })();

  const horizontalOverflowPx = Math.max(
    0,
    doc.documentElement.scrollWidth - doc.documentElement.clientWidth,
  );

  const infoBlockCount = regionEl
    ? regionEl.querySelectorAll("section, article, [class*='section'], [class*='block'], h2, h3")
        .length
    : doc.querySelectorAll("section, article, h2, h3").length;

  const firstViewportVisibleTextLines = ((): number => {
    const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
    let lines = 0;
    let node: Node | null;
    const seen = new Set<string>();
    while ((node = walker.nextNode()) && lines < 400) {
      const t = (node.textContent ?? "").trim();
      if (!t) continue;
      const el = node.parentElement;
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.top < 0 || r.top > vpHeight) continue;
      const key = t.slice(0, 24);
      if (seen.has(key)) continue;
      seen.add(key);
      lines += 1;
      // Long blocks count more than one visual line (rough estimate).
      lines += Math.max(0, Math.floor((r.height - 4) / 18) - 1);
    }
    return lines;
  })();

  const contentHeightInViewport = regionEl
    ? Math.max(
        0,
        Math.min(
          regionEl.getBoundingClientRect().height,
          vpHeight - regionEl.getBoundingClientRect().top,
        ),
      )
    : null;

  const primaryActionCount = regionEl
    ? regionEl.querySelectorAll(
        "a.primary, button.primary, [data-testid*='go-'], [class*='primary']",
      ).length
    : doc.querySelectorAll("a.primary, button.primary").length;

  return {
    largestVerticalGap,
    horizontalOverflowPx,
    infoBlockCount,
    firstViewportVisibleTextLines,
    contentHeightInViewport,
    primaryActionCount,
  };
}

/** Visible text scan 鈥?pure function over body innerText. Node-side usable too. */
export interface LanguageScanFlat {
  uuidHits: string[];
  enumHits: string[];
  invariantHits: string[];
  allcapsHits: string[];
}

const UUID_RE = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/i;
const UUID_PREFIX_RE = /\b[0-9a-f]{8}-(?![0-9a-f]{4}-)/i;
const SNAKE_RE = /\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b/g;
const ALLCAPS_RE = /\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b/g;
const KNOWN_SAFE_ALLCAPS = new Set([
  "NO_RECENT_RECORD",
  "INSUFFICIENT_OBSERVATION",
  "OBSERVED_RECENTLY",
  "MULTI_EVIDENCE_OBSERVED",
  "RULE_REALITY_ALIGNED",
  "POTENTIAL_CONFLICT",
  "REVIEW_REQUIRED",
]);

export function scanLanguage(text: string): LanguageScanFlat {
  const uuidHits: string[] = [];
  const enumHits: string[] = [];
  const invariantHits: string[] = [];
  const allcapsHits: string[] = [];

  const m1 = text.match(UUID_RE);
  if (m1) uuidHits.push(m1[0]!);
  const m2 = text.match(UUID_PREFIX_RE);
  if (m2) uuidHits.push(m2[0]!);

  const snake = text.match(SNAKE_RE) ?? [];
  for (const s of snake) {
    if (KNOWN_SAFE_ALLCAPS.has(s)) continue;
    if (s.length < 4) continue;
    enumHits.push(s);
  }
  const caps = text.match(ALLCAPS_RE) ?? [];
  for (const s of caps) {
    if (KNOWN_SAFE_ALLCAPS.has(s)) continue;
    allcapsHits.push(s);
  }
  for (const inv of KNOWN_SAFE_ALLCAPS) {
    if (text.includes(inv)) invariantHits.push(inv);
  }
  return { uuidHits, enumHits, invariantHits, allcapsHits };
}

/* --- v0.2.3 Oracle v2: O3 hierarchy / O4 budget / O5 composition / O6 state - */

export interface HierarchyArg {
  a: string;
  b: string;
}

export interface HierarchyFlat {
  aFontSize: number | null;
  bFontSize: number | null;
  ratio: number | null;
}

export function firstEl(root: Element, sel: string): Element | null {
  return sel === "body" ? root : root.querySelector(sel);
}

export function pxValue(cs: CSSStyleDeclaration): number | null {
  const m = cs.fontSize.match(/^([\d.]+)px$/);
  return m ? Number(m[1]) : null;
}

/** O3: ratio = fontSize(a) / fontSize(b) for the first matching elements. */
export function measureHierarchy(root: Element, arg: HierarchyArg): HierarchyFlat {
  const a = firstEl(root, arg.a);
  const b = firstEl(root, arg.b);
  const aFontSize = a ? pxValue(getComputedStyle(a)) : null;
  const bFontSize = b ? pxValue(getComputedStyle(b)) : null;
  const ratio =
    aFontSize !== null && bFontSize !== null && bFontSize > 0
      ? Math.round((aFontSize / bFontSize) * 100) / 100
      : null;
  return { aFontSize, bFontSize, ratio };
}

export interface BudgetArg {
  metric: "rowTextLines" | "firstViewportBlocks" | "firstViewportTextLines";
  selector?: string;
}

/** Count visible text lines within an element (true rendered line boxes). */
export function visibleLinesIn(el: Element): number {
  const rect = el.getBoundingClientRect();
  const vp = window.innerHeight;
  if (rect.height <= 0 || rect.top > vp) return 0;
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let node: Node | null;
  const tops = new Set<number>();
  while ((node = walker.nextNode())) {
    const t = (node.textContent ?? "").trim();
    if (!t) continue;
    const parent = node.parentElement;
    // Skip SR-only / aria-hidden text: it is not a visual line and must not
    // inflate the content-budget (v0.2.3 §21.5 row ≤5 lines).
    if (!(parent instanceof HTMLElement)) continue;
    const hidden = parent.closest(".visually-hidden, [aria-hidden='true'], .sr-only");
    if (hidden) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const rects = Array.from(range.getClientRects());
    for (const r of rects) {
      // Only lines that actually intersect the first viewport.
      if (r.height <= 0 || r.width <= 0 || r.bottom < 0 || r.top > vp) continue;
      // Bucket tops within ~6px: inline labels (status badge) share the same
      // visual line as their anchor text (name), so they must count as ONE
      // text line — genuine lines are ≥ line-height (~18px) apart.
      tops.add(Math.round(r.top / 6) * 6);
    }
    range.detach();
  }
  return tops.size;
}

export interface BudgetFlat {
  value: number | null;
}

/** O4: content-budget metrics over a region / first viewport. */
export function measureBudget(root: Element, arg: BudgetArg): BudgetFlat {
  const region = arg.selector ? (root.querySelector(arg.selector) ?? root) : root;
  switch (arg.metric) {
    case "rowTextLines": {
      // Aggregated over every row match: each row's visible text lines.
      const rows = Array.from(region.querySelectorAll("[data-ui*='row' i], li")).filter(
        (el) => el.getBoundingClientRect().height > 0,
      );
      if (rows.length === 0) return { value: visibleLinesIn(region) };
      const perRow = rows.map((r) => visibleLinesIn(r));
      return { value: Math.max(...perRow) };
    }
    case "firstViewportBlocks": {
      const vp = window.innerHeight;
      const blocks = Array.from(
        region.querySelectorAll(
          "[data-ui-block], section, article, h2, h3, [class*='section'], [class*='block']",
        ),
      ).filter((el) => {
        const r = el.getBoundingClientRect();
        return r.height > 0 && r.top >= 0 && r.top < vp;
      });
      return { value: blocks.length };
    }
    case "firstViewportTextLines":
      return { value: countFirstViewportTextLines(region) };
    default:
      return { value: null };
  }
}

/** Visible text lines in first viewport of whole body (shared with density). */
export function countFirstViewportTextLines(root: Element): number {
  const vp = window.innerHeight;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let lines = 0;
  let node: Node | null;
  const seen = new Set<string>();
  while ((node = walker.nextNode()) && lines < 400) {
    const t = (node.textContent ?? "").trim();
    if (!t) continue;
    const el = node.parentElement;
    if (!el) continue;
    const r = el.getBoundingClientRect();
    if (r.top < 0 || r.top > vp) continue;
    const key = t.slice(0, 24);
    if (seen.has(key)) continue;
    seen.add(key);
    const cs = getComputedStyle(el);
    const lh = pxValue(cs);
    lines += 1;
    if (lh) lines += Math.max(0, Math.floor((r.height - 4) / lh) - 1);
  }
  return lines;
}

export interface CompositionArg {
  metric:
    | "contentOccupancy"
    | "inspectorOccupancy"
    | "largestVerticalGap"
    | "primaryStatusRepeatCount"
    | "semanticBlockCount";
  selector?: string;
  container?: string;
  text?: string;
}

export interface CompositionFlat {
  value: number | null;
}

export function widestChildRatio(content: Element, container: Element): number {
  const cw = container.getBoundingClientRect().width;
  if (cw <= 0) return 0;
  const contentWidth = content.getBoundingClientRect().width;
  const maxChild = Array.from(content.children).reduce((max, ch) => {
    const w = ch.getBoundingClientRect().width;
    return w > max ? w : max;
  }, contentWidth);
  return Math.round((Math.min(maxChild, cw) / cw) * 100) / 100;
}

/** O5: composition metrics (occupancy / gap / status-repeat / block count). */
export function measureComposition(root: Element, arg: CompositionArg): CompositionFlat {
  const region = arg.selector ? (root.querySelector(arg.selector) ?? root) : root;
  switch (arg.metric) {
    case "contentOccupancy": {
      const container = arg.container ? (root.querySelector(arg.container) ?? root) : root;
      return { value: widestChildRatio(region, container) };
    }
    case "inspectorOccupancy": {
      const container = arg.container ? (root.querySelector(arg.container) ?? root) : root;
      const cw = container.getBoundingClientRect().width;
      if (cw <= 0) return { value: 0 };
      const w = region.getBoundingClientRect().width;
      return { value: Math.round((w / cw) * 100) / 100 };
    }
    case "largestVerticalGap": {
      const kids = Array.from(region.children)
        .map((k) => k.getBoundingClientRect())
        .filter((r) => r.height > 0 && r.top >= 0);
      if (kids.length < 2) return { value: 0 };
      kids.sort((a, b) => a.top - b.top);
      let maxGap = 0;
      for (let i = 1; i < kids.length; i += 1) {
        maxGap = Math.max(maxGap, kids[i]!.top - kids[i - 1]!.bottom);
      }
      return { value: maxGap };
    }
    case "primaryStatusRepeatCount": {
      if (!arg.text) return { value: 0 };
      const vp = window.innerHeight;
      const hits = Array.from(region.querySelectorAll("div, span, p, h1, h2, h3, section")).filter(
        (el) => {
          const r = el.getBoundingClientRect();
          if (r.height <= 0 || r.top < 0 || r.top > vp) return false;
          const own = (el.textContent ?? "").trim();
          if (own !== arg.text) return false;
          // Only count leaf-ish nodes (no descendant with identical full text).
          const children = Array.from(el.children);
          return !children.some((c) => (c.textContent ?? "").trim() === own);
        },
      );
      return { value: hits.length };
    }
    case "semanticBlockCount": {
      const vp = window.innerHeight;
      const blocks = Array.from(
        region.querySelectorAll(
          "[data-ui-block], section, article, h2, h3, [class*='section'], [class*='block']",
        ),
      ).filter((el) => {
        const r = el.getBoundingClientRect();
        return r.height > 0 && r.top >= 0 && r.top < vp;
      });
      return { value: blocks.length };
    }
    default:
      return { value: null };
  }
}

export interface StateArg {
  page?: string;
  state?: string;
  fixture?: string;
  componentCounts?: Array<{ selector: string; min: number }>;
}

export interface StateFlat {
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

/** O6: real captured page state read from DOM / URL (never hand-written). */
export function measureState(root: Element, _arg: StateArg | null): StateFlat {
  const host = root.querySelector("[data-ui-page]") ?? root;
  const h1 = root.querySelector("h1");
  const resultCountEl = root.querySelector("[data-ui='search-count']");
  const selected = root.querySelector("[data-ui*='selected']");
  const counts: Record<string, number> = {};
  for (const el of root.querySelectorAll("[data-ui-count]")) {
    const name = el.getAttribute("data-ui-count") ?? "";
    if (name) counts[name] = Number(el.textContent ?? NaN) || 0;
  }
  return {
    route: location.hash,
    page: host.getAttribute("data-ui-page"),
    state: host.getAttribute("data-ui-state"),
    fixture: host.getAttribute("data-ui-fixture"),
    h1: h1 ? (h1.textContent ?? "").trim() : null,
    entityId:
      host.getAttribute("data-ui-entity-id") ??
      host.getAttribute("data-entity-id") ??
      location.hash.match(/place\/([0-9a-f-]{36})/i)?.[1] ??
      null,
    resultCount: resultCountEl ? Number(resultCountEl.textContent ?? NaN) || null : null,
    selectedId: selected?.getAttribute("data-ui") ?? null,
    componentCounts: counts,
  };
}

/* --- language v0.2.3: refs (ADR/RFC/TD/AC/PR) scan ------------------------ */

const ADR_RE = /\bADR-\d+\b/gi;
const RFC_RE = /\bRFC-\d+\b/gi;
const TD_RE = /\bTD-\d+\b/gi;
const AC_RE = /\bAC-[A-Z0-9-]+\b/gi;
const PR_RE = /\bPR-\d+\b/gi;

export function scanRefs(text: string): string[] {
  const out = new Set<string>();
  for (const re of [ADR_RE, RFC_RE, TD_RE, AC_RE, PR_RE]) {
    for (const m of text.matchAll(re)) out.add(m[0].toUpperCase());
  }
  return [...out].sort();
}
