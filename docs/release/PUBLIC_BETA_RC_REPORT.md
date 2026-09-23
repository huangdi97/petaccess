# PUBLIC_BETA_RC_REPORT — v0.9 Public Beta RC（2026-09-23）

> 母版 Phase 33（Release Candidate）与 Phase 34（Public Beta Gate）。全部状态为真实实测；
> 状态词：PASS / PASS_WITH_LIMITATIONS / NOT_VERIFIED / BLOCKED_EXTERNAL / BLOCKED_HUMAN / FAIL。

## 0. RC 冻结事实

| 条目 | 值 |
|---|---|
| HEAD | `6a48135` |
| BRANCH | `master` |
| WORKTREE | clean（`git status --porcelain` = 0 行） |
| TOTAL_COMMITS | 115（`git rev-list --count HEAD`） |
| RELEASE_TAG | `v0.5-quality-freeze`（历史唯一 tag；v0.9 RC 不新建 tag，发布授权后打） |
| MIGRATION_HEAD | `e9f2c1d4a5b6`（petaccess 与 petaccess_test 双环境实测） |
| MIGRATION_DRIFT | `alembic check` = No new upgrade operations（F1 闭合） |
| DB | PostgreSQL 17 / PostGIS 3.5 healthy；Redis healthy；MinIO running |
| BACKUP | 最新 drill 2026-09-23 PASS（`docs/backup/BACKUP_RESTORE_DRILL_REPORT.md`） |

## 1. 数据层（DB 实测，2026-09-23）

| 指标 | 值 |
|---|---|
| REAL_PLACES | 30（全部 active，真实上海坐标） |
| ACCESS_RULES | 42 current（LEGAL 14 / OPERATOR_POLICY 28） |
| RULES_WITH_SOURCE | 42/42 = 100% |
| RULE_CANDIDATES | 95（51 published） |
| SOURCES | 36（official_operator_policy 16 / external_web_reference 13 / government_service 4 / statute_or_regulation 2 / ordinary_user 1） |
| SOURCE_MONITORS | 22（active） |
| ZONES | 44 |
| RULE_EXCEPTIONS | 9 |
| DATA_LICENSE | **0 行 → FAIL**（许可未落库） |
| REALITY 各表（8 张） | 0 行（表结构齐全；数据为 INSUFFICIENT_OBSERVATION，未造数） |

## 2. 质量门（本轮全部实测）

| 门 | 结果 |
|---|---|
| pytest 全量 | **889 passed / 2 skipped**（TEST DB + Celery worker；fail-closed 生效） |
| ruff | PASS（All checks passed） |
| ruff format | PASS（255 files） |
| mypy（canonical services/api） | PASS（97 files / 0 errors） |
| H5 vue-tsc + build | PASS |
| Admin vue-tsc + build | PASS |
| Playwright E2E | **18 passed**（2026-09-23 重跑） |
| Visual regression | PASS（17 基线；`VISUAL_REGRESSION_BASELINE.md`） |
| a11y（机器可判定） | PASS（serious=0 / moderate=0 / minor=0，覆盖 consumer 12 页 + admin 10 页；`A11Y_AUDIT.md`） |
| design-token | PASS（硬编码色板 0） |

## 3. 专项门（Phase 26/28/29 实测报告）

| 门 | 结果 |
|---|---|
| Security | CRITICAL=0 / HIGH=0（`docs/security/SECURITY_FINAL_REPORT.md`；EXIF/XMP 剥离已落地） |
| Backup/Restore | PASS（`docs/backup/BACKUP_RESTORE_DRILL_REPORT.md`） |
| Observability | PASS_WITH_LIMITATIONS（`docs/ops/OBSERVABILITY_REPORT.md`；生产 exporter/告警为部署项） |

## 4. Public Beta Gate 判定（母版 Phase 34 逐项）

| 门 | 判定 | 依据 |
|---|---|---|
| Data | PASS_WITH_LIMITATIONS | 30 places / 42 rules / 36 sources；License 0 行 FAIL |
| Rule | PASS | 42/42 source；UNKNOWN≠ALLOWED；resolver 0 错；Human Decision 不可改写 |
| Reality | FAIL | Reality 8 表 0 行；30/30 INSUFFICIENT_OBSERVATION（未造数，诚实） |
| Consumer | PASS | H5 全页面（Home/Search/Map/Place/Contribute/Mine/…）build + E2E 通过 |
| Map | PASS_WITH_LIMITATIONS | Mock 图（lens UI 全）；真实 provider BLOCKED_EXTERNAL（TENCENT_MAP_KEY，B-04） |
| Admin | PASS | 30+ 视图（含 Reality Dashboard/Queue/Claims）；build + E2E 通过 |
| Contribution | PASS_WITH_LIMITATIONS | RealityReport 建模 + 贡献服务 + 防滥用已落地；完整 UX 深化待 Phase 12-19 收口 |
| Evidence | PASS | evidence_bundle 全覆盖规则候选；Evidence Viewer 存在 |
| Privacy | PASS | staff 仅 actor_role；EXIF 剥离；位置最小化；媒体默认私有 |
| Security | PASS | CRITICAL=0 / HIGH=0 |
| Full Regression | PASS | 889 passed / 2 skipped |
| E2E | PASS | 18 passed |
| a11y | PASS | 机器可判定项全 0 |
| Backup/Restore | PASS | 2026-09-23 drill |
| Observability | PASS_WITH_LIMITATIONS | 生产级监控待部署 |
| Staging | BLOCKED_EXTERNAL | 无独立 staging 环境（Phase 31） |
| UAT | BLOCKED_HUMAN | 需要真实 7 类角色（Phase 32） |
| Production Infrastructure | BLOCKED_EXTERNAL | 无公网域名/HTTPS/对象存储/监控（Phase 30） |
| Compliance | BLOCKED_HUMAN | 备案/隐私条款/地图 SDK 条款/许可确认需人类（Phase 27） |

## 5. 总判定

```
READY_FOR_PUBLIC_BETA = NO
```

原因（按母版 Phase 34：全部 PASS 才 YES）：
1. Reality 数据 = 0（INSUFFICIENT_OBSERVATION，未造数）→ Reality 门 FAIL；
2. License 未落库 → Data 门带 FAIL 项；
3. Staging / UAT / Production Infrastructure / Compliance 为 BLOCKED_EXTERNAL / BLOCKED_HUMAN；
4. Map 真实 provider 缺 Key（B-04）。

已达成：代码/测试/安全/备份/可观测性本地全绿，RC 可冻结；
未达成：真实公网发布所需的外部条件与人类签署。

## 6. Release Notes（拟）

v0.9-R1 Reality Contribution 深化（Shanghai 中心城区试点）：
- RealityLayer：Rule（42）+ Reality（0，待真实贡献）+ Evidence 三层语义分离；
- RealityReport 父模型 + 7 状态枚举 + ObservationEffort + Confirmation + 防滥用；
- 30 real Places 全部坐标/规则/来源就绪；Consumer（H5）与 Admin 全治理面；
- 已知限制：Map 为 Mock（Key 未接）；Reality 无数据；License 未落库；无公网环境。
