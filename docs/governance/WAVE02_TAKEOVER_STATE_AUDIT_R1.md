# TAKEOVER STATE AUDIT — Wave01 复验 + Wave02 启动

轮次：`PET_ACCESS_PLATFORM_CONTINUATION_R1 · TAKEOVER`
接手人：PI-Desktop（Agent）· 决定人 / Human Reviewer：`huangdi97`
审计时点：2026-09-19 / 2026-09-20（与生产库实时比对，非复述旧报告）

## 0. 结论指标

```
CURRENT_HEAD                        = aee7bb8（AccessAnswer 消费端迁移已提交）
CURRENT_HEAD_BEFORE_WORKTREE_COMMIT = 6400fc1（接手时 HEAD）
WORKTREE_CLEAN                      = 否（见 §2：含 Wave02 未提交产物）
CURRENT_DB_AVAILABLE                = YES（petaccess / PRODUCTION，alembic f2a1c7d9e034）
CENTURY_PARK_BATCH_FOUND            = YES（EXP_R1_W01_REVIEW_R1_BATCH_03_CENTURY_PARK.json）
CENTURY_PARK_REAL_PUBLISH_EXECUTED  = YES（rule 149828d0-b995-4a99-986e-fd740cea4466）
WAVE01_APPROVED_DISPOSITION         = ALREADY_PUBLISHED 12 / SUPERSEDED 3 /
                                      CURRENTLY_EXECUTABLE 0 / PUBLISH_BLOCKED 0
SUPERSEDED_GUARD_ACTIVE             = YES（3 个退役 manifest 均 REFUSED，见 §6）
ADR030_STATUS                       = JPROV-001 active（LEGAL 层 jurisdictional proviso）
ADR031_STATUS                       = holder_scope 语义收口（runtime 参与 Resolver）
ADR032_STATUS                       = 独立 additive track（未触碰历史行，不阻塞 Wave02）
REAL_PLACE_COUNT                    = 20 → 30（Wave02 新增 10 个真实场所）
REAL_GEO_COVERAGE                   = 30 / 30（OSM Nominatim 真实坐标 + 全量 provenance）
PRODUCTION_INTEGRITY_CRITICAL       = 0
PRODUCTION_INTEGRITY_HIGH           = 0
```

## 1. 接手时 repo 状态

接手时 `git status`（HEAD=`6400fc1`）存在未提交改动，归类为既有的 **AccessAnswer 消费端迁移 WIP**：

- 修改：`apps/client-h5/src/views/{Home,Map,MatchExplain,Place,Search}View.vue`、
  `packages/client-core/src/modes/query.ts`、`packages/client-core/src/platform/map.ts`、
  `services/api/app/db/seed.py`
- 未跟踪：`apps/client-h5/src/answer.ts`

本 Goal 将其完成、测试并提交（见 AccessAnswer 迁移章节），未丢弃任何用户工作。

## 2. 本次接管期间的 worktree 变化

除 AccessAnswer 迁移已提交外，工作区新增（未提交、本次 Goal 的 Wave02 产物）：

- `docs/expansion/expansion_r1_wave02_evidence.json`（证据文件，20 条候选，含 OSM 真实坐标 provenance）
- `docs/expansion/expansion_r1_wave02_manifest.json`（ingest 记录）
- `docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md` / `WAVE02_HUMAN_REVIEW_QUICK_TABLE.md` /
  `review_decisions_expansion_r1_wave02.json`（人工复核三件套，Human 字段全空）
- `scripts/expansion_w02_ingest.py`、`scripts/wave02_section29_gates.py`、
  `scripts/wave02_review_packet.py`、`scripts/wave02_candidate_correction.py`、
  `scripts/wave02_monitor_dedup.py`
- 修改：`services/api/app/rulespec/source_scope_semantics.py`（声明 `犬类`→dog、`猫类`→cat 阅读）
- 修改：`tests/unit/test_wave01_semantic_bridge.py`（pin 新阅读）

无 reset / 无 checkout 覆盖 / 无弃置本地修改。

## 3. Century Park 发布事实

Century Park（w01-4e217d5810）已由历史轮次真实发布（授权来源 ROUND6），
生产库 `access_rule 149828d0-…`，`source_type=government_service`、
`directness=secondary`、`operator_first_party_verified=false`、
`FIRST_PARTY_OPERATOR_SOURCE_PENDING=true`，与 Evidence Acceptance 逐字一致。
本 Goal 未重跑也未改动该发布。

## 4. Wave01 复验（重测，非复述）

`scripts/wave01_approved_disposition_audit.py`（registry=`artifacts/wave01_register_reprojected.json`、
acceptance 同步）重跑实测：

```
REVISION                  = EXP-R1-W01-REVIEW-R1
APPROVED_TOTAL            = 15
ALREADY_PUBLISHED_APPROVED= 12   （含世纪公园本次计入）
SUPERSEDED_APPROVED       = 3    （w01-3a04d4d1aa / w01-6f2bfd39d7 / w01-305fa08c1e）
CURRENTLY_EXECUTABLE_APPROVED = 0  ✅ Wave01 无「已批准且当前可执行未处理」候选
PUBLISH_BLOCKED_APPROVED   = 0
ZERO_DB_MUTATION           = True
```

Human Decision 文件（`review_decisions_*` 等）与 HEAD 逐字节一致（diff = 0），未改写任何决定。

## 5. 生产完整性

`scripts/check_production_integrity.py --db-name petaccess`：

```
PRODUCTION_INTEGRITY_SCAN = PASS（23 项）
CRITICAL = 0   CONFLICTING_CURRENT_RULES / CROSS_LAYER_EXCEPTION /
               HOLD_OR_REJECTED_PUBLISHED / ORPHAN_RULE_EXCEPTION /
               SELF_SUPERSEDE / SUPERSESSION_CYCLE 全为 0
HIGH     = 0   DUPLICATE_CURRENT_RULE / ORPHAN_{PLACE,ZONE} /
               PUBLISHED_WITHOUT_{AUDIT,EVIDENCE,SOURCE,CANDIDATE} / TEST_* 全为 0
MEDIUM   = 1   AUDIT_TARGET_ID_UNUSABLE（2647 行 / 4 组，历史存量，与本次无关）
```

## 6. 旧语义永久守卫（P0 invariant）

直接持 `load_manifest` 实测 3 个退役 planning manifests：

```
EXP_R1_W01_REVIEW_R1_BATCH_01    → BatchManifestError（OBSOLETE_NON_EXECUTABLE）
EXP_R1_W01_REVIEW_R1_BATCH_01A   → BatchManifestError
EXP_R1_W01_REVIEW_R1_BATCH_02    → BatchManifestError
EXP_R1_W01_REVIEW_R1_BATCH_03_CENTURY_PARK → 正常加载（live）
ALL_RETIRED_REFUSED              = YES
```

`superseded_semantics.json` 在 load_manifest / validate_manifest / build_plan
三层拒绝旧语义；相关 pytest（superseded/manifest/build_plan/disposition）39 passed。

## 7. AccessAnswer 迁移（已完成并提交 aee7bb8）

Home / Search / MatchExplain / Map / Place 五点消费端全部改为调用统一
`POST /api/v1/places/{place_id}/access-answer`（新增 `apps/client-h5/src/answer.ts`），
`query.ts` 移除客户端 `evaluatePlace`（不再扁平化 zone）、`map.ts` 统一
MATCH→ALLOWED + STALE 词汇。`seed.py` 的 demo rule 补齐
`source_scope_exact/subject_scope_normalized/normalization_type`（`exact` 仅用于真等价，
`OTHER` 明确不在 exact 映射内，ADR-025 保真）。门禁：
pytest 825 passed/2 skipped、ruff/format 全绿、mypy 87 files、H5 build（vue-tsc+vite）通过、
ESLint 0、Prettier clean。

## 8. Wave01 收口复验结论

Wave01（EXP-R1-W01-REVIEW-R1）：**CURRENT_EXECUTABLE=0 · CRITICAL=0 · HIGH=0 ·
Human Decision diff=0 · superseded guard active = 全部满足**。
治理上 `30_50_PLACE_EXPANSION_R1 — WAVE_02` 解锁（ANIMAL_SCOPE_REMODEL_GATE=PASS、
PILOT_REVIEW_PUBLISH_GATE=PASS）。

---

## 9. Wave02 启动状态（本 Goal 的主体）

- REAL_PLACE_COUNT = 30，新增 10 个真实 Shanghai 场所（含 7 公园、2 景区、1 场馆），
  每个带 OSM Nominatim 真实坐标 + `osm_type/osm_id/display_name/licence/query/fetch` 溯源，
  无 mock geo、无随机坐标、无 LLM 猜测坐标。
- 证据链 Source→Artifact→EvidenceBundle→RULE_CANDIDATE（REVIEW_PENDING）经生产 API
  写入，DataSourceJob `EXP-R1-W02-20260919` 审计闭环。
- 候选 20 条，全部 REVIEW_PENDING、无 Human 字段；§29 全部位 gate probe 全 PASS
  （SOURCE_SCOPE / LAYERING / ZONE / REACHABILITY / ADR030 / ADR031 / EVIDENCE /
  FRESHNESS / LICENSE / CONFLICT / SUPERSESSION / GUIDE_DOG / CONDITION_SCHEMA）。
- SourceMonitor 9 个（9 个独立来源各 1，和平/昆山共享虹口 pilot source），无重复。
- Wave02 数据真实，来源为官方/政府一手或政府转述（含 1 处二级来源 顾村公园 → lead，
  标注 needs_verification）。

## 10. 唯一待办（人工）

```
HUMAN_ACTION_REQUIRED = WAVE02_FINAL_DECISIONS
```

复核包已就绪，20 条说明见 `docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md`；
等待 Kaiser / huangdi97 逐条给出 APPROVED / HOLD / REJECTED。