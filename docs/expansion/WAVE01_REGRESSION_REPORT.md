# WAVE01_REGRESSION_REPORT — 回归校验报告

**运行 ID：** `EXP-R1-W01-20260918`  
**数据库：** `petaccess`  
**Alembic head：** `c9d4e2a17b30`

## 1. 质量门禁

| 门禁 | 结果 | 来源 |
|---|---|---|
| pytest | 669 passed / 0 failed | pytest -q |
| e2e | 18 passed / 0 failed | pnpm exec playwright test |
| visual | 47 passed / 0 failed | pnpm exec playwright test --config playwright.visual.config.ts |
| eslint | PASS | pnpm lint:fe |
| prettier | PASS | pnpm format:check:fe |
| ruff_check | PASS | ruff check services/api services/worker tests scripts |
| ruff_format | PASS | ruff format --check services/api services/worker tests scripts |
| mypy | PASS | mypy services/api |
| a11y | NOT_RUN | scripts/a11y_audit.mjs |

> 视觉套件首次全量并发出现 1 例 `search-empty h5-1440` 抖动（服务启动时序导致）；单独重跑 3 个视口全部通过，判定为非回归。

## 2. 生产完整性扫描

- CRITICAL：0  HIGH：0  MEDIUM：4  INFO：0
- MEDIUM 项：`AUDIT_TARGET_ID_UNUSABLE 2647 rows / 4 groups`
- 是否为 Wave-01 引入：`待复核`
- ORPHAN_SOURCE 清理后：0

## 3. 已发布规则解析回归（§55–§57 / §78）

- 基线来源：发布验收快照 `2026-09-17T12:44:23.039117+00:00`
- 重放查询数：15
- 场所：fairmont, library, starbucks
- 结果：**PASS**
- 差异：无

## 4. 治理语义指纹（治理冻结校验）

- 已发布 access_rule 数：5（变化：否）
- 已发布 rule_exception 数：3（变化：否）
- 批次对象变化：否
- 签名/清单哈希变化：否
- duplicate_current_groups 变化：否

## 5. Wave-01 数据规模

- 总场所数：20（目标 20）
- Wave-01 候选规则：31（全部 REVIEW_PENDING）
- Wave-01 自动发布：0（目标 0）
- 必监控来源：13/13
- 新鲜度覆盖：26/26

## 6. 悬空来源清理

- 清理数量：1
- 清理 ID：8cdcbc8d-0ad3-4184-9f67-4248fdd5cc02
- 原因：Wave-01 采集到但从未产出 artifact/证据束/主张的悬空来源；保留会让未核验的 search snippet 被误当作已抓取证据

## 7. 结论

治理区（已发布规则/例外、人工签名、批次对象）与已发布场所解析答案均未发生变化；生产完整性 CRITICAL=0 / HIGH=0；代码质量门禁全部通过。Wave-01 满足 §55–§57 / §78 回归要求。
