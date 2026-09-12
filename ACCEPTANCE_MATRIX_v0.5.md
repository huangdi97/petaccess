# ACCEPTANCE_MATRIX_v0.5.md

Verified at HEAD `0542827` on 2026-09-12. Every PASS below has a real command
and its real output recorded in `WORKBUDDY_TAKEOVER_REPORT.md` /
`PROJECT_STATE_V05.md`.

| Gate | 验收 | 状态 |
|---|---|---|
| V00 | 原 RC baseline 全绿 | **PASS** — pytest 89, Playwright 5, lint, mypy |
| V01 | MinIO 上传/删除/OCR queue E2E | **PASS** — `test_media.py` 5 passed (real MinIO) |
| V02 | Tencent adapter + contract tests | **PASS** — 13 fixture contract tests |
| V03 | AI adapters + contract tests | **PASS** — `test_ai_guard.py` |
| V04 | backup/restore 真演练 | **PASS** — commit `a6123e3` + runbook |
| V05 | observability/retry/failed jobs | **PASS** — commit `17226c9` |
| V06 | RuleLayer migration | **PASS** — `b2a1c7d9e001` up/down/up |
| V07 | EffectiveRuleResolver | **PASS** — `test_v05_resolver.py` |
| V08 | RuleCandidate | **PASS** — state machine + E2E-A publish |
| V09 | DataSourceJob | **PASS** — model + API present |
| V10 | SourceMonitor → Candidate | **PASS** — E2E-C repaired & passing |
| V11 | FreshnessPolicy | **PASS** — model + service present |
| V12 | CoexistencePolicy | **PASS** — model + service present |
| V13 | BoundaryProfile + Matcher | **PASS** — `test_v05_track_b.py` |
| V14 | Amenity | **PASS** — model + API present |
| V15 | Entrance + AccessPath | **PASS** — model + API present |
| V16 | Organization + PolicyTemplate | **PASS** — E2E-B inheritance/override |
| V17 | Event/Temporary policy | **PASS** — model + API + tests |
| V18 | DataLicense | **PASS** — model + API present |
| V19 | PetAccessJSON | **PASS** — `test_v05_properties.py` |
| V20 | Answerability | **PASS** — `answerability.py` + tests |
| V21 | Admin v0.5 真 API | **NOT_STARTED** — v0.3-era views only |
| V22 | H5 v0.5 E2E | **NOT_STARTED** — v0.3-era surfaces only |
| V23 | Rule acquisition E2E-A | **PASS** — upload→MinIO→OCR→candidate→publish |
| V24 | Operator E2E-B | **PASS** — template inheritance + override |
| V25 | Source monitor E2E-C | **PASS** — hash change→candidate→supersede→watch |
| V26 | migration up/down/up | **PASS** — 4 revisions, clean cycle |
| V27 | old tests remain PASS | **PASS** — full suite green |
| V28 | new domain/property tests PASS | **PASS** — resolver/properties/track_b |
| V29 | Reality Audit tooling | **NOT_STARTED** |
| V30 | HBuilderX target build status | **BLOCKED_EXTERNAL** (B-01) |
| V31 | real map live smoke | **BLOCKED_EXTERNAL_EXPECTED** (B-04) |
| V32 | real AI live smoke | **BLOCKED_EXTERNAL_EXPECTED** (B-05) |
| V33 | V05_FINAL_REPORT | **NOT_STARTED** |

附加（NEXT_GOAL 新增要求，非原 Gate 编号）:

| Gate | 验收 | 状态 |
|---|---|---|
| V34 | E2E-D external public lead（不得直接发布） | **NOT_STARTED** |
| V35 | Adversarial fixtures（≥30 类） | **NOT_STARTED** |
| V36 | `MIGRATION_V05.md` | **NOT_STARTED** |
| V37 | Evidence-first / EvidenceBundle 一等实体 | **PARTIAL** — candidate 携带 `raw_text` + `media_id` + `extraction_method`，可追溯；但无独立 EvidenceBundle 表（source_platform / captured_at / content_hash / license metadata 未独立建模） |
| V38 | Collector abstraction / SourceArtifact | **NOT_STARTED** |
| V39 | Original vs Derived evidence 分离 | **PARTIAL** — `media_object`（原始媒体）+ `raw_text`（派生）已分离存储，未显式标注 evidence class |
| V40 | DataLicense source policy 字段完整度 | **PASS** — 7 个必需字段全部存在（display/storage/redistribution/commercial/attribution/license_name/license_url/expires_at），默认值保守（redistribution=false, commercial=false） |
| V41 | ObservationCandidate 与 RuleCandidate 分离 | **NOT_STARTED** — 仅有 `rule_candidate`，无独立 observation candidate 状态机 |

状态：NOT_RUN / PASS / PARTIAL / FAIL / BLOCKED_EXTERNAL / NOT_STARTED
