# PROJECT_STATE_V05.md

## Historical expected baseline
95c357e

## Actual HEAD
054282729c1ba08a55811a26f3bc016ac2812ff2

## Current phase
BASELINE_GREEN — local repairs applied at takeover; proceeding to Track B/C closeout.

## Existing evidence
See FINAL_RELEASE_REPORT.md (v0.3 RC) and WORKBUDDY_TAKEOVER_REPORT.md (takeover).

## Baseline re-run at takeover (2026-09-12)

| Check | Command | Result |
|---|---|---|
| Backend tests | `uv run pytest -q` | 89 passed |
| Playwright | `./node_modules/.bin/playwright test` | 5 passed |
| Lint + format | `bash scripts/lint.sh` | All checks passed! / 90 files |
| Types | `uv run mypy services/api/app` | Success, 68 files |
| Admin build | `pnpm --filter @petaccess/admin build` | ✓ built |
| H5 build | `VITE_API_BASE=…:8010/api/v1 pnpm --filter @petaccess/client-h5 build` | ✓ built |
| Migration up/down/up | `alembic downgrade base` + `upgrade head` | 4 revisions, clean |
| PostGIS | `SELECT PostGIS_Version()` | 3.5 USE_GEOS=1 USE_PROJ=1 |
| Postgres | `SHOW server_version` | 17.5 |
| Redis | `docker exec … redis-cli ping` | PONG |
| Celery | `celery inspect ping` | 1 node online |
| MinIO chain | `pytest tests/integration/test_media.py` | 5 passed |
| Demo seed | `python -m app.db.seed --demo` | 4 places / 15 zones / 8 sources |

## v0.5 status
- Track A (RC-HARDENING-01): PASS (A1–A5 commits present; media chain re-verified).
- Track B (V05-DOMAIN-01): domain + API + backfill migration PASS.
  Remaining: `MIGRATION_V05.md`, Admin v0.5 pages, H5 v0.5 surfaces.
- Track C (PILOT-READINESS-01): E2E-A/B/C repaired and PASS.
  Remaining: Reality Audit tooling, adversarial fixtures.

## Local repairs made at takeover
1. `tests/integration/test_v05_e2e.py` — 3 root causes fixed (Windows
   `getaddrinfo` artifact; watch user/uniqueness + shared-DB race; assertion
   matched a UUID the product never emits). 13 lint findings cleared.
2. `tests/integration/test_v05_e2e.py` missing `select` import.
3. `services/api/app/db/seed.py` — **real defect**: v0.5 tables were absent from
   the reset list, so `--demo` crashed with
   `ForeignKeyViolation … fk_rule_candidate_source_id_source`.
4. Environment: started API on 8010, rebuilt H5 with an explicit `VITE_API_BASE`,
   re-seeded the polluted dev DB.

ZCode's two uncommitted files were reviewed and **kept unchanged** —
`db.flush()` before `record_audit` (audit target id) and `trust_env=False`
(proxy-inheriting httpx client). Both are correct.

## Next action
Track B/C closeout: `MIGRATION_V05.md`, Admin v0.5 pages, H5 v0.5 surfaces,
Reality Audit tooling, adversarial fixtures, then `V05_FINAL_REPORT.md`.

## Truth rule
No v0.5 PASS without actual validation.
