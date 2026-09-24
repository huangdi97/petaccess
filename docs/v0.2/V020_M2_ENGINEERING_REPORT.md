# V020 M2 Engineering Report

Status: M2 Product Experience Foundation — engineering closure (M2-G)
Last updated: 2026-09-24
All statuses below are **measured this round** (the 938/2 baseline was never copied; the full suite was re-run after every M2 code change).

## 1. Machine gates — final result

| Gate | Command | Result |
|---|---|---|
| Engineering quality | `scripts/check_engineering_quality.py` | **PASS** — 0 FAIL / 60 REVIEW / 28 WARN |
| Secret scan | `scripts/scan_secrets.py` | PASS (no secrets in worktree/history) |
| Ruff lint | `ruff check services/api services/worker tests scripts` | PASS — All checks passed |
| Ruff format | `ruff format --check` (repo-wide incl. docs) | PASS — 467 files formatted |
| mypy | `mypy services/api/app` | PASS — 0 errors, 96 files |
| Backend pytest | `pytest -q` (TEST DB + Celery + MinIO) | **944 passed / 2 skipped / 0 failed** (DISCOVERED 946) |
| ESLint | `pnpm lint:fe` | PASS |
| Prettier | `pnpm format:check:fe` | PASS |
| client-h5 build | `vue-tsc --noEmit && vite build` | PASS (1.65 s) |
| admin build | `vue-tsc && vite build` | PASS (1.49 s) |
| Playwright visual (consumer) | `playwright.visual.config.ts` consumer.spec.ts | **42 passed** (6 families × 390/768/1440) |
| Playwright e2e | `playwright.config.ts` tests/e2e | **70 passed** |
| a11y machine scan | axe-core 4.10 over 6 families | **0 critical / 0 serious** |

## 2. Backend regression (full re-run, §52)

```
DISCOVERED = 946   PASSED = 944   SKIPPED = 2   FAILED = 0   (44s)
```

Preflight (§53) run in one orchestrated command: `isolated_db.py --role TEST
--reset` → Celery worker (`--pool=solo -Q petaccess_test`) → pytest. MinIO was
already healthy on :9000. The three media/v05 tests that rely on a live worker
consume tasks and pass; they fail with `TimeoutError` only when no worker is
running (verified: worker must live for the whole suite session).

## 3. Frontend gates

- ESLint and Prettier pass after closure cleanup (see §6).
- Two real defects were found and fixed here (not papered over): 5 Vue files
  contained corrupted em-dash bytes (invalid UTF-8) that broke the design-token
  source guards' decoding; the guards themselves stand unchanged.

## 4. Visual regression + a11y

- 42 consumer baselines (home-fixture / home-empty / search-fixture /
  search-empty / offline / error / map / map-sheet / place-unknown /
  place-conditional / rule-trace / contribute / mine / boundary) regenerated
  and green in compare mode at 390 / 768 / 1440, light theme.
- axe-core 4.10 pass (one-off audit, §45): first run 4 critical + 6 serious →
  **0 critical / 0 serious** after:
  - `.home-entries`: removed `role="list"` (buttons cannot be listitems).
  - `--pa-color-text-muted`: `#69747f` → `#5c6772` (4.36:1 → ≥5.0:1 on all
    surfaces used by `.muted`/`.notice`), closing the goal §5 灰色字过浅 item.
  Full detail in `V020_M2_SCREENSHOT_REVIEW.md` §6.

## 5. Performance baseline (§50) — recorded, not optimised

| Asset | Raw | gzip |
|---|---|---|
| Main entry `index-*.js` (shared) | 134.39 kB | 51.94 kB |
| HomeView route chunk | 10.19 kB | 4.44 kB |
| SearchView route chunk | 9.99 kB | 4.38 kB |
| MapView chunk | 9.04 kB | 4.25 kB |
| PlaceView chunk | 22.91 kB | 8.41 kB |
| ContributeView chunk | 21.57 kB | 7.32 kB |
| Base CSS `index-*.css` | 22.12 kB | 4.24 kB |
| Home initial route ≈ index + HomeView | 144.6 kB JS | 56.4 kB JS gzip |

Windows cold start / Android cold start numbers belong to M8/M9 real-artifact
QA; this round records the H5 bundle baseline only (no obvious regression
flagged — largest chunk is PlaceView at 22.9 kB).

## 6. Issues found and fixed during M2-G closure

| # | Issue | Fix | Type |
|---|---|---|---|
| 1 | Engineering gate FAIL: `type-escape dev_fixture.py:18` — word "Any" in a docstring prose line (scanner's Python branch does not skip comments) | Reworded the docstring ("If any of those conditions fails…"); **no scanner change, no exemption** | gate |
| 2 | `ruff format` — 6 files (3 docs *.md code blocks, `core/config.py`, `test_reality_report_api.py`, `test_production_fail_closed.py`) | `ruff format` on exactly those files | format |
| 3 | 5 Vue components had corrupted UTF-8 (`\xe2\x80?` broken em-dash): ToastHost, PaEmptyState, PaMetadataRow, PaPageHeader, PaSectionHeader | Byte-level repair to `\xe2\x80\x94`; all sources re-scanned valid | encoding |
| 4 | mypy 5 errors: `int(dict[str,object])` in dev_fixture; `fixture_place_out` dict vs `Place`; `Sequence` vs `list` in reality_reports `_source_type_label` | `int(str(...))`; `fixture_place_out` now returns a typed `PlaceOut` and `get_place -> Place | PlaceOut`; params widened to `Sequence[...]` | typing |
| 5 | `test_ui_states`: per-view `offline-banner` needles outdated after M2 moved offline to the shell (§29) | Updated to assert `ConsumerAppShell` wires `GlobalOfflineBanner`; per-view list drops offline (architecture-honest, not a weakening) | test |
| 6 | ESLint failed on transient `.tmp/*.mjs` scratch files | Deleted leftovers; added `.tmp/**` to eslint ignores (local scratch is never app source) | tooling |
| 7 | Prettier flagged 29 files (M2-A..F landed before prettier enforcement; no remote → CI never ran) | `prettier --write` on the exact set; `format:check:fe` green | format |
| 8 | a11y: 4 critical + 6 serious | See §4 — 0/0 after fixes | a11y |
| 9 | e2e home test flake on one run | Stale local preview from an earlier one-off audit was being reused (`reuseExistingServer`); killed, re-ran: 70 passed | env |

## 7. Platform QA status (§46 / §47) — honest

| Check | Status | Evidence |
|---|---|---|
| H5 responsive (390 … 1920 px) | **PASS** | responsive e2e (9 viewports × pages, no horizontal overflow) + visual 390/768/1440 |
| Desktop layout rail + content container | **PASS** | visual 1440, DOM audit (no centered-390px look) |
| Windows Tauri binary QA (1280×720 / 1440×900 / 1920×1080, DPI 100/125/150 %) | **PARTIAL** — deferred to M8 | v0.1.0 Windows smoke exists; M2 is H5-viewport verified |
| Android device QA (360/390/430, status/nav bar, keyboard, sheet) | **PARTIAL** — deferred to M9 | v0.1.0 emulator smoke exists; M2 covers 390 logical width |

Recorded as PARTIAL per project rule (never infer PASS).

## 8. Tech debt / exemptions (§54 / §55)

- TD-028 / TD-029: registered in `docs/audit/V010_TECH_DEBT_REGISTER.md`,
  status DONE (M1) — unchanged this round.
- Dead-code exemption registry: 130 symbol exemptions maintained; gate 0 FAIL.
- No new scanner code was added this round (issue #1 fixed by rewording, not
  by extending scanners — §55).

## 9. §56 deliverables — all eight present in `docs/v0.2/`

V020_DESIGN_SYSTEM_SPEC · V020_APP_SHELL_SPEC · V020_HOME_UX_REPORT ·
V020_SEARCH_UX_REPORT · V020_EMPTY_ERROR_OFFLINE_SPEC ·
V020_REALITY_CONTRIBUTION_GAP_AUDIT · V020_M2_SCREENSHOT_REVIEW ·
V020_M2_ENGINEERING_REPORT (this file).

**Overall: V020_M2 = PASS** (all §58 acceptance items green on this machine).