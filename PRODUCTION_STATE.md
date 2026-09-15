# PRODUCTION_STATE.md

> 最后更新：2026-09-14（GMT+8）· 真实基线 HEAD `53c4c0339ffcaea54b7c4cced46ad7edd28d7bb1`
> 依据：`ENV01_RESOLUTION_REPORT.md`、`P0_PUBLISH_CLOSURE_REPORT.md`、`UI_CORE_CLOSURE_REPORT.md`

## Current Phase
P0_PUBLISH_CLOSURE + UI_CORE_CLOSURE + **ENV-01 解除**
（写库能力已就绪并经往返验证；仅剩 GOV-01 人类签署）

## Current Baseline
HEAD `53c4c03`（真实基线）。旧 `FINAL_PRODUCTION_READINESS_REPORT.md` 指向的 `716b163`
**早于**当前 HEAD，其结论不作为本状态依据。

## Actual HEAD
`53c4c0339ffcaea54b7c4cced46ad7edd28d7bb1`

## 环境（ENV-01 已解除）
| 依赖 | 状态 |
|---|---|
| Docker / docker-compose | 运行中（Docker Desktop 4.64.0 / Client 29.2.1） |
| PostgreSQL + PostGIS | **17.5 + 3.5.2**（5432，healthy） |
| Redis | **7.4.11**（6379，healthy） |
| MinIO | 运行中（9000-9001，bucket `petaccess-dev`） |
| Celery worker | `--pool=solo` 可运行（任务往返通过） |
| `/health/components` | **`all_ok: true`** |
| Alembic head | **`f4c9d2e7a831`**；up/down/up 往返 **PASS** |

## Actual Facts（本轮实测）
- 真实 Place: 273；Zone 30；AccessRule 163；RuleCandidate 145（其中 33 条为 R1 待审）
- 33 条候选：`REVIEW_PENDING`，层级/规范力已与登记表一致（LEGAL/mandatory 16）
- **全量 `pytest`（不 deselect）：324 passed / 0 failed**
- **Playwright 全量 E2E：14 passed / 0 failed**
- **Admin 端到端（真实 DB）：Rollback（新增 5 用例）/ Supersession / Evidence Review / Data Quality 全部验证通过**
- `ruff check` / `ruff format --check`（含 scripts）：PASS（132 files）
- `mypy`：PASS（76 source files）
- ESLint / Prettier：PASS
- H5 构建 / Admin 构建：PASS
- OpenAPI: 89 paths（admin 31）
- **BLK-LAYER-02: FIXED**（ADR-023）+ 迁移约束命名修复（ADR-024，`f4c9d2e7a831`）
- 发布门禁：预检**双重把关**（登记表 + 登记表↔库一致性）；未签署仍硬拒绝（exit 3）

## 总判定
```text
PILOT_REVIEW_PUBLISH_GATE = NOT PASS
READY_FOR_PUBLIC_BETA     = NO
```
原因：**仅剩 GOV-01**（缺具名人类评审员签署 33 条候选）。ENV-01 已解除，写库能力就绪。

## 阶段状态
| 阶段 | 状态 |
|---|---|
| P0 takeover audit | PASS |
| P0 review 工作稿（33 条） | PASS |
| P0 review 最终签署 | BLOCKED_EXTERNAL (GOV-01) |
| P0 第一批 Publish | **READY**（写库就绪；待签署即可执行） |
| P0 发布路径缺陷修复（BLK-LAYER-01） | PASS |
| P0 规范力缺口修复（BLK-LAYER-02 → ADR-023） | PASS（FIXED） |
| P0 迁移/数据一致性修复（ADR-024） | PASS（FIXED） |
| P1 30–50 扩量 | NOT_RUN（被 P0 Gate 阻塞） |
| P2 UX Freeze | PASS |
| P3 UI / Frontend（UI-CORE-CLOSURE） | **PASS**（含真实数据 E2E） |
| P4 Admin / Data Ops | **PARTIAL+**（数据质量 KPI 真实有效；L1 Rollback 已端到端验证；端到端**发布**验证待 GOV-01 签署） |
| P5 Real Provider | BLOCKED_EXTERNAL |
| P6 Backend Hardening | NOT_RUN |
| P7 Security/Privacy/Compliance | PARTIAL |
| P8 Perf/Reliability/Observability | PARTIAL |
| P9 Cross-platform Build | BLOCKED_EXTERNAL |
| P10 Staging | PARTIAL（依赖栈已可运行；未做 staging 部署） |
| P11 UAT | NOT_RUN |
| P12 Production Release | BLOCKED_EXTERNAL |
| P13 Post-launch | NOT_RUN |

## Next Action
1. 由具名人类评审员逐行签署 `RULE_REVIEW_SHEET_R1.md`（33 行），回填
   `docs/reality_audit/review_decisions_r1.json` 的
   `final_decision` / `reviewer` / `reviewed_at`（解 GOV-01）；
2. `python scripts/publish_reviewed_r1.py --dry-run` → 确认 `signed=true` 且库一致性校验通过；
3. `python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>"` → 首批 10–20 条真实发布；
4. 逐项校验 linkage / evidence / audit / resolver / effective-rules / client /
   rollback / supersession / watch；
5. `PILOT_REVIEW_PUBLISH_GATE = PASS` 后进入 P1（30–50 Place 扩量）。

## Final Target
Shanghai central public Beta（不得宣称全上海/全国覆盖）。

## Truth Rule
Never mark PASS without actual evidence.
