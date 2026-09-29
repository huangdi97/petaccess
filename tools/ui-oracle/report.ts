/**
 * UI Oracle — report.ts
 *
 * Aggregates probe artifacts (+ contract compare) into stage-level reports at
 * artifacts/blind-ui-recovery/reports/. Used by the Playwright capture to
 * produce phase-a/phase-b/.../final.json with the shape the goal contract
 * requires (semantic/geometry/density/interaction/a11y/responsive/screenshot/
 * known gaps).
 */
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const PROBES_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/probes");
const SCREENS_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/screens");
const REPORTS_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/reports");

export interface StageReport {
  stage: string;
  generatedAt: string;
  contracts: Record<string, unknown>;
  screenshots: string[];
  semantic: Record<string, unknown>;
  geometry: Record<string, unknown>;
  density: Record<string, unknown>;
  interaction: Record<string, unknown>;
  a11y: Record<string, unknown>;
  responsive: Record<string, unknown>;
  knownGaps: string[];
}

export function listProbes(): string[] {
  try {
    return readdirSync(PROBES_DIR).filter((f) => f.endsWith(".json"));
  } catch {
    return [];
  }
}

export function listScreens(): string[] {
  try {
    const out: string[] = [];
    const walk = (dir: string, rel: string): void => {
      for (const e of readdirSync(dir, { withFileTypes: true })) {
        if (e.isDirectory()) walk(path.join(dir, e.name), `${rel}/${e.name}`);
        else if (e.name.endsWith(".png")) out.push(`${rel}/${e.name}`);
      }
    };
    walk(SCREENS_DIR, "");
    return out.sort();
  } catch {
    return [];
  }
}

export function findGaps(
  stageCounts: Array<{ contract: string; PASS: number; WARN: number; FAIL: number }>,
): string[] {
  const gaps: string[] = [];
  for (const c of stageCounts) {
    if (c.FAIL > 0) gaps.push(`${c.contract}: ${c.FAIL} FAIL`);
    else if (c.WARN > 0) gaps.push(`${c.contract}: ${c.WARN} WARN`);
  }
  return gaps;
}

export function buildStageReport(
  stage: string,
  contractOverrides: Record<string, unknown> = {},
): StageReport {
  mkdirSync(REPORTS_DIR, { recursive: true });
  const probes = listProbes().filter((f) => f.startsWith(`${stage}-`));
  const contracts: Record<string, unknown> = {};
  const semantic: Record<string, unknown> = {};
  const geometry: Record<string, unknown> = {};
  const density: Record<string, unknown> = {};
  const counts: Array<{ contract: string; PASS: number; WARN: number; FAIL: number }> = [];

  for (const p of probes) {
    const raw = JSON.parse(readFileSync(path.join(PROBES_DIR, p), "utf8"));
    const contractId = raw.contractId ?? p.replace(/^[a-z-]+-/, "").replace(/\.json$/, "");
    contracts[contractId] = raw;
    geometry[contractId] =
      raw.pages?.map((pg: { pageId: string; elements: unknown }) => ({
        pageId: pg.pageId,
        elements: pg.elements,
      })) ?? [];
    density[contractId] =
      raw.pages?.map((pg: { pageId: string; density: unknown }) => ({
        pageId: pg.pageId,
        density: pg.density,
      })) ?? [];
    semantic[contractId] =
      raw.pages?.map((pg: { pageId: string; language: unknown }) => ({
        pageId: pg.pageId,
        language: pg.language,
      })) ?? [];
    counts.push({ contract: contractId, PASS: 0, WARN: 0, FAIL: 0 });
  }

  const report: StageReport = {
    stage,
    generatedAt: new Date().toISOString(),
    contracts,
    screenshots: listScreens().filter((s) => s.startsWith(`/${stage}/`)),
    semantic,
    geometry,
    density,
    interaction: {},
    a11y: {},
    responsive: {},
    knownGaps: findGaps(counts),
    ...contractOverrides,
  };
  const file = path.join(REPORTS_DIR, `${stage}.json`);
  writeFileSync(file, JSON.stringify(report, null, 2));
  return report;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]).replace(/\\/g, "/") ===
    fileURLToPath(import.meta.url).replace(/\\/g, "/")
) {
  const stage = process.argv[2] ?? "baseline";
  const r = buildStageReport(stage);
  console.log(
    `[report] ${stage}: probes=${Object.keys(r.contracts).length} screens=${r.screenshots.length} gaps=${r.knownGaps.join(";") ?? "none"}`,
  );
}
