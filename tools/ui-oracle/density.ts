/**
 * UI Oracle — density.ts
 *
 * Density-aware thresholds expressed as importable constants so compare.ts and
 * the Playwright gate share one source of truth. All values trace to
 * GLOBAL_UI_CONTRACT.md §6 (Dense but Quiet).
 */
export const DENSITY_LIMITS = {
  /** Desktop: no >180px meaningless vertical gap between semantic sections. */
  maxSemanticGapDesktop: 180,
  /** Mobile: same ceiling for non-map pages. */
  maxSemanticGapMobile: 180,
  /** Desktop 900px viewport: at least this many meaningful info blocks. */
  minInfoBlocksDesktop: 3,
  /** Mobile first viewport visible text lines — warn at 30, fail at 40+. */
  mobileFirstViewportLinesWarn: 30,
  mobileFirstViewportLinesFail: 40,
  /** Detail 首屏高度（selected place 存在时）。 */
  searchDetailFirstViewportMin: 360,
  /** 非地图页面主要区域空白占比 ≤ 60%。 */
  maxWhitespaceRatioDesktop: 0.6,
} as const;

export interface DensityReport {
  region: string;
  visibleTextLines: number;
  elementCount: number;
  headingCount: number;
  interactiveCount: number;
  contentBoundingArea: number;
  regionArea: number;
  estimatedWhitespaceRatio: number;
  largestVerticalGap: number;
  resultRowDensity: number;
  metadataLineCount: number;
  firstViewportInfoCount: number;
}

export function whitespaceRatio(contentArea: number, regionArea: number): number {
  if (regionArea <= 0) return 1;
  return Math.max(0, 1 - contentArea / regionArea);
}

export function gapVerdictPx(gap: number, mobile = false): "PASS" | "FAIL" {
  return gap <=
    (mobile ? DENSITY_LIMITS.maxSemanticGapMobile : DENSITY_LIMITS.maxSemanticGapDesktop)
    ? "PASS"
    : "FAIL";
}

export function firstViewportVerdict(lines: number): "PASS" | "WARN" | "FAIL" {
  if (lines <= DENSITY_LIMITS.mobileFirstViewportLinesWarn) return "PASS";
  if (lines <= DENSITY_LIMITS.mobileFirstViewportLinesFail) return "WARN";
  return "FAIL";
}
