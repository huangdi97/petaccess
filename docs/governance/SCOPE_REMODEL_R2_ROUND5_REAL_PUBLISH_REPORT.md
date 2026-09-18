# SCOPE-REMODEL-R2-BATCH-03 真实生产发布报告

> 授权：huangdi97 明确授权 `SCOPE_REMODEL_R2_BATCH_03_REAL_PUBLISH`，范围严格限定为
> 清单 `SCOPE_REMODEL_R2_BATCH_03.json` + 登记表 `review_decisions_scope_remodel_r2_dog_publishable.json`，
> 预期写入 CREATE_ACCESS_RULE=1 / CREATE_RULE_EXCEPTION=1，不得扩大。

## 0. 授权范围外的动作（单独记录，不与数据库审计混同）

仓库根目录 0 字节文件 `0` 已删除（单独确认：size=0、`git status` 显示 `??` 未跟踪、
无任何代码/配置引用、由 shell redirect 误建于 2026-09-18 23:17）。**与本次生产发布不是同一审计事件。**

## 1. 执行前闸门复核（生产库，只读）

```
PRODUCTION_DATABASE          = petaccess
BATCH_SELECTED               = 2
FINAL_EXECUTABLE             = 2   （计划中两行 gate 全 PASS，无 NOOP / BLOCKED）
BATCH_DEPENDENCY_CLOSED      = PASS
BATCH_EXECUTION_ORDER        = sr2-7b595de9e0 -> sr2-69e0916a2f<-sr2-7b595de9e0
CROSS_LAYER_EXCEPTION        = 0
ZERO_INERT_RULES             = PASS
HOLD_SELECTED                = 0
REJECTED_SELECTED            = 0
PREPUBLISH_APPROVED_EVALUATED= 2    PREPUBLISH_PASS = 2    PREPUBLISH_BLOCKED = 0
SELECTED_BUT_BLOCKED         = 0
```

> 说明：`FINAL_EXECUTABLE` 的权威出处是发布器计划本身（两行均为可执行步骤）。
> `w01_semantic_bridge.py` 里的同名指标是 Wave01 专用的，不适用于 SCOPE-REMODEL-R2。

## 2. 首次 execute

```
ACCESS_RULE_CREATED          = 1    → 892643b0-8934-42ed-98e5-19c21d8fa833
RULE_EXCEPTION_CREATED       = 1    → a9f564bb-30bd-45c2-86a8-745272563fad
FAILED                       = 0
CLI_PUBLISH_AUDIT_CONTRACT   = PASS（checked 2 / missing 0）
```

## 3. 第二次 execute（同一清单）

```
ACCESS_RULE_CREATE_COUNT     = 0
RULE_EXCEPTION_CREATE_COUNT  = 0
NOOP_COUNT                   = 2
NEW_WRITES                   = 0
FAILED                       = 0
```

## 4. Disney Resolver 矩阵（真实 API `/places/{id}/effective-rules`）

| 查询 | effect | applied | missing_inputs |
|---|---|---|---|
| ordinary dog | **prohibited** | 0 | — |
| guide_dog，未提供 holder | **conditional** | 0 | `['holder_scope']` |
| guide_dog + `person_with_disability` | **conditional**（例外**已应用**） | **1** | — |
| generic service_dog | prohibited | 0 | — |
| police_dog | prohibited | 0 | — |
| military_working_dog | prohibited | 0 | — |

`SERVICE_DOG / POLICE_DOG / MILITARY_DOG_OVERGENERALIZATION = 0` —— 三者都没有命中
这份 guide_dog 但书。

**关于「statutory holder matches → statutory exception applied」的实际结果**：
例外确实进入 `applied_exceptions`（`a9f564bb…`），但 `effect` 仍是 **conditional** 而非
`allowed` —— 因为该 but 书自带条件（须栓系绳、部分游乐项目可能不允许）。
这正是授权书第 8 条要求的：**不把 conditional 显示成 unconditional allowed**。

## 5. RuleException 绑定

- `rule_exception.rule_id = 892643b0…` = **新建的 dog 基底**（`animal_scope=dog`、
  `source_scope_exact='动物（导盲犬除外）'`），不是旧的 `other` 基底 `0d2f70f8…`
- `is_reachable_carveout = True`、`same_layer = True`（均 OPERATOR_POLICY）
- `holder_scope = person_with_disability`、`subject_scope_normalized = guide_dog`、
  `normalization_type = exact`、`normative_effect = exempt_from_prohibition`

## 6. Evidence / Source / Audit

`VERIFY = PASS`：两条新对象各有 source + `evidence_class=original` 证据包、
scope 三列逐字保留、审计 6 行（candidate.create 2 / candidate.transition 4）全在词表内。

**Execution Actor 与 Human Reviewer 分字段记录**：
审计行 `actor_role=admin` / `actor_user_id=<admin user>`（执行者），
人类评审员 `huangdi97` 记在登记表的 `reviewer` 与发布回执的 `reviewer` 字段（不写入审计的 actor）。

## 7. 历史保护

快照前后比对（`scope_remodel_r2_publish_snapshot.py --diff before after`，`problems=[]`）：

| 项 | 结果 |
|---|---|
| 旧冻结候选 `305fa08c…` sha256 | 不变（FROZEN_CANDIDATES_MUTATED = 0） |
| 旧 Human Review 登记表（Wave01 / sr2 / carve-out 三份） | 字节不变（OLD_HUMAN_REVIEW_DIFF = 0） |
| 旧 published rules / exceptions | `changed = []`，只有新增 |
| source_monitor 行 | 13 行全部字节不变（monitor history 未被重置） |
| 计数 delta | access_rule +1、rule_exception +1、audit_log +4，其余 0 |

## 8. Production Integrity

```
CRITICAL = 0   （CONFLICTING_CURRENT_RULES / CROSS_LAYER_EXCEPTION / HOLD_OR_REJECTED_PUBLISHED /
                 ORPHAN_RULE_EXCEPTION / SELF_SUPERSEDE / SUPERSESSION_CYCLE 全 0）
HIGH     = 0   （DUPLICATE_CURRENT_RULE / ORPHAN_* / PUBLISHED_WITHOUT_* 全 0）
MEDIUM   = 1   （历史项，与发布前一致）
```

## 9. 最终指标

```
REAL_PUBLISH_EXECUTED              = YES
BATCH_ID                           = SCOPE-REMODEL-R2-BATCH-03
BATCH_SELECTED                     = 2
ACCESS_RULE_CREATED                = 1
RULE_EXCEPTION_CREATED             = 1
FAILED                             = 0
SECOND_EXECUTE_NOOP                = 2
DISNEY_ORDINARY_DOG                = prohibited
DISNEY_GUIDE_DOG_NO_HOLDER         = conditional
DISNEY_GUIDE_DOG_MATCHING_HOLDER   = conditional（applied_exceptions=1，例外已应用，非无条件 allowed）
SERVICE_DOG_OVERGENERALIZATION     = 0
POLICE_DOG_OVERGENERALIZATION      = 0
MILITARY_DOG_OVERGENERALIZATION    = 0
RULE_EXCEPTION_REACHABLE           = PASS
SAME_LAYER                         = PASS
EVIDENCE_LINKAGE                   = PASS
SOURCE_LINKAGE                     = PASS
AUDIT_LINKAGE                      = PASS
OLD_FROZEN_CANDIDATES_MUTATED      = 0
OLD_HUMAN_REVIEW_DIFF              = 0
PRODUCTION_INTEGRITY_CRITICAL      = 0
PRODUCTION_INTEGRITY_HIGH          = 0
```

生产指纹 `2fafa05a…` → `45f995a9…`。
post-publish 快照：`artifacts/scope_remodel_r2_round5/post_publish_snapshot.json`。
