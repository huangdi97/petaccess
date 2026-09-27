# Consumer Contract Corrective Closure (M3.1)

> Date: 2026-09-28 · Branch: `feat/ui-reconstruction-spatial-dossier` · Parent: `434efd3` (origin/master)
> Contract: `PetAccess v0.2 — UI Reconstruction GOAL` §8 (G1), executed before any large-scale UI work.

## G0 — Git / Runtime Reality (executed first)

| Item | Value |
|---|---|
| CURRENT_HEAD | `434efd3` (verified by `git rev-parse HEAD`) |
| REMOTE_MASTER | `434efd3` (after `git fetch origin`) |
| MERGE_BASE | `434efd3` (HEAD == origin/master, zero divergence) |
| TRACKED_WORKTREE | CLEAN at start (no tracked modifications) |
| UNTRACKED_FILES | `docs/ui/reference/` (Approved Reference PNG) + v0.10-R1 canonical master |
| LOCAL_ONLY_COMMITS | none |
| REMOTE_ONLY_COMMITS | none |
| DIVERGENCE | none — no force push / rebase / tag movement; `v0.1.0` tag untouched |

Canonical master and Approved Reference were committed into the reconstruction branch as the round's source documents.

## Gate results

| Gate | Status | Evidence |
|---|---|---|
| COEXISTENCE_SNAPSHOT_SSOT | **PASS** | Code: `consumer/repository.ts` is the only consumer data module; `rowFacts` / `snapshotFor` / Map marker statuses / Place dossier Reality panel all read the same cached `CoexistenceSnapshot`. Home/Search/Map no longer call `accessAnswer`+`placeReality` per row; Map's own `deriveStatuses` worker pool was replaced by `enrichRows`. No second Rule/Reality resolver remains in the frontend. |
| TRANSPORT_ERROR_CACHE | **PASS** | Code: `rowFacts` no longer uses `catch(() => null)` inside `coalesce`; failure throws through `snapshotFor`, nothing is written to the store. Regression test `C2` (first request 500 → recovery → same query re-requests and shows the real ALLOWED badge) passes. |
| SNAPSHOT_CACHE_KEY | **PASS** | Code: `snapshotKey` includes placeId, animal/species, service_role, declared_role, action, zone_id. `currentQueryContext` maps `session.mode === "service_dog"` → `service_role: "working"` (mirrors PlaceView, ADR-025). Regression tests `C3` (key differs ordinary vs service dog / other place / other action; mode→working mapping) pass. |
| OFFLINE_STALE_WIRING | **PASS** | Code: repository returns `{ stale, fetchedAtMs }`; `snapshotFor`/`searchPlaces`/`nearbyPlaces` serve stale entries immediately and background-refresh when online; offline+cached returns the entry with an explicit age; offline+no-cache propagates the error to the caller's Offline state. Home and Search render `freshnessLineFor(...)` when stale/offline. Client-cache freshness is never labelled as Rule/Reality domain freshness. |
| LENS_SEMANTICS | **PASS** | Code: `rowView.ts` `lensProjection` (headline rule-first vs reality-first; indoor/dining surface server `observed_zones`) + `lensOrderScore` (presentation-only sort). SearchView reads `?lens=` and reorders/headlines rows; domain facts and requests are unchanged. Regression test `C5` (rules→rule headline, presence→reality headline, indoor→zone facts) passes. |

## Additional defect found and fixed

`SearchView` fed a **StatusKey** (`ALLOWED` / `CONDITIONAL` …) into `StatusBadge`'s `status` prop, which expects resolver statuses (`MATCH` / `CONDITIONAL` / …). `semanticForAnswerStatus("ALLOWED")` falls back to UNKNOWN, so **every** search row badge rendered "尚未核验" even for an explicitly allowed answer. Fixed to pass `:semantic=`. (Pre-existing bug, not introduced by this round.)

## Test runs (measured)

- Frontend typecheck `vue-tsc --noEmit`: PASS
- `vite build` (client-h5): PASS
- ESLint (changed files): PASS · Prettier: PASS (formatted)
- Playwright contract suite `consumer-contract-closure` + `m3-consumer-core`: **9/9 PASS**
- Full Playwright e2e (`playwright.config.ts`): **161 passed**, 1 fail = `contribute-wizard` A1/A4 — re-run in isolation **passes**, matches the documented **TEST-001 parallel flake** (frozen baseline, unrelated to this round).
- Backend pytest (TEST DB, `petaccess_test`): **883 passed / 2 skipped**; 3 pre-existing failures in `tests/isolation/test_production_fail_closed.py` reproduce identically on the clean stash (Windows GBK codec, environment), not caused by this round. Media/OCR tests required the Celery worker on `petaccess_test` queue; with worker running all 3 pass.

## Remaining gaps

None for the G1 gate. Entering Design System reconstruction (per contract §51 order: primitives → Search → Place → Phase 1 visual gate → Home → Map → …).
