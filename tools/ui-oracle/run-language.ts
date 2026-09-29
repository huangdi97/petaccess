/**
 * UI Oracle — run-language.ts
 *
 * Node-side language scan over probe artifacts already captured by the
 * Playwright stage run. Reads artifacts/blind-ui-recovery/probes/{stage}-*.json
 * and writes a consolidated language-scan.json at
 * artifacts/blind-ui-recovery/language-scan.json.
 *
 * Run: node --experimental-strip-types tools/ui-oracle/run-language.ts <stage>
 */
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { LanguageMeasurement, PageProbe } from "./contracts.ts";
import { verdict } from "./language-scan.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const PROBES_DIR = path.join(ROOT, "artifacts/blind-ui-recovery/probes");
const OUT_FILE = path.join(ROOT, "artifacts/blind-ui-recovery/language-scan.json");

const STAGE = process.argv[2] ?? "baseline";

interface ScanRow {
  contractId: string;
  pageId: string;
  verdict: "PASS" | "FAIL";
  uuid: string[];
  snakeCase: string[];
  allcaps: string[];
  invariants: string[];
}

export function runLanguageScan(stage: string): ScanRow[] {
  mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  const rows: ScanRow[] = [];
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
    let raw: { contractId: string; pages: Array<PageProbe & { language?: LanguageMeasurement }> };
    try {
      raw = JSON.parse(readFileSync(path.join(PROBES_DIR, f), "utf8"));
    } catch {
      continue;
    }
    for (const page of raw.pages ?? []) {
      const lang = page.language;
      if (!lang) continue;
      rows.push({
        contractId: raw.contractId ?? f,
        pageId: page.pageId,
        verdict: verdict({
          pageId: page.pageId,
          uuid: lang.uuidHits,
          snakeCase: lang.enumHits,
          invariants: lang.invariantHits,
          allcaps: lang.allcapsHits,
        }),
        uuid: lang.uuidHits,
        snakeCase: lang.enumHits,
        allcaps: lang.allcapsHits,
        invariants: lang.invariantHits,
      });
    }
  }
  writeFileSync(
    OUT_FILE,
    JSON.stringify({ stage, generatedAt: new Date().toISOString(), rows }, null, 2),
  );
  writeFileSync(
    OUT_FILE,
    JSON.stringify({ stage, generatedAt: new Date().toISOString(), rows }, null, 2),
  );
  return rows;
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]).replace(/\\/g, "/") ===
    fileURLToPath(import.meta.url).replace(/\\/g, "/")
) {
  const rows = runLanguageScan(STAGE);
  const fails = rows.filter((r) => r.verdict === "FAIL");
  for (const r of rows) {
    console.log(
      `[language:${STAGE}] ${r.contractId}/${r.pageId}: ${r.verdict}${r.snakeCase.length ? ` enums=${r.snakeCase.join(",")}` : ""}${r.uuid.length ? ` uuid=${r.uuid.join(",")}` : ""}${r.invariants.length ? ` inv=${r.invariants.join(",")}` : ""}`,
    );
  }
  console.log(`[language:${STAGE}] total=${rows.length} FAIL=${fails.length}`);
}
