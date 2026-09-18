# DATA_QUALITY_REPORT — 数据质量与缺陷清单

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 候选分布

**rule_layer**：LEGAL×10、OPERATOR_POLICY×21

**effect**：allowed×2、conditional×14、prohibited×15

**animal_scope**：dog×12、ordinary_pet×14、other×2、service_dog×3

**normalization_type**：exact×24、legal_interpretation_required×7

**mandatory_level**：mandatory×10、operator_discretion×21

**review_status**：REVIEW_PENDING×31

## 2. ADR-025 作用域字段完整性

| 字段 | 非空数 / 总数 |
|---|---|
| source_scope_exact | 31 / 31 |
| subject_scope_normalized | 31 / 31 |
| normalization_type | 31 / 31 |
| normative_effect | 31 / 31 |
| holder_scope | 31 / 31 |

## 3. 零惰性规则检查（§26）

本轮候选均为 base 层规则候选，未创建任何 RuleException。如后续为某条 base 创建 carve-out，必须校验 base 语义上确实管辖该例外主体，否则判定 `SEMANTIC_REMODEL_REQUIRED`。

## 4. 本轮发现并修复的缺陷

| # | 缺陷 | 处置 |
|---|---|---|
| 1 | `next_check_at` 仅在 sweep 后写入，创建时不写，导致监控建而不跑 | 创建时初始化为 `now()`，并回填存量 |
| 2 | 无到期监控的调度入口，监控舰队从未被扫描 | 新增 sweep 服务、API 端点与 Celery beat 任务 |
| 3 | 429/503 的 `Retry-After` 未被遵守，只用通用退避 | 解析并优先遵守 `Retry-After`（含 HTTP-date） |
| 4 | 三次中断的 ingest 造成候选/bundle/artifact/monitor 重复 | 受治理清理（备份 + 已审阅 dry-run 计划），残留重复 0 |
| 5 | freshness_policy 因重复运行产生 4 套副本 | 收敛为每 source_type 一张 |

## 5. 本轮未修、如实记录的项

| # | 项 | 为何不本轮修 |
|---|---|---|
| 1 | SEMANTIC_REMODEL_ISSUE | 治理冻结项，须独立流程，不得顺手自动修复 |
| 2 | 5 个来源被反爬拦截（403） | 外部条件，非流水线缺陷；证据与规则不受影响 |
| 3 | 外部通知通道未实现 | 缺凭据与适配器，已按 NOT_IMPLEMENTED 申报 |
| 4 | amenity / entrance / access_path 为 0 | §16-§26 要求「仅当来源明示时」才建，本轮来源未明示 |

## 6. 未做的降级

- 未把 UNKNOWN 推断为 ALLOWED。
- 未为凑数放宽 Place Match。
- 未代填任何人工决策。
