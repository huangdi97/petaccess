# FRESHNESS_MATRIX — 新鲜度矩阵

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 覆盖率

| 指标 | 值 |
|---|---|
| 来源总数 | 26 |
| 有 freshness_policy_id | 26 |
| 有 last_verified_at | 26 |
| 有 review_due_at | 26 |

覆盖率：26/26、26/26、26/26

## 2. 复核周期

| review_interval_days | 来源数 |
|---|---|
| 180 | 15 |
| 365 | 2 |
| 90 | 9 |

周期按来源类型确定：法规 365 天、政务/外部参考 180 天、运营方政策与现场标识 90 天。

## 3. 关键语义（§35）

> **`review_due_at` 表示「需要重新核验」，绝不等于「规则失效」。**

这是新鲜度模型里最危险的误读：把关复核人若把逾期来源视为过期，会静默撤回仍在生效的规则。本项目的行为是——逾期来源**照常参与解析**，仅在治理视图中标记为需复核。

## 4. 本轮处理

- 27 个来源全部补齐 `freshness_policy_id` / `last_verified_at` / `review_due_at`。
- `last_verified_at` 取 `COALESCE(last_verified_at, observed_at, published_at, collected_at)`，不伪造为当前时间。
- 三次中断的 ingest 运行产生了 4 套重复的 freshness_policy，已收敛为「每 source_type 一张规范策略」，策略表由 21 张降到 3 张（在用的旧策略保留，避免无谓改动）。
