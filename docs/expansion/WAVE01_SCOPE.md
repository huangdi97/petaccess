# WAVE01_SCOPE — 本轮范围与不做什么

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 目标

30–50 Place 扩张的第一波。本轮目标不是「多 10 行」，而是验证数据生产闭环在真实数据上仍然**真实、可追溯、可核验、可监控、可版本化、可人工审查、可持续更新**。

## 2. 工作量拆分

| 工作流 | 内容 | 是否计入「新增 10 个」 |
|---|---|---|
| A | 补齐存量 7 个无规则场所 | 否 |
| B | 新增 10 个真实场所 | 是（精确 10） |

- A 流：新增证据 3 个，本轮无新证据 4 个
- B 流：10 个新场所，place_type 多样性 8
- 完成后 REAL_PLACE_COUNT = 20，WORKING_PLACE_COUNT = 待人工审核后统计

## 3. 地理范围

本轮**仅限上海**（试点法域）。未引入新城市、新法域、新法规体系。

## 4. 治理冻结（§1，本轮未触碰）

| 冻结项 | 值 |
|---|---|
| 已签署版本 | R2-FINAL-R3 |
| 人工复核人 | huangdi97 |
| 人工决策数 | 37（23 批准 / 9 HOLD / 5 拒绝） |
| 首个真实发布批次 | R2-FINAL-R3-BATCH-01B |
| 已发布规则 | 5 条 AccessRule + 3 条 RuleException |

当前校验：`access_rule = 5`，`rule_exception = 3`，与冻结值一致。

## 5. 本轮明确不做（§3 NO-GO）

1. 不代填人工 final_decision
2. 不自动发布，不执行任何 batch `--execute`
3. 不自动修复 SEMANTIC_REMODEL_ISSUE
4. 不生成 ordinary_pet → guide_dog 惰性例外
5. 不用 OPERATOR_POLICY 例外覆盖 LEGAL
6. 不把社交线索直接发布为规则
7. 不为凑够 10 个而伪造证据
8. 不把 UNKNOWN 推断为 ALLOWED

## 6. 本轮实际写入的数据

| 对象 | Wave01 数量 |
|---|---|
| rule_candidate | 31 |
| source_artifact | 14 |
| evidence_bundle | 21 |
| source_monitor | 10 |
| place | 10 |

全部经 Service/Domain 层（API）写入，无绕过服务的裸 SQL 插入，无「先插入后补来源」。
