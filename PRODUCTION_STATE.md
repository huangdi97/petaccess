# PRODUCTION_STATE.md

## Current Phase
P0_PILOT_REVIEW_PUBLISH（工作稿与工具链完成；写库被阻塞）

## Current Baseline
REAL_DATA_PILOT_10_R2（`REAL_DATA_PILOT_10_R2_REPORT.md`，R2 Gate PASS 有条件）

## Actual HEAD
`716b163`（本轮 P0 + P3 + P4 + P7/P13 增量已提交；前置基线 `08ee60c`）

## Expected Facts（R2 基线）
- Evidence completeness: 93.9%
- 33 RuleCandidate REVIEW_PENDING
- 3 ObservationCandidate lead-only
- Published: 0
- Service dog: 7/7
- Tests: 238/238 at R2 baseline

## Actual Facts（本轮实测）
- 真实 Place: 10
- RuleCandidate: 33（全部 REVIEW_PENDING）
- APPROVED / REJECTED / PUBLISHED: 0 / 0 / 0
- 数据库无关测试 + 契约测试: 194 passed / 20 deselected（DB 依赖用例）
- `ruff check .`: All checks passed
- `mypy services/api/app`: 74 files, no issues
- 全量测试（含 DB 依赖）: 无法执行（ENV-01）
- H5 构建 / Admin 构建: 均通过（两端各 65 个令牌入产物）

## 总判定
```text
READY_FOR_PUBLIC_BETA = NO
```
原因：P0 未 PASS（写库受 ENV-01 阻塞；最终审核决策受 GOV-01 治理红线阻塞），P1–P12 依纪律未启动。

## 阶段状态
| 阶段 | 状态 |
|---|---|
| P0 takeover audit | PASS |
| P0 review 工作稿 | PASS |
| P0 review 最终签署 | BLOCKED_EXTERNAL (GOV-01) |
| P0 第一批 Publish | BLOCKED_EXTERNAL (ENV-01) |
| P0 发布路径缺陷修复 | PASS（BLK-LAYER-01） |
| P1 30–50 扩量 | NOT_RUN（被 P0 Gate 阻塞） |
| P2 UX Freeze | PARTIAL |
| P3 UI / Frontend | PARTIAL |
| P4 Admin / Data Ops | PARTIAL（数据质量看板已实现；端到端验证待数据层） |
| P5 Real Provider | BLOCKED_EXTERNAL |
| P6 Backend Hardening | NOT_RUN |
| P7 Security/Privacy/Compliance | PARTIAL |
| P8 Perf/Reliability/Observability | PARTIAL |
| P9 Cross-platform Build | BLOCKED_EXTERNAL |
| P10 Staging | BLOCKED_EXTERNAL |
| P11 UAT | NOT_RUN |
| P12 Production Release | BLOCKED_EXTERNAL |
| P13 Post-launch | NOT_RUN |

## Next Action
1. 以管理员启动容器运行时并 `docker compose up -d` + `alembic upgrade head`（解 ENV-01）；
2. 由具名人类评审员填写 `docs/reality_audit/review_decisions_r1.json`（解 GOV-01）；
3. 执行 `python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>"`；
4. 处置 BLK-LAYER-02（`mandatory_level` 缺口）裁定；
5. 此后按 Master Goal 顺序进入 P1。

## Final Target
Shanghai central public Beta（不得宣称全上海/全国覆盖）。

## Truth Rule
Never mark PASS without actual evidence.
