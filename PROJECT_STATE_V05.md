# PROJECT_STATE_V05.md

## Historical expected baseline
95c357e

## Actual HEAD
See `git log` — V33 final commit (post `2d7e7cb`, V29 reality audit).

## Current phase
V0.5 LOCAL RC COMPLETE — all locally-executable gates PASS; final report issued.

## Existing evidence
- `V05_FINAL_REPORT.md` (authoritative summary, real commands + outputs)
- `WORKBUDDY_TAKEOVER_REPORT.md` (takeover repairs)
- `ZCODE_RESUME_TAKEOVER_REPORT.md` (post-WorkBuddy takeover audit)

## Final verification (2026-09-13, actual runs)

| Check | Command | Result |
|---|---|---|
| Backend tests | `uv run pytest -q` | **184 passed** |
| Playwright | `./node_modules/.bin/playwright test --output=playwright-out` | **7 passed** |
| Lint + format | `bash scripts/lint.sh` | All checks passed / 103 files |
| Types | `uv run mypy services/api/app` | Success, 72 files |
| Admin build | `pnpm --filter @petaccess/admin build` | ✓ built |
| H5 build | `VITE_API_BASE=…:8010/api/v1 pnpm --filter @petaccess/client-h5 build` | ✓ built |
| Migrations | `alembic downgrade base` / `upgrade head` ×2 + rev7 single cycle | 7 revisions, clean |
| PostGIS / Postgres / Redis / Celery / MinIO | real queries | 3.5 / 17.5 / PONG / 1 node / media chain PASS |
| Demo seed | `python -m app.db.seed --demo` | 4 places / 15 zones / 8 sources |
| Reality audit run | `python -m app.tools.reality_audit docs/reality_audit/synthetic_samples.json` | 6 samples, 5 expressible, 3 gap candidates |

## Gates closed this session (ZCode, post-WorkBuddy)

1. **V36** `MIGRATION_V05.md` + double down/up cycle (`ac7c541`)
2. **V34** E2E-D lead chain — publish gate wired to licence at the API boundary,
   `rule_candidate.evidence_bundle_id` migration (`c81e02ba6d45`) (`35a3e3a`)
3. **V35** 40 adversarial fixture classes, auditable registry (`4d4dcab`)
4. **V29** Reality Audit engine (CLI + admin API), CSV/JSON templates, report
   trio over synthetic samples (`2d7e7cb`)
5. **V33** `V05_FINAL_REPORT.md` + state docs

## Gate status (see ACCEPTANCE_MATRIX_v0.5.md for evidence lines)

- V00–V28, V37–V44: PASS (prior sessions; baseline re-verified)
- V29, V33, V34, V35, V36: PASS (this session)
- V30/V31/V32: BLOCKED_EXTERNAL (B-01 / B-04 / B-05) — live smoke only

## Product-rule invariants under test

Observation≠Rule (structural + API byte-identical test) · UNKNOWN never coerced ·
service-dog scope isolation · place UUID ≠ external ID · lead-only licence gate ·
no scores/rankings/reviews · demo fully fictional · provenance manifest pins
`real_place_claims: 0` until lawful real material exists.

## Next action (outside local scope)

Real 30–50 place sample collection under lawful provenance → run
`python -m app.tools.reality_audit` → extend schema per SCHEMA_GAPS findings.
External keys (B-04/B-05) when available → live smokes only.

## Truth rule
No v0.5 PASS without actual validation.
