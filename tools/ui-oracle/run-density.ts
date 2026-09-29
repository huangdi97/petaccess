/**
 * UI Oracle — run-density.ts
 *
 * Consolidated density summary from probe artifacts. Prints per-contract
 * density verdicts using the Dense-but-Quiet thresholds (density.ts). Output:
 * artifacts/blind-ui-recovery/reports/density-{stage}.json
 *
 * Run: node --experimental-strip-types tools/ui-oracle/run-density.ts <stage>
 */
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { DENSITY_LIMITS } from "./density.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const PROBES_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/probes");
const REPORTS_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/reports");
const CONTRACTS_DIR = path.join(ROOT, "docs/ui/contracts/json");

const STAGE = process.argv[2] ?? "baseline";

interface DensityRow {
  contractId: string;
  pageId: string;
  largestVerticalGap: number | null;
  gapVerdict: "PASS" | "FAIL" | "n/a";
  whitespaceRatio: number | null;
  whitespaceVerdict: "PASS" | "FAIL" | "n/a";
  infoBlocks: number | null;
  firstViewportLines: number;
  linesVerdict: "PASS" | "WARN" | "FAIL";
}

export function runDensity(stage: string): DensityRow[] {
  mkdirSync(REPORTS_DIR, { recursive: true });
  const rows: DensityRow[] = [];
  const files = (() => {
    try {
      return readdirSync(PROBES_DIR).filter(
        (f) => f.startsWith(`${stage}-`) && f.endsWith(".json"),
      );
    } catch {
      return [];
    }
  })();
  for (const f of files) {
    let raw: {
      contractId: string;
      viewport?: { width: number; height: number };
      pages: Array<{
        pageId: string;
        density: Record<
          string,
          {
            largestVerticalGap: number | null;
            horizontalOverflowPx: number;
            infoBlockCount: number;
            firstViewportVisibleTextLines: number;
            contentHeightInViewport: number | null;
          }
        >;
      }>;
    };
    try {
      raw = JSON.parse(readFileSync(path.join(PROBES_DIR, f), "utf8"));
    } catch {
      continue;
    }
    // The first-viewport line budget is a *mobile* budget (density.ts doc):
    // desktop list-detail pages legitimately show more text lines, so the
    // diagnostic only applies it to <1000px contracts. Desktop verdicts come
    // from the contract rules in compare.ts, which are the machine gate.
    const isMobile = (raw.viewport?.width ?? 1440) < 1000;
    // Where the contract defines the first-viewport-lines budget itself (e.g.
    // place.mobile warnAt=30/max=40), use the contract's verdict so this
    // diagnostic and the compare gate agree; otherwise fall back to the global
    // mobile heuristic and skip desktop pages entirely.
    let contractLinesRule: { min?: number; max?: number; warnAt?: number } | undefined;
    try {
      const c = JSON.parse(
        readFileSync(path.join(CONTRACTS_DIR, `${raw.contractId ?? f}.json`), "utf8"),
      ) as {
        density?: Array<{ metric?: string; min?: number; max?: number; warnAt?: number }>;
      };
      contractLinesRule = c.density?.find((r) => r.metric === "firstViewportVisibleTextLines");
    } catch {
      contractLinesRule = undefined;
    }
    for (const page of raw.pages ?? []) {
      const d = Object.values(page.density ?? {})[0];
      if (!d) continue;
      const gap = d.largestVerticalGap;
      const info = d.infoBlockCount;
      const lines = d.firstViewportVisibleTextLines;
      rows.push({
        contractId: raw.contractId ?? f,
        pageId: page.pageId,
        largestVerticalGap: gap,
        gapVerdict:
          gap === null ? "n/a" : gap <= DENSITY_LIMITS.maxSemanticGapDesktop ? "PASS" : "FAIL",
        whitespaceRatio: null,
        whitespaceVerdict: "n/a",
        infoBlocks: info,
        firstViewportLines: lines,
        linesVerdict: contractLinesRule
          ? lines <= (contractLinesRule.max ?? DENSITY_LIMITS.mobileFirstViewportLinesFail)
            ? "PASS"
            : contractLinesRule.warnAt !== undefined && lines > contractLinesRule.warnAt
              ? "WARN"
              : "FAIL"
          : isMobile
            ? lines <= DENSITY_LIMITS.mobileFirstViewportLinesWarn
              ? "PASS"
              : lines <= DENSITY_LIMITS.mobileFirstViewportLinesFail
                ? "WARN"
                : "FAIL"
            : "n/a",
      });
    }
  }
  writeFileSync(
    path.join(REPORTS_DIR, `density-${stage}.json`),
    JSON.stringify({ stage, generatedAt: new Date().toISOString(), rows }, null, 2),
  );
  return rows;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]).replace(/\\/g, "/") ===
    fileURLToPath(import.meta.url).replace(/\\/g, "/")
) {
  const rows = runDensity(STAGE);
  for (const r of rows) {
    console.log(
      `[density:${STAGE}] ${r.contractId}/${r.pageId}: gap=${r.gapVerdict}(${r.largestVerticalGap ?? "-"}px) infoBlocks=${r.infoBlocks ?? "-"} lines=${r.linesVerdict}(${r.firstViewportLines})`,
    );
  }
  const fails = rows.filter((r) => r.gapVerdict === "FAIL" || r.linesVerdict === "FAIL");
  console.log(`[density:${STAGE}] total=${rows.length} FAIL=${fails.length}`);
}
