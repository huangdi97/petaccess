# WATCH_READINESS — 关注（Watch）就绪度

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 结论

| 项 | 状态 |
|---|---|
| 后端订阅/去重/退订 | **PASS** |
| 外部真实投递（短信/邮件/推送） | **NOT_IMPLEMENTED** |

## 2. 已验证的后端行为

| 行为 | 结果 |
|---|---|
| 重复订阅同一 (user, target) | 幂等，不产生第二行 |
| 退订 | 置 `UNSUBSCRIBED`，从扫描中排除 |
| 退订后重新订阅 | 复用同一行并置回 ACTIVE |
| PLACE / ZONE / RULE 三类目标 | 视为不同订阅 |
| 通知去重 | 以 `last_notified_at` 为水位，避免重复发送 |

## 3. 诚实申报的未实现项

通知 provider 当前为 `MockNotificationProvider`：`send()` 可调用并记录，但**没有任何真实外部通道适配器**（短信/邮件/推送均未接入）。

因此「关注功能可用」这句话只在「站内/后端记录」范围内成立。把它写成「已支持通知」会是这份报告里唯一一条读者照做就会出错的结论。

## 4. 时钟域

通知扫描的比较水位与时间戳**同域**：`now` 取自 `SELECT now()`，与 `AccessRule.updated_at`（数据库写入）同属数据库时钟。容器时钟与主机时钟存在已知偏差，混用两个时钟域会导致扫描重复通知。
