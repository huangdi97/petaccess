# UI Oracle — PetAccess Blind-Model UI Verification Tooling

A small, dependency-free Oracle that turns the machine-readable UI contracts
(`docs/ui/contracts/json/*.json`) into measured evidence. It exists so the
"no-vision agent" can complete and verify UI without reading screenshots.

## Files

| File | Responsibility |
|---|---|
| `contracts.ts` | Contract JSON schema + TypeScript types (shared) |
| `probe.ts` | In-page measurement (bbox / computed style / text / density) |
| `compare.ts` | Probe + contract → PASS / WARN / FAIL rows |
| `language-scan.ts` | Visible-text scan (UUID / snake_case / ALL_CAPS / invariants) |
| `density.ts` | Density thresholds & verdicts (Dense but Quiet) |
| `report.ts` | Stage report aggregation → `artifacts/blind-ui-recovery/reports/` |

Contracts live in `docs/ui/contracts/` (Markdown for humans,
`json/` for machines).

## How it runs

1. **Probe** — `tests/ui-oracle/oracle.spec.ts` (Playwright) starts the same
   deterministic stack as the visual suite (`petaccess_visual` seed + API on
   8011 + H5 preview on 5175), visits every contract page at the contract
   viewport, runs `probe.ts` functions in-page, screenshots each state, and
   writes `artifacts/blind-ui-recovery/probes/{stage}-{contract}.json`.
   Screenshots are evidence artifacts — never interpreted by the agent.
2. **Compare** — node-side: `node --experimental-strip-types tools/ui-oracle/compare.ts <stage>`
   reads probes + contracts, produces `reports/compare-*.json` + stage totals.
3. **Language scan** — included in every probe (visible text), also exposed as
   `language-scan.ts` for a standalone run.
4. **Report** — `node --experimental-strip-types tools/ui-oracle/report.ts <stage>`
   aggregates into `reports/{stage}.json` and `final.json`.

## Commands

```bash
# Probe + screenshots at a stage (baseline | phase-a | phase-b | ... | final)
$env:UI_ORACLE_STAGE="baseline"; pnpm exec playwright test -c playwright.ui-oracle.config.ts

# Compare probes against contracts
node --experimental-strip-types tools/ui-oracle/compare.ts baseline

# Aggregate stage report
node --experimental-strip-types tools/ui-oracle/report.ts baseline
```

Viewports follow each contract (`1440x900` desktop, `430x932` mobile), so
`.search.mobile.json` runs on the mobile layout and produces mobile screenshots.

## Honesty rules (Goal §4, §40)

- Screenshots are for humans. The agent verifies only: file exists, PNG magic,
  dimensions, non-zero bytes, distinct hashes.
- The agent never claims "the screenshot looks right" — it reports the machine
  contract verdicts and leaves visual acceptance to the human.
- Every FAIL / WARN row must trace to a contract target + measured actual.