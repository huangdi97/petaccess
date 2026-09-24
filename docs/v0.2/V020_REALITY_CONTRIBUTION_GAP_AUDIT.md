# V020 Reality/Contribution Backend Gap Audit

Status: M2 Product Experience Foundation — backend gap audit
Last updated: 2026-09-24
Method: read-only audit of `services/api/app` + `packages/client-core` + consumer UI wiring. **Nothing was rebuilt that already exists** (M2 §38). No new enum/model was created.

Per-item verdicts use exactly one of:
**IMPLEMENTED** · **PARTIAL** · **MISSING** · **NOT_WIRED** · **NOT_TESTED**

Each item records the five layers: schema / service / API / client / UI / tests (six columns where the client layer exists).

---

## 0. Summary table

| Item | Schema | Service | API | Client | UI | Tests |
|---|---|---|---|---|---|---|
| RealityReport | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | PARTIAL | IMPLEMENTED |
| ObservationOrigin / Effort | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| ExternalContentReference | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| PlaceMatchState / Evidence | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| TimeEvidenceState | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| FactEvidenceState | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| StaffAwarenessState | PARTIAL | MISSING | MISSING | MISSING | NOT_WIRED | NOT_TESTED |
| FacilityPurposeState | PARTIAL | MISSING | MISSING | MISSING | NOT_WIRED | NOT_TESTED |
| RealityConfirmation | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| RealityCandidate family | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| Reality Review | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_WIRED | IMPLEMENTED |
| Reality Freshness | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | PARTIAL | IMPLEMENTED |

---

## 1. RealityReport

- **Schema**: `services/api/app/models/reality.py` `RealityReport` (:281); Pydantic `RealityReportIn` / `RealityReportOut` in `app/schemas/reality.py` (:203 / :234); parent-flow DTOs `RealityContributionIn` / `RealityContributionOut` in `app/schemas/reality_reports.py` (:56 / :81). Migration `d4e7b2a8c9f1_reality_report_parent_and_state_models.py`.
- **Service**: `app/services/reality_contribution.py::create_report` (:166) — one report, zero-or-more candidates, dedup window 24h (`DEDUP_WINDOW_HOURS`), anti-abuse flags, always `REVIEW_PENDING` (proximity never verifies).
- **API**: `POST /api/v1/places/{id}/reality/reports` (`app/api/v1/reality_reports.py::create_report` :145), `GET /api/v1/places/{id}/reality/reports` (:249).
- **Client**: `packages/client-core/src/api/client.ts` `createRealityReport` (parent-flow) — **fixed this round**: it previously sat outside the `client` object literal and broke `vue-tsc`; moved inside, no behavior change.
- **UI**: ContributeView still posts legacy `submitRealityContribution` (single-candidate); the parent-flow report form is **not wired to any UI yet** → `PARTIAL` (UI layer), backend layers `IMPLEMENTED`.
- **Tests**: `tests/integration/test_reality_report_api.py` (10: parent flow, on-site-past time rule, effort≠claim, confirmation append-only, idempotency, trace).

## 2. ObservationOrigin / ObservationEffort

- **Schema**: `ObservationOrigin` StrEnum (`app/models/enums.py:673`), `ObservationEffortDurationBucket` (:753); model `ObservationEffort` (`models/reality.py:362`); DTOs `ObservationEffortIn` (`schemas/reality.py:264`).
- **Service**: `create_observation_effort` (`services/reality_contribution.py:292`).
- **API**: part of the report payload (`effort` field on `POST .../reality/reports`).
- **Client**: `createRealityReport` accepts `effort` in the body type.
- **UI**: no UI writes effort → `NOT_WIRED`.
- **Tests**: covered inside `test_reality_report_api.py` (effort≠claim assertion).

## 3. ExternalContentReference

- **Schema**: `ExternalContentReference` model (`models/reality.py:422`); `ExternalContentReferenceIn` (`schemas/reality.py:297`); `ExternalContentPlatform` StrEnum (`enums.py:823`).
- **Service**: `create_external_content_ref` (`services/reality_contribution.py:371`) + old-video gate `OLD_VIDEO_MAX_AGE_DAYS=365` (:61).
- **API**: `external_content` field on the report endpoint.
- **Client**: typed in `createRealityReport`.
- **UI**: `NOT_WIRED` (no UI for external content ingestion; source URLs only via legacy paths).
- **Tests**: `test_reality_report_api.py` external-content cases.

## 4. PlaceMatchState / PlaceMatchEvidence

- **Schema**: `PlaceMatchState` (`enums.py:687`), `PlaceMatchEvidenceType` (:702); consumed on `RealityReport` (place_match_state, place_match_evidence_types).
- **Service**: `check_place_match_consistency` (`services/reality_contribution.py:125`).
- **API**: report payload fields.
- **Client**: typed in `createRealityReport` body.
- **UI**: `NOT_WIRED`.
- **Tests**: in `test_reality_report_api.py`.

## 5. TimeEvidenceState

- **Schema**: `TimeEvidenceState` (`enums.py:715`), `TimeCertainty` (:732).
- **Service**: `_validate_report_times` (`api/v1/reality_reports.py:97`) — on-site-past vs external content time rules.
- **API**: report payload fields (`content_published_at`, `claimed_event_at`, `observed_at`, `time_certainty`).
- **Client**: typed.
- **UI**: `NOT_WIRED`.
- **Tests**: `test_reality_report_api.py` includes the on-site-past rule.

## 6. FactEvidenceState

- **Schema**: `FactEvidenceState` (`enums.py:740`).
- **Service**: stored on report (`fact_evidence_state`).
- **API**: report payload field.
- **Client**: typed.
- **UI**: `NOT_WIRED`.
- **Tests**: in `test_reality_report_api.py`.

## 7. StaffAwarenessState

- **Schema**: enum exists (`enums.py:763`) — **enum-only, no column/schema/endpoint** (recorded as TD-029 in `docs/audit/V020_GLOBAL_CODE_AUDIT.md`; a test stores the value inside `payload`).
- **Service/API/Client/UI**: `MISSING`.
- **Tests**: `NOT_TESTED` (only a payload round-trip in a candidate test).
- **Verdict**: **PARTIAL** (schema) / **MISSING** (service/API/client/UI) / **NOT_TESTED**. Not rebuilt this round (M2 §39: no new moderation/crawler/ingest capability).

## 8. FacilityPurposeState

- **Schema**: enum exists (`enums.py:776`) — enum-only, same TD-029 status as StaffAwarenessState.
- **Service/API/Client/UI**: `MISSING`.
- **Tests**: `NOT_TESTED`.
- **Verdict**: **PARTIAL / MISSING / NOT_TESTED** — same treatment as §7.

## 9. RealityConfirmation

- **Schema**: `RealityConfirmation` model (`models/reality.py:392`); `RealityConfirmationType` (`enums.py:790`); DTO `RealityConfirmationIn` (`schemas/reality.py:275`).
- **Service**: `create_confirmation` (`services/reality_contribution.py:332`), append-only.
- **API**: `confirmation` field on report endpoint.
- **Client**: typed in `createRealityReport`.
- **UI**: `NOT_WIRED`.
- **Tests**: append-only assertion in `test_reality_report_api.py`.
- **Known duplicate** (audit-named, not recreated): `RealityConfirmationOut` exists twice — `schemas/reality.py:285` and `schemas/reality_reports.py:97`. One should be deleted in a future cleanup; nothing was rebuilt.

## 10. RealityCandidate family

- **Schema**: `RealityCandidate` (`models/reality.py:70`) + subclasses `ObservedPresence` (:127), `StaffResponseObservation` (:166), `AnimalFacility` (:221); `RealityCandidateType` (`enums.py:519`); `RealityCandidateIn/Out` (`schemas/reality.py:42/:61`); parent-flow drafts `RealityCandidateDraft` / `RealityCandidateBrief` (`schemas/reality_reports.py:40/:66`).
- **Service**: `attach_candidate` (`services/reality_contribution.py:238`).
- **API**: admin router (`api/v1/reality.py`): `GET /api/v1/reality/candidates` (:262), `POST ...` (:283), `POST /reality/candidates/{id}/decision` (:329); consumer `POST /places/{id}/reality/contributions` (:191); legacy claim projection `_publish_claim` (:379) mirrors VERIFIED candidates into the three claim tables.
- **Client**: `submitRealityContribution` + `createRealityReport` candidates.
- **UI**: legacy ContributeView uses `submitRealityContribution`; parent-flow UI `NOT_WIRED`.
- **Tests**: `tests/integration/test_reality_report_api.py` + v0.9 claim tests.
- **Finding (fixed-this-round scope)**: the **admin UI calls wrong paths** — `apps/admin/src/views/RealityDashboardView.vue:56` and `RealityCandidateQueueView.vue:63/:81` call `/admin/reality/candidates.../decision`, but the backend reality admin router has **no `/admin` prefix** (real routes are `/api/v1/reality/candidates...`). Every admin reality screen 404s today. OpenAPI confirms no `/api/v1/admin/reality/candidates` entry. This is a **contract gap**; per M2 §39 the fix belongs to the admin client or a path alias — recorded here, not silently rewritten in this round.

## 11. Reality Review

- **Schema**: `RealityVerificationStatus` (`enums.py:653`) — `REVIEW_PENDING`/`REVIEWED` (uppercase) + `RealityDecision` (:527, lowercase values) + `REALITY_VERIFIED_DECISIONS` frozenset (:537).
- **Service**: candidates land `REVIEW_PENDING`; only `POST /reality/candidates/{id}/decision` (moderator) moves them; AI never sets `reality_decision`.
- **API**: decision endpoint + trace endpoint `GET /places/{id}/reality/trace` (`api/v1/reality_reports.py:275`).
- **Client**: `realityTrace` typed (client.ts) — no UI caller → `NOT_WIRED`.
- **Tests**: `test_reality_report_api.py` trace case.
- **Known inconsistency** (audit-named): `review_status` (uppercase) vs `reality_decision` (lowercase enum values) — bridged in the API layer; not rebuilt.

## 12. Reality Freshness

- **Schema**: `RealityFreshnessState` (`enums.py:542`, lowercase values) vs the summary engine's **uppercase** bucket strings (FRESH/RECENT/AGING/HISTORICAL/EXPIRED_FOR_SUMMARY) bridged by `_freshness_state` (`api/v1/reality.py:66-70`). Two spellings of one vocabulary — **the duplicate the audit must not widen**.
- **Service**: `app/services/reality_summary.py` — thresholds `FRESH_DAYS=7 / RECENT_DAYS=30 / AGING_DAYS=90 / HISTORICAL_DAYS=365` (:34-37), `freshness_for()` (:58), `summarize()` (:121); frozen `RealitySummary` dataclass (:82).
- **API**: `GET /places/{id}/reality` returns `freshness_state` (`api/v1/reality.py:78`).
- **Client**: `placeReality` + `CoexistenceSnapshot.reality_answer.freshness_state`.
- **UI**: `PARTIAL` — RealityPanel renders freshness for place detail; Search/Home rows show rule freshness (`last_verified_at`) but not reality freshness yet.
- **Tests**: `services/api/tests/test_reality_summary.py` (13: boundary days, future dates, invariants).
- **Note**: no background/scheduled recompute of reality freshness exists (worker has zero reality references); freshness is computed on read via `freshness_for()`. M2 scope: recorded, not built.

---

## 13. Findings & disposition (M2 §38/§39)

1. **No duplicate creation**: this round added zero new enums, zero new models, zero new schemas for reality/contribution. All existing implementation was reused. ✔
2. **Known duplicates — audit-named, NOT recreated**:
   - `RealityConfirmationOut` (schemas/reality.py:285 vs reality_reports.py:97)
   - `RuleEffect(StrEnum)` (models/enums.py:206 vs services/rule_reality_divergence.py:42)
   - `REALITY_STATE_LABELS` (api/v1/reality_reports.py:81 vs apps/client-h5/src/reality.ts:18) — UI-side copy dictionary centralised in `@petaccess/design-tokens` copy.ts (M2); the API label map is an admin-side convenience.
   - lowercase `RealityFreshnessState` vs uppercase summary bucket strings.
   - legacy observation lane (`POST /observations`) coexists with the v0.9 reality lane — both intentionally supported; not merged.
   - `SourcePlatform` string-class (models/evidence.py:47) vs `ExternalContentPlatform` StrEnum (enums.py:823).
3. **Admin reality 404 gap**: admin views hit `/admin/reality/...` paths that the backend does not expose (no `/admin` prefix on the reality admin router). Recorded as the single most impactful consumer-visible gap of this audit; **deferred to a client-contract fix**, not rewritten here (M2 §39 scope).
4. **Enum-only states** StaffAwarenessState / FacilityPurposeState stay enum-only (TD-029); not wired this round.
5. **UI wiring**: parent-flow report / effort / confirmation / external content / trace / decision queue are backend-complete but UI-unwired → all marked `NOT_WIRED`. Contribution UX is M7 scope.

## 14. Backend changes actually made this round

- `app/core/config.py`: added `dev_fixture_mode: bool` setting (DEV_FIXTURE_MODE).
- `app/services/dev_fixture.py` (new): demo-only fixture dataset + fail-closed gate.
- `app/api/v1/places.py`: `list_places` / `nearby_places` / `get_place` serve clearly-labelled `·演示` fixture rows when `dev_fixture_active()` — never on production (enforced by DB role + APP_ENV gate).
- `tests/isolation/test_production_fail_closed.py`: new `TestDevFixtureModeIsFailClosedForProduction` (6 tests, all PASS) proving production/staging/prod-DB refuse fixtures even with the flag set.
- `packages/client-core/src/api/client.ts`: moved `createRealityReport` / `realityTrace` back inside the `client` object literal (was breaking vue-tsc).

No reality/contribution enum, model, schema, or resolver was duplicated or rewritten.
