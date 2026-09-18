# SCOPE-REMODEL-R2 签署后闸门报告（R1）

> 本轮起于 huangdi97 对 6 条 SCOPE-R2 候选的逐条决定，止于**真实发布授权点**。
> 生产库零写入（`REAL_PUBLISH_EXECUTED = NO`）。

## 0. 结论先行

| 指标 | 值 |
|---|---|
| `SIGNED_ROWS` | **6** |
| `APPROVED` | **5** |
| `HOLD` | **1** |
| `REJECTED` | **0** |
| `APPROVED_WITH_NOTE` | 0 |
| `PREPUBLISH_EVALUATED`（5 条 APPROVED） | **5** |
| `PREPUBLISH_PASS` | **5** |
| `PREPUBLISH_BLOCKED` | **0** |
| `SHANGHAI_ZOO_DOG_PUBLISHABLE` | **0** |
| `DISNEY_DOG_BASE_REACHABLE_BY_GUIDE_EXCEPTION` | **PASS** |
| `CROSS_LAYER_EXCEPTION` | **0** |
| `INERT_EXCEPTION` | **0** |
| `UNMODELED_SOURCE_SCOPE_REMAINDER` | **YES** |
| `REHEARSAL_EXECUTE`（BATCH-01，6 条原意清单） | **FAIL**（实测产生禁止状态） |
| `REHEARSAL_EXECUTE`（BATCH-02，4 条收窄清单） | **PASS** |
| `DRY_RUN_ZERO_DB_MUTATION` | **PASS** |
| `REAL_PUBLISH_EXECUTED` | **NO** |
| `HUMAN_ACTION_REQUIRED` | **SCOPE_REMODEL_R2_REAL_PUBLISH_AUTHORIZATION** |

**唯一需要人类先知道的判断**：Disney dog 的语义可达性成立（新 `dog` 基底确实 governs `guide_dog`，
carve-out 不再惰性），但**它的依赖例外本身不可发布**，因此 Disney dog 本轮**不能**发布 ——
不是决定被推翻，而是依赖闭包无法执行。

## 1. 机械写入人类决定

脚本 `scripts/sign_scope_remodel_r2_decisions.py`（为此 revision 新建，只写 4 个签署字段 +
2 个顶层字段；任何非签署字段变化即回滚）。

* 写入前硬闸门：revision 匹配、6 行、candidate_id 集合与授权集一致、签署字段全空白、
  决定词表合法、分布 5/1/0/0、HOLD 行必须且只能是带 `legal_applicability_caveat` 的那一行、
  例外必须挂在已批准的同层基底上。
* `decided_at = 2026-09-18T22:42:35+08:00`（执行时刻，timezone-aware）。
* `git diff` 核对：改动 **只有** `final_decision` / `reviewer` / `decided_at` / `decision_note`
  与顶层 `reviewer` / `decided_at` / `decision_summary`；证据、scope、layer、exception 对象逐字节未动。
* `ai_recommendation` 未被复制进 `final_decision`。

| candidate | 场所 / scope | 决定 | decision_note |
|---|---|---|---|
| `7b595de9…` | 迪士尼 / dog | APPROVED | 三标志 |
| `4580ab21…` | 迪士尼 / cat | APPROVED | 三标志 |
| `4ca5e55a…` | 迪士尼 / other | APPROVED | 三标志 |
| `a4e2ba26…` | 动物园 / dog | **HOLD** | `HIGHER_LEVEL_GUIDE_DOG_LEGAL_APPLICABILITY_UNRESOLVED` |
| `27893d75…` | 动物园 / cat | APPROVED | 三标志 |
| `2a3de3ab…` | 动物园 / other | APPROVED | 三标志 |

5 条 APPROVED 的 note 逐字记录：`CURRENT_ONTOLOGY_EXPRESSIBLE_SPLIT = YES`、
`SOURCE_SCOPE_FULL_REAL_WORLD_EXHAUSTIVE = NO`、`UNMODELED_SOURCE_SCOPE_REMAINDER = YES`，
并声明未建模的鸟类、爬行类等必须继续保持 `UNKNOWN / unsupported`，不得解释为 ALLOWED。

## 2. 旧冻结对象未变（实测）

* 3 条冻结候选（`305fa08c…` carve-out、`3a04d4d1…` 迪士尼旧基底、`6f2bfd39…` 动物园旧基底）
  与 materialize 前快照逐字段比对：**drift = 0**。
* 旧人工审查登记表 `docs/expansion/review_decisions_expansion_r1_wave01.json`
  sha256 `d331efeb…` 与快照一致：**未被改写**。
* 生产指纹 `569d3bb6…`（前后两次一致）：access_rule 14 / rule_exception 5 / candidate 74 / audit 9652。

## 3. Pre-Publish Gate（5 条 APPROVED，生产库只读）

`publish_reviewed_r1.py --dry-run --database-name petaccess`：

```
PREPUBLISH_GATE_RAN           = True
PREPUBLISH_APPROVED_EVALUATED = 6      # 5 条 SCOPE-R2 + 1 条导入依赖
PREPUBLISH_PASS               = 5
PREPUBLISH_BLOCKED            = 1      # w01-305fa08c1e（导入依赖，非 5 条之一）
HOLD_PUBLISHABLE              = 0
REJECTED_PUBLISHABLE          = 0
```

5 条 APPROVED **逐条 PASS**；`sr2-a4e2ba26f5`（动物园 dog）`publication_type = HOLD_NOT_PUBLISHABLE`，
`SHANGHAI_ZOO_DOG_PUBLISHABLE = 0`。

## 4. Disney dog 与 guide_dog carve-out：可达 ≠ 可执行

* **可达性（PASS）**：`publish_batch.is_reachable_carveout(迪士尼 dog, w01-305fa08c1e)` = **True**
  （Wave01 登记表里同一条是 `reachable=false` —— 旧基底 scope=`other` 不 governs `guide_dog`；
  新 `dog` 基底后转为可达）。`CROSS_LAYER_EXCEPTION = 0`、`INERT_EXCEPTION = 0`、
  `ZERO_INERT_RULES = PASS`。
* **可执行性（FAIL）**：`w01-305fa08c1e` 自身被 canonical 闸门 BLOCKED ——
  `schema_unsupported`：它的 `proposed_conditions` 用遗留键 `type`，规范要求 `condition_type`。
  ADR-029 §9 明文规定**已签署候选不得原地改写**，救济是「新候选 + 新人工审查」。
  本轮授权不含新建候选，故不能修。
* **实测后果**（演练库真执行 BATCH-01，6 条）：发布器把被 BLOCK 的例外**静默跳过**，
  于是迪士尼 dog 禁令落地而批准的导盲犬例外缺失 —— 解析器实测
  **上海迪士尼乐园 / 导盲犬 = prohibited**（应为 conditional）。这正是 canonical refusal 4
  要阻止的错误状态，因此 BATCH-01 已改名为 `SCOPE_REMODEL_R2_BATCH_01_BLOCKED.json`
  并写入 `_BLOCKED_DO_NOT_EXECUTE`。
* **暴露的闸门缺口**（记录，不自行改码）：`publish_reviewed_r1.py` 对「清单内被 BLOCK 的行」
  只跳过、不拒绝整批；批次校验因此会 PASS 而执行产生错误状态。建议后续在发布器加一条
  「selected-but-blocked ⇒ refuse」的拒绝（需人类授权改码）。

## 5. 收窄批次 BATCH-02（可执行）

`docs/governance/publish_batches/SCOPE_REMODEL_R2_BATCH_02.json`：
`sr2-4580ab2160` → `sr2-4ca5e55a6a` → `sr2-27893d75aa` → `sr2-2a3de3abde`（4 条），
`excluded_approved` / `deferred` 逐条写明 2 条被推迟的 APPROVED 及其解封条件。
**收窄不是推翻决定**：`sr2-7b595de9e0` 与 `w01-305fa08c1e` 的人类 APPROVED 全部保留，未发布而已。

## 6. 演练库真执行 + 幂等 + 验证

克隆 `petaccess → petaccess_publish_rehearsal_scope_r2`（14/5/74/9652，与生产一致）。

| 步骤 | 结果 |
|---|---|
| 执行 BATCH-02 | `ACCESS_RULE_CREATE_COUNT = 4`，`RULE_EXCEPTION_CREATE_COUNT = 0`，`BLOCKED_COUNT = 0`，`BATCH_VALIDATION = PASS` |
| 二次执行（幂等） | `NOOP_COUNT = 4`，`ACCESS_RULE_CREATE_COUNT = 0`，`SELF_SUPERSEDE = 0`，`DUPLICATE_PLAN = 0` |
| 计数 | access_rule 14→18，rule_exception 5（+0），candidate 74（+0），audit 9652→9660（+8） |
| 解析器（`scripts/verify_scope_r2_resolver.py`） | 变更 4 格，全部 `unknown → prohibited`：迪士尼猫/其他、动物园猫/其他。**犬类两格保持 unknown —— 导盲犬没有任何错误禁止** |
| 证据 / 来源 / 审计（`scripts/verify_scope_r2_publish.py`） | **VERIFY = PASS**：4 条规则各有 source、evidence_bundle（`evidence_class=original`）、`storage_allowed=True`；scope 三列逐字保留；候选 review_status=PUBLISHED；audit 12 行（`candidate.create`×4 / `candidate.transition`×8），动作全在词表内 |

## 7. 作用域语义检查（Disney cat/other、Zoo cat/other）

`validate_source_scope_semantic_compatibility`（canonical，按 `normalization_type` 分派）：

| 行 | source_scope_exact | subject | 结果 |
|---|---|---|---|
| 迪士尼 cat | 动物（导盲犬除外） | cat | compatible=True / compound_term_split 成员 |
| 迪士尼 other | 动物（导盲犬除外） | other | compatible=True |
| 动物园 cat | 动物 | cat | compatible=True |
| 动物园 other | 动物 | other | compatible=True |
| （参考）迪士尼 dog | 动物（导盲犬除外） | dog | compatible=True |
| （参考）动物园 dog | 动物 | dog | compatible=True |

## 8. 生产 dry-run 与完整性

* `--dry-run --database-name petaccess`：`DRY_RUN_ZERO_DB_MUTATION = true`；
  生产指纹前后同 `569d3bb6…`，逐键比对只有采集时间与文件名不同。
* 完整性扫描：CRITICAL 0 / HIGH 0 / MEDIUM 1（历史 `AUDIT_TARGET_ID_UNUSABLE` 2647 行，本轮前后不变）。
* `db_cross_checked = false`：生产 dry-run 未挂 admin token（登记表↔库一致性校验在**生产克隆**
  演练库上带 token 完成，两库候选行完全一致）。

## 9. 停止点

停在 **SCOPE_REMODEL_R2_REAL_PUBLISH_AUTHORIZATION**。
若授权发布 BATCH-02（4 条），命令为：

```
.venv/Scripts/python.exe scripts/publish_reviewed_r1.py --execute \
  --registry docs/expansion/review_decisions_scope_remodel_r2_publishable.json \
  --batch-file docs/governance/publish_batches/SCOPE_REMODEL_R2_BATCH_02.json \
  --database-name petaccess --reviewer huangdi97 --token <admin JWT> \
  --production-confirm --max-approve 10
```

未授权前不做：`--execute` 打生产、自动发布、改旧签名、启动 Wave02。

## 附：本轮新增脚本

* `scripts/sign_scope_remodel_r2_decisions.py`（机械签署，拒绝二次签署）
* `scripts/scope_remodel_r2_publish_register.py`（投影为发布器可消费登记表；跨 revision 导入依赖行）
* `scripts/verify_scope_r2_resolver.py`（多库解析器对照）
* `scripts/verify_scope_r2_publish.py`（来源/证据/审计/scope 三列验证）
