/**
 * UI Oracle — probe.ts
 *
 * In-page measurement functions. Each is a self-contained DOM function that is
 * passed to `page.evaluate(fn, arg)` — no imports, no outer closures, so
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

  return {
    count: nodes.length,
    sampleClasses,
    sampleText: sample ? ((sample as HTMLElement).innerText ?? "").slice(0, 200) : "",
    surfaceRows,
    forbiddenTextHits,
    missingRequiredTexts,
    hasArrows,
    collapsed,
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

/** Visible text scan — pure function over body innerText. Node-side usable too. */
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
