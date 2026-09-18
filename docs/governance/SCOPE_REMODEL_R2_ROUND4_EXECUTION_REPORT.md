# SCOPE-REMODEL-R2 第四轮：carve-out 签署 → 投影 → 批次 → 演练

> 授权来源：huangdi97 于本轮授权机械签署 1 行（决定值由人给定：APPROVED）。
> 决定内容是**人给的**，脚本只负责写入与证明；本文件是执行证据，不是决定本身。

## 1. 签署（机械写入）

`scripts/sign_scope_remodel_r2_carveout_decision.py`：只写 4 个签署字段 + 2 个顶层字段，
写入前后对「非签署字段」做 sha256 比对，不一致即回滚。

硬闸门（写入前全部通过）：

| 闸门 | 值 |
|---|---|
| revision / 行数 / candidate_id | SCOPE-REMODEL-R2 / 1 / `69e0916a…` |
| remediates | `305fa08c-1edd-4cc9-9b7e-554647e44b0a`（未被重新指向他处） |
| 签署字段 | 全部空白（拒绝二次签署） |
| 决定值 | `APPROVED`（在规范词表内） |
| **依赖闭包** | 基底 `7b595de9…` 在已签署登记表中 `final_decision=APPROVED`、`decided_at` 非空 |
| 跨层绑定 | 无（`same_layer=true`，`cross_layer_dropped=[]`） |

结果：`final_decision=APPROVED`，`reviewer=huangdi97`，
`decided_at=2026-09-19T00:01:16+08:00`（timezone-aware），
`decision_note` 记录「维持对 w01-305fa08c1e 的原批准；新候选唯一改动为条件键规范化；
必须与基底 sr2-7b595de9e0 同批发布」。

`git diff` 只含 4 个行内签署字段 + 顶层 `reviewer`/`decided_at`/`decision_summary`。

## 2. 投影（基底 + 例外进同一张登记表）

`scripts/scope_remodel_r2_carveout_publish_register.py --execute`
→ `docs/expansion/review_decisions_scope_remodel_r2_dog_publishable.json`

- 两行：基底 `sr2-7b595de9e0`（APPROVED）+ 例外 `sr2-69e0916a2f`（APPROVED）
- `is_reachable_carveout` = **True**，`same_layer=True`
- 两份签名均**逐字复制**，未重新计算
- 冻结的 `w01-305fa08c1e` 刻意不在表内（它会让批次不可执行）

## 3. 批次清单

`docs/governance/publish_batches/SCOPE_REMODEL_R2_BATCH_03.json`
`candidate_rule_ids = ["sr2-7b595de9e0", "sr2-69e0916a2f"]`（位置即顺序：例外在基底之后）。

## 4. 生产 dry-run（只读，零突变）

```
BATCH_DEPENDENCY_CLOSED     = PASS
BATCH_EXECUTION_ORDER        = sr2-7b595de9e0 -> sr2-69e0916a2f<-sr2-7b595de9e0
BATCH_VALIDATION             = PASS
PREPUBLISH_APPROVED_EVALUATED = 2    PREPUBLISH_PASS = 2    PREPUBLISH_BLOCKED = 0
ACCESS_RULE_CREATE_COUNT     = 1     RULE_EXCEPTION_CREATE_COUNT = 1
NOOP_COUNT = 0   BLOCKED_COUNT = 0   SELECTED_BUT_BLOCKED = 0
ZERO_INERT_RULES             = PASS
DRY_RUN_ZERO_MUTATION        = PASS（指纹 2fafa05a… 前后一致）
```

> 第一次提交清单时带了 `dependency_closed` / `register` / `replaces` 三个字段，被
> `publish_batch` 的未知字段闸门直接 REFUSED（exit 4）—— 它拒绝静默忽略。
> 已把这些信息并入 `note` 后重跑通过。

## 5. 演练库真执行（克隆自生产）

```
ACCESS_RULE_CREATE_COUNT    = 1
RULE_EXCEPTION_CREATE_COUNT = 1
CLI_PUBLISH_AUDIT_CONTRACT  = PASS
幂等复跑：CREATE 0 / NOOP 2（无重复、无自超）
```

例外落库行 `cc2a6ccf…`：`animal_scope=service_dog`、`effect=conditional`、
`source_scope_exact='导盲犬'`、`subject_scope_normalized='guide_dog'`、
`normalization_type='exact'`、`normative_effect='exempt_from_prohibition'`、
`holder_scope='person_with_disability'`、`status=current`；证据包 `573cd58f`
`class=original`，artifact 许可 storage/display=True。

## 6. 解析器（生产 vs 演练）

| 场所 | 主体 | 生产 | 演练 BATCH-03 |
|---|---|---|---|
| 上海迪士尼乐园 | 普通犬 | unknown | **prohibited** |
| 上海迪士尼乐园 | 导盲犬 | unknown | **conditional** |
| 上海迪士尼乐园 | 猫 / 其他宠物 | prohibited | prohibited（不变） |
| 上海动物园 | 犬类 / 导盲犬 | unknown | unknown（HOLD，不变） |

`changed_cells = 2`。**导盲犬得到的是 conditional（有条件允许），不是 prohibited** ——
这正是上一轮 6 条清单被判定为错误状态的那一个格子。

## 7. 冻结对象与全局校验

- 冻结候选 `305fa08c…` sha256 `94cea72f…` **未变**（FROZEN_UNCHANGED）
- 生产计数未变：access_rule 18 / rule_candidate 75 / rule_exception 5 / audit_log 9662
- 生产完整性：CRITICAL 0 / HIGH 0 / MEDIUM 1（历史项，未变）
- 已发布 BATCH-02 回归验证：VERIFY = PASS
- `pytest` **783 passed / 2 skipped**；`ruff` 全绿（顺手修了 `adr030_holder_scope_probe.py`
  一处 102 字符的超长行 —— 上一轮提交留下的，与本轮无关）

## 8. 本轮修掉的一个验证器缺陷

`verify_scope_r2_publish.py` 原来按 `rule_candidate.published_rule_id` 找 `access_rule`，
但**例外候选的 `published_rule_id` 指向基底规则**（例外本身没有 access_rule 行），
于是拿基底的 scope 三列去比例外候选，报出 3 条并不存在的「漂移」。已改为：
`normative_effect=exempt_from_prohibition` 的行改从 `rule_exception` 解析
（用 note 里的 `from candidate <uuid>` 反查），修正后 VERIFY = PASS。

## 9. 停点

```
REAL_PUBLISH_EXECUTED = NO
HUMAN_ACTION_REQUIRED = SCOPE_REMODEL_R2_BATCH_03_REAL_PUBLISH_AUTHORIZATION
```

生产发布命令（待授权）：

```
.venv/Scripts/python.exe scripts/publish_reviewed_r1.py --execute \
  --registry docs/expansion/review_decisions_scope_remodel_r2_dog_publishable.json \
  --batch-file docs/governance/publish_batches/SCOPE_REMODEL_R2_BATCH_03.json \
  --database-name petaccess --reviewer huangdi97 --token <admin JWT> \
  --production-confirm --max-approve 10
```
