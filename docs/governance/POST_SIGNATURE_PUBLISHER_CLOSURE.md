# Human Signature 之后的发布器闭环（POST_SIGNATURE_PUBLISHER_CLOSURE_R1）

> 轮次：POST_SIGNATURE_PUBLISHER_CLOSURE_R1
> 签署：revision `R2-FINAL-R3` · reviewer `huangdi97` · commit `8ac1925`
> 结论：**POST_SIGNATURE_PUBLISHER_GATE = PASS**（真实发布未执行）

## 1. 生命周期

```
PRE_SIGNATURE
  └─ 登记表由数据库证据链生成，签署字段全空
SIGNED                                  ← 8ac1925（人类裁决，不可变事件）
  └─ final_decision / reviewer / reviewed_at 齐备
PREPUBLISH_VALIDATED                    ← 本轮：闸门对每条 APPROVED 真实执行
  └─ publish_gate.evaluate_for_publish 逐条给 PASS / BLOCKED + reasons
DRY_RUN_READY                           ← 本轮：计划确定、自检全 0、零写入
REAL_PUBLISH                            ← 未进入
  └─ 需要：--execute、事务写入、base→exception 顺序、审计
POST_PUBLISH_VERIFIED                   ← 未进入
  └─ 需要：resolver 复核、Evidence/Source 复核、rollback、supersession、watch、audit
```

**签署 ≠ 可发布。** `PREPUBLISH_VALIDATED` 是独立关卡：人类授权是必要不充分条件。

## 2. 本轮修掉的三个 P0

### P0-01 `RuleException` 没有发布路径

`publish_reviewed_r1.py` 只会 `transition` + `publish`，没有 carve-out 概念，
11 条例外候选会被规划成普通 `AccessRule`（于是 resolver 见到两条同层规则取最严，豁免静默失效）。

处理：例外成为一等发布类型，带 base 依赖；写入走
`candidate_service.publish_exception()`，在**写入边界**拒绝跨层绑定。
详见 `docs/governance/RULE_EXCEPTION_PUBLISHING.md`。

### P0-02 计划用机器建议授权

dry-run 用 `proposed_decision` 计算计划，只有 preflight 读签署值。后果：一条被人类 HOLD 的行，
若机器曾建议 APPROVE，仍可能进入发布计划。

处理：授权只看 `final_decision`（`authorise()`），`proposed_decision` 降级为展示与审计字段
（`human_overrides_ai`）。`run()` 不再持有独立的决策逻辑——它现在只是同一个 planner 的薄包装。

### P0-03 dry-run 从不调用发布闸门

旧的 `signed=true` 只证明签署齐备，六项 Pre-Publish Validation 一项都没跑。

处理：`publish_gate` 拆成两个入口、一个实现：

| 入口 | 用途 |
|---|---|
| `evaluate_for_publish()` | 返回**全部**违规（按闸门顺序），dry-run 用 |
| `validate_for_publish()` | 抛第一条违规，`candidate_service.publish()` 用（薄包装） |

`DatabaseGate` 就是对真实会话调用前者。它**不会**长出自己的一套检查——
一旦如此，dry-run 就不再预测真实发布，跑它也就没有意义了。

## 3. 本轮数字（真实测量，非推断）

```bash
.venv/Scripts/python.exe scripts/publish_reviewed_r1.py --dry-run --max-approve 23 --json
```

| 项 | 值 |
|---|---|
| REVISION | `R2-FINAL-R3` |
| REVIEWER | `huangdi97` |
| TOTAL / APPROVED / HOLD / REJECTED | 37 / 23 / 9 / 5 |
| PREPUBLISH_GATE_RAN | `True`（真实数据库、真实闸门） |
| PREPUBLISH_APPROVED_EVALUATED | 23 |
| PREPUBLISH_PASS / BLOCKED | **23 / 0** |
| ACCESS_RULE_CREATE_COUNT | 12 |
| RULE_EXCEPTION_CREATE_COUNT | 11 |
| ACCESS_RULE_SUPERSEDE_COUNT / NOOP_COUNT | 0 / 0 |
| HOLD_PUBLISHABLE / REJECTED_PUBLISHABLE | 0 / 0 |
| CROSS_LAYER_EXCEPTION / SELF_SUPERSEDE / DUPLICATE_PLAN / SUPERSESSION_CYCLE | 0 / 0 / 0 / 0 |
| DRY_RUN_ZERO_DB_MUTATION | `True`（dry-run 前后 `access_rule` / `rule_exception` / `rule_candidate` / `audit_log` 行数逐一相同） |

`PREPUBLISH_PASS = 23` 是**当次**测量：闸门含 freshness（`STALE_DAYS = 180`，
比较证据 `collected_at` 与调用时刻），所以它是日期相关的。允许 `--now` 注入以便复现与测试。

绝对行数不写进本文件：集成测试会向开发库提交自己的夹具，计数会随跑测变化。
本条记录的是**不变量**（dry-run 前后一致），以及上面那些与数据库规模无关的判定结果。

默认 `--max-approve 20` 会因「批准数 23 > 20」退出 3 并完整打印计划——这是刻意的防盲批闸门，不是缺陷。
上限**没有**为了绿灯被改成默认值。

## 4. 与签署的关系

签署是**不可变事件**。本轮任何代码、测试、formatter、generator 都不得改动这些值：

- `gen_human_review_packet_r2_final.py` 现在通过 `preserve_signature()`（按 `candidate_id` 匹配，
  不按位置）在重新生成时**保留**已有签署；此前重跑生成器会把签署抹成空白；
- `.prettierignore` 覆盖 `docs/reality_audit/**/*.json`、`HUMAN_REVIEW_DECISIONS_*.json`、`**/*.md`，
  formatter 不得与生成器争夺签署文件；
- 快照双份保留：`snapshots/baseline.json`（签署前）与 `snapshots/post_human_signature_r3.json`（签署后），
  另存 `snapshots/baseline_r2_final_r2.json` 作为 R2 轮历史证据，互不覆盖。
  签署前后**非签署字段**必须逐键相同——由测试锁定，而不是由报告声明。

## 5. 本轮明确未做

- `REAL_PUBLISH_EXECUTED = NO`：未执行 `--execute`，未在真实库写任何 `AccessRule` / `RuleException`；
- 30–50 Place 扩量未进入；
- `PILOT_REVIEW_PUBLISH_GATE` 仍为 `NOT_RUN` / `BLOCKED_BEFORE_REAL_PUBLISH`：
  它还需要真实首批发布、resolver 复核、Evidence/Source 复核、rollback、supersession、watch、audit。

## 6. 何时才算可以真实发布

1. `--dry-run` 的这份计划被人类审阅确认（尤其 12 + 11 的分解与 `depends_on`）；
2. 逐条确认 `PREPUBLISH_PASS` 是当次结果（freshness 随时间变化）；
3. 明确 `--max-approve`（≥23）并接受这是一次整批写入；
4. 准备好回滚路径（`docs/ROLLBACK_RUNBOOK.md`）与发布后复核（resolver / effective-rules）；
5. 由人类发出 `--execute`，而不是由 agent 自行决定。
