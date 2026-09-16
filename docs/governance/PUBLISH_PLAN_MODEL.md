# 发布计划模型（PUBLISH_PLAN_MODEL）

> 适用：`scripts/publish_reviewed_r1.py`（GOV-01 首批真实发布的唯一执行入口）
> 相关：`docs/governance/RULE_EXCEPTION_PUBLISHING.md`、`docs/governance/POST_SIGNATURE_PUBLISHER_CLOSURE.md`

## 1. 一条流水线，两个出口

```
签署登记表（signed register）
  → 授权（authorisation）          只读 final_decision
  → 发布前校验（pre-publish gate） publish_gate.evaluate_for_publish（真实调用）
  → 发布分类（classification）     ACCESS_RULE / RULE_EXCEPTION / SUPERSEDE / NOOP / BLOCKED
  → 依赖规划（dependency planning）base AccessRule 先于其 RuleException
  → 计划（Plan）
  → dry-run：不写        |        execute：按序事务写入
```

`--dry-run` 不是「把登记表念一遍」。它打印的就是 `--execute` 将要消费的那个 `Plan`，
并且是对**真实数据库**调用**真实闸门**算出来的。否则「dry-run 通过」不表示任何东西。

同一条构造路径：`build_plan()` 对世界是纯的（数据库事实以参数传入），
所以它既能被穷举单测，也能被 execute 直接消费。**不存在**「一套假的 dry-run + 一套真的 execute」。

## 2. 授权：`final_decision` 是唯一来源

| 输入 | 作用 |
|---|---|
| `final_decision` | **唯一**发布授权。`APPROVED` / `APPROVED_WITH_NOTE` 才有资格进入闸门 |
| `proposed_decision` | 机器意见。只用于展示与比对（`human_overrides_ai`），**永不授权** |
| `recommendation_reason` | 同上，审计用途 |

| Human Decision | 结果 |
|---|---|
| `APPROVED` / `APPROVED_WITH_NOTE` | 进入 Pre-Publish 校验 |
| `HOLD` | `HOLD_NOT_PUBLISHABLE`，任何轮次都不可发布 |
| `REJECTED` | `REJECTED_NOT_PUBLISHABLE`，任何轮次都不可发布 |
| 空值 / 词表外 | `BLOCKED`（未签署） |

推论（并由测试锁定）：机器建议 APPROVE + 人类 HOLD ⇒ **不可发布**；
机器建议 HOLD + 人类 APPROVED ⇒ 可进入下一阶段，但**仍须**完整过闸门。

## 3. 发布类型

| 类型 | 含义 |
|---|---|
| `CREATE_ACCESS_RULE` | 新建基础规则 |
| `SUPERSEDE_ACCESS_RULE` | 新建基础规则，且会取代同来源/同归属/同 scope/同 action 的现行规则 |
| `CREATE_RULE_EXCEPTION` | 在已发布（或本批先发布）的基础规则上挂 carve-out |
| `NOOP_ALREADY_EXISTS` | 候选已是 `PUBLISHED`，无可做 |
| `BLOCKED` | 被拒，附原因 |
| `HOLD_NOT_PUBLISHABLE` / `REJECTED_NOT_PUBLISHABLE` | 人类裁决为挂起 / 拒绝 |

## 4. 顺序与确定性

排序键：`(是否可写, 是否例外, rule_id)`
⇒ 可写步骤在前、**base 先于 exception**、同级按 `rule_id` 稳定排序。

同一份登记表连续跑两次，`Plan` 必须逐字段相同（`tests/unit/test_publish_plan.py` 锁定）。
不得出现「第二次多一批 / 顺序随机 / 候选重复 / 例外重复」。

## 5. 计划自检（必须全为 0）

| 检查 | 含义 |
|---|---|
| `SELF_SUPERSEDE` | 某步骤把自己的产物或本批新建规则列为 supersedes 目标 |
| `DUPLICATE_PUBLICATION_PLAN` | 同一候选出现两次，或两条步骤写同一 (owner, source, scope, action, layer, effect) |
| `CROSS_LAYER_EXCEPTION` | 例外绑定了非同层 base |
| `SUPERSESSION_CYCLE` | `supersedes_rule_id` 链出现环（现行规则将无法判定） |

## 6. 依赖闭包

例外步骤的 base 必须满足：

1. 存在于本批登记表 **或** 库中已有对应现行规则；
2. 层与例外一致；
3. 本身是**可写类型**（`CREATE_*` / `SUPERSEDE_*`）。

任一条不满足 ⇒ 例外转 `BLOCKED`，并在 `blocked_reasons` 指名是哪一条。
因此「base 被 HOLD/REJECTED/闸门拦下」不会让例外被间接带进发布集。

## 7. 输出契约

`--dry-run --json` 输出 `summary`（含 `PREPUBLISH_*`、各类型计数、`DRY_RUN_ZERO_DB_MUTATION`）、
`integrity`（上面四类自检 + 明细）、`plan`（逐项 order / candidate / rule / place / layer /
human_decision / publication_type / depends_on / gate_result / gate_reasons / supersedes /
publishable）。

## 8. 只读保证

dry-run 只做 SELECT：

- 不 commit、不 flush 业务写入；
- 前后比对 `access_rule` / `rule_exception` / `rule_candidate` / `audit_log` 行数，写入报告；
- CLI 级端到端测试（子进程真实执行）与会话级测试各一份（`tests/integration/test_publish_exception.py`）。

dry-run 期间数据库不可用 ⇒ 闸门状态为 `NOT_RUN`（**不是** PASS），且 `--execute` 直接拒绝运行。

## 9. 批次上限

`--max-approve`（默认 20）是刻意的防盲批闸门。整批批准数超过上限时 dry-run 报 1 项前置问题并以 3 退出，
但**仍然完整打印计划**——上限是给人看的，不是隐藏信息的理由。要看签署后的真实前置状态，显式传 `--max-approve <n>`。
不要为了让绿灯而改默认值。
