# ADR-031 · holder scope 与 service role 语义收口（BATCH_02 最终发布前）

轮次：`ADR030_HOLDER_SCOPE_AND_SERVICE_ROLE_SEMANTICS_CLOSURE_R1`
基线：`869167f`（本轮开始时 HEAD）· 签署评审 `EXP-R1-W01-REVIEW-R1` · 评审员 `huangdi97`
生成时间：2026-09-18

---

## 0. 结论指标（§29 逐字输出）

```
ADR030_HOLDER_SCOPE_GATE                  = PASS
HOLDER_SCOPE_RUNTIME_ACTIVE               = YES
JPROV001_HOLDER_CONDITION_ACTIVE          = YES
GUIDE_DOG_MATCHING_HOLDER_TESTS           = 11/11
GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW = 0
SERVICE_DOG_OVERGENERALIZATION            = 0
POLICE_DOG_OVERGENERALIZATION             = 0
MILITARY_DOG_OVERGENERALIZATION           = 0
DOUBLE_APPLIED_EXCEPTION                  = 0
EXISTING_LEGAL_GUIDE_EXCEPTIONS           = 5
MISSING_HOLDER_SCOPE                      = 0
LEGACY_EXCEPTION_MIGRATION_REQUIRED       = YES
BATCH_02_SELECTED                         = 6
BATCH_02_FINAL_EXECUTABLE                 = 6
DRY_RUN_ZERO_DB_MUTATION                  = PASS
REAL_PUBLISH_EXECUTED                     = NO   （本轮未执行任何发布）
PLACE_GEO_PENDING                         = OPEN （本轮动议范围外；见 §9）
```

```
HUMAN_ACTION_REQUIRED = BATCH_02_REAL_PUBLISH_AUTHORIZATION_FINAL
```

**但必须先读 §9**：在本轮进行期间，另一条工作线已经把 BATCH_02 的 6 条真实发布到了
生产库。授权点因此变成"追认 / 回滚"的选择，而不是"是否发布"。

---

## 1. 修的是哪两个缺口

| 缺口 | 修前 | 修后 |
|---|---|---|
| **P0-01** `holder_scope` 不参与判定 | 行上有 `person_with_disability`，resolver 从不读 → 导盲犬对**任何**携犬人 `allowed` | `evaluate_holder()` 四态判定；不匹配→不应用；未知→`conditional` + `missing_inputs=['holder_scope']` |
| **P0-02** generic `service_dog` 命中导盲犬但书 | 查询展开为 4 个协助角色，存在性语义 → 父查询整体 `allowed` | 例外必须**完整覆盖**查询（`query ⊆ carve-out`）；未点名角色 → `conditional` + `missing_inputs=['service_role']` |

---

## 2. holder_scope 的 source of truth（§2）

```
HOLDER_SCOPE_STORAGE          = rule_exception.holder_scope (models/rule.py:281)
                                jurisdiction_exception.holder_scope (models/civic.py:136)
                                access_rule.holder_scope (models/rule.py:148)
                                rule_candidate.holder_scope (models/v05.py:171)
                                policy_template_rule.holder_scope (models/v05.py:93)
HOLDER_SCOPE_RUNTIME_CONSUMER = app.rulespec.holder_scope.evaluate_holder
                                ← v05_resolver.resolve(..., holder_context=...)
                                ← guide_dog_safety.probe_guide_dog_safety_path
CURRENT_RUNTIME_USAGE         = ACTIVE   （上一轮：DEAD —— 只有 holder_scope_allows 且无调用点）
```

**没有新增第二套字段。** 存储复用现有 `holder_scope` 列；`animal_scope.holder_scope_allows`
保留为布尔形状（供义务侧测试），内部委托给新模块，避免两份实现。

新增的是**查询侧**的临时上下文 `HolderContext`，它是 dataclass，不是列，也不落库（§4）。

---

## 3. holder 语义（§3）：四态，不是一个布尔

```python
class HolderMatch(StrEnum):
    NOT_REQUIRED   = "not_required"     # 规范没有 holder 限定
    MATCHES        = "matches"          # 有限定，且上下文满足
    DOES_NOT_MATCH = "does_not_match"   # 有限定，上下文明确不满足
    UNKNOWN        = "unknown"          # 有限定，但根本没有给出上下文
```

关键区分：**未提供 ≠ 不满足**。`HolderContext.of()`（给了但为空）是 `DOES_NOT_MATCH`；
`HolderContext.unknown()` / `None` 是 `UNKNOWN`。把两者混为一谈会拿"缺少输入"
冒充"法律结论"，所以 §7 要求第三态而不是三态里的两头。

---

## 4. 隐私边界（§4）

- `HolderContext` **只存在于一次请求的调用栈里**：读、判定、丢弃。
- 没有新增任何表/列，`PetProfile` 未动；残障状态不落库。
- API 侧 `holder_scopes` 是**可选请求体字段**，不传即为 `UNKNOWN`，绝不解释为"否"。
- 未来若要持久化，属于独立的隐私设计 + 用户授权，不在本轮。

---

## 5. JPROV-001 的 holder 条件来源（§5）

从实际来源读取，不从文档摘要推断：

- `jurisdiction_proviso_candidates_adr030.json` → `proviso_text_ref`：
  「**盲人**携带导盲犬的，不受本条规定的限制。」
- 生产库 `jurisdiction_exception` 行 `JPROV-001`：`holder_scope = person_with_disability`、
  `subject_scope_normalized = guide_dog`、`normalization_type = exact`、
  `applies_to_layer = LEGAL`、`binding = instrument`。

来源明确写了持有人限定 ⇒ 运行时必须携带 holder 谓词。现在已强制执行
（`HOLDER_CONDITION_ACTIVE_ON_PROVISOS = 1`）。

---

## 6. 判定式（§6）

```
subject matches
AND holder matches            ← 本轮新增
AND jurisdiction matches      ← instrument_source_ids 法律文件同一性
AND provision matches         ← layer + effect + scope（见 §11 限制）
AND time valid
⇒ carve-out applies
```

任何一条不满足 ⇒ **不应用**。holder 为 `UNKNOWN` 时既不应用也不判禁，
而是记 `pending_exceptions` 并让答案降级为 `conditional`。

---

## 7. 三种答案（§7 / §19）

| 查询 | effect | missing_inputs |
|---|---|---|
| A. 普通犬 | `prohibited` | — |
| B. 导盲犬 + holder 满足 | `allowed`，`applied_exceptions=['JPROV-001']` | — |
| C. 导盲犬 + holder 未知 | `conditional` | `['holder_scope']` |
| D. generic service_dog | `conditional` | `['service_role']` |

C 与 D 的实现位置：`v05_resolver` 末尾的 §7 降级分支。它只在**被扣留的例外确实
指向当前正在产生该禁令的基底**时触发——否则一条运营方层的扣留例外会把法定禁令
"软化"成 conditional，看起来像是运营方放宽了法律（§14）。

---

## 8. 真实运行时矩阵（§23，生产库 11 个 LEGAL 基底）

`scripts/adr030_holder_scope_probe.py --db-name petaccess`
产物 `artifacts/adr031/holder_probe_production.json`。

`no_place_exception` 模式（只留 JPROV-001，= 新发布基底的真实状态）：

| 场所 | 普通犬 | 导盲犬+满足 | 导盲犬+未知 | 导盲犬+不满足 | generic service_dog | 警犬 | 军犬 |
|---|---|---|---|---|---|---|---|
| CHARLIE'S 粉红汉堡（马当路店） | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| omitofee 上海首店 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 上海博物馆东馆 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 上海图书馆东馆 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 上海新天地朗廷酒店 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 上海苏河湾万象天地 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 兴业太古汇 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 前滩太古里 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 和平饭店（费尔蒙） | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 星巴克臻选上海烘焙工坊 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |
| 港汇恒隆广场 | prohibited | allowed ✓ | conditional | prohibited | conditional | prohibited | prohibited |

```
JURISDICTION_EXCEPTION_MATCHED = 11/11      （applied = JPROV-001）
GUIDE_DOG_MATCHING_HOLDER_WRONG_PROHIBITION = 0
GUIDE_DOG_UNKNOWN_HOLDER_UNCONDITIONAL_ALLOW = 0
GUIDE_DOG_NONMATCHING_HOLDER_STILL_ALLOWED  = 0
SERVICE_DOG / POLICE_DOG / MILITARY_DOG / HEARING_DOG OVERGENERALIZATION = 0
DOUBLE_APPLIED_EXCEPTION                    = 0
ORDINARY_DOG_NOT_PROHIBITED                 = 0
```

`full` 模式（场所级历史例外 + JPROV-001）同样全零 —— 即 §17 的"不双重生效"在生产库成立。

---

## 9. 必须上报的治理事实（本轮进行期间发生，非本轮所为）

```
BATCH_02_PRODUCTION_STATE   = ALREADY_PUBLISHED
PUBLISHED_AT                = 2026-09-18 13:30:13 UTC（容器时钟，比主机快约 23s）
ACTOR                       = admin (ccfe8e68-9319-55a8-a01b-156eee5a49dd)
EVIDENCE                    = audit_log: 6 × candidate.publish
                              target ids = bb259b10 / 519e0779 / 8f6e597c / 42c9a35e / 39ee0061 / 6f51e8c0
                              candidate ids = 052d19cc / 7de2f5d7 / df1645fe / 8ba2b49b / d1aee781 / e951785d
                              = BATCH_02 manifest 的 6 条，逐条对上
COMMITS                     = 896724c "Close PLACE_GEO_PENDING and publish BATCH_02"
                              1c10bbe "B2: materialise the SCOPE-REMODEL-R2 candidates on a rehearsal clone"
                              ee6e6dc "SCOPE-REMODEL-R2: production materialization report and review packet"
PLACE_GEO_PENDING           = 由 human:huangdi97 的 place.update 关闭（13:29:20 UTC）
```

即：本轮拿到的授权文档要求"不要 --execute BATCH_02 / 不要进入 B2、B4、B5"，
**本轮一条都没做**；但同一工作区里另有并行工作线完成了 BATCH_02 真实发布、B5 坐标回填、
B2 scope remodel 候选物化。生产库 `access_rule` 由 8 行变为 14 行，指纹由
`a4f55b14…`（上一轮基线）变为 `569d3bb6…`。

本轮发布器 dry-run 的结果是 6 条全部 `NOOP_ALREADY_EXISTS`，与上述事实一致。

**需要人决定的事**：追认这次发布，还是按越权流程处理（回滚 / 补充补签）。本轮不代决。

---

## 10. BATCH_02 重审（§25，不得沿用上一轮结论）

`scripts/w01_semantic_bridge.py --batch-id EXP-R1-W01-REVIEW-R1-BATCH_02`
（产物 `artifacts/adr031/bridge_full.txt`）。逐条：

| # | rule_id | 场所 | scope | 导盲犬门禁（含 holder） | 执行契约 | 结论 |
|---|---|---|---|---|---|---|
| 1 | `w01-052d19ccba` | CHARLIE'S 粉红汉堡（马当路店） | PASS | PASS | PASS | 可执行 |
| 2 | `w01-7de2f5d75b` | omitofee 上海首店 | PASS | PASS | PASS | 可执行 |
| 3 | `w01-df1645fe68` | 上海新天地朗廷酒店 | PASS | PASS | PASS | 可执行 |
| 4 | `w01-8ba2b49b01` | 上海苏河湾万象天地 | PASS | PASS | PASS | 可执行 |
| 5 | `w01-d1aee78159` | 前滩太古里 | PASS | PASS | PASS | 可执行 |
| 6 | `w01-e951785d1b` | 港汇恒隆广场 | PASS | PASS | PASS | 可执行 |

```
人类决定 / 证据 / 场所匹配 / Schema / 冲突 / 时效 / License / mandatory 层 /
source-scope 语义 / 辖区适用性 / holder scope / service role 语义 / 导盲犬安全 /
重复 / supersession / 执行契约 —— 16 类全过：6/6
legal_dog_blocked = 0   EXCLUDED_APPROVED 未因语义收紧而变化
```

门禁现在跑**三次**导盲犬查询（holder 满足 / 不满足 / 未知），`safe_to_publish` 要求：
普通犬仍禁、holder 满足时可执行、holder 不满足时不套用、holder 未知时不得无条件放行。

### 清单不可变性（§26）

`docs/governance/publish_batches/EXP_R1_W01-REVIEW-R1_BATCH_02.json`（实际文件名
`EXP_R1_W01_REVIEW_R1_BATCH_02.json`）**未被修改**，候选选择未变 ⇒ 不建立 BATCH_02A，
只生成新的审计结果。

---

## 11. 发布器 dry-run 零变更（§27）

```
total = 6   human_decisions = {APPROVED: 6}
prepublish_pass = 6   prepublish_blocked = 0
ACCESS_RULE_CREATE_COUNT = 0   RULE_EXCEPTION_CREATE_COUNT = 0   NOOP_COUNT = 6
CROSS_LAYER 0 / SELF_SUPERSEDE 0 / DUPLICATE_PLAN 0 / SUPERSESSION_CYCLE 0
6 条均为 NOOP_ALREADY_EXISTS（已发布，不重复发布）
```

```
PROD_FINGERPRINT_BEFORE = 569d3bb6b86437e07d8babfd6f39fa2b1d01bd81934c0bf887dcf70c8897053a
PROD_FINGERPRINT_AFTER  = 569d3bb6b86437e07d8babfd6f39fa2b1d01bd81934c0bf887dcf70c8897053a
ROW_DIFF = 0        SEMANTIC_DIFF = 0
DRY_RUN_ZERO_DB_MUTATION = PASS
```

（指纹与上一轮基线 `a4f55b14…` 不同，原因是 §9 的并行发布，不是本轮写入。）

---

## 12. 已发布 LEGAL 导盲犬例外审计（§15）

见 `docs/governance/LEGACY_EXCEPTION_MIGRATION_PLAN.md`：5 条，holder 全部正确，
`MISSING_HOLDER_SCOPE = 0`，迁移计划已出、未执行。

---

## 13. 已知限制（不阻断，但要在发布前知道）

1. **法条级区分不可表达（§22.12 的部分）**：`access_rule` 没有法条引用列，
   因此"同一部法律的另一条"目前只能用 (法律文件, layer, effect, scope) 近似。
   已验证这四种区分都生效；真正的法条级匹配需要 `access_rule` 增列 + 回填 + 人工审阅，
   会触碰已发布历史行，本轮不做。
2. **语义变更会改变线上答案**：generic `service_dog` 与"导盲犬但未声明持有人"
   两类查询从 `allowed` 变为 `conditional`。这是修复本身，不是回归；
   消费者需要靠 `missing_inputs` 触发追问（§21 的 hook 已在响应里，UI 未做）。
3. **规则层（非例外层）的 `holder_scope` 仍未参与判定**：本轮只收紧 carve-out，
   义务侧（`facilitation_required`）维持原状，避免 OPERATOR 层被法条用语污染（§14）。

---

## 14. 本轮改动的文件

```
services/api/app/rulespec/holder_scope.py            新增：HolderContext / HolderMatch / evaluate_holder
services/api/app/rulespec/animal_scope.py            新增 carve_out_covers；holder_scope_allows 改为委托
services/api/app/rulespec/v05_resolver.py            holder 条件 + 角色覆盖 + pending/duplicate + missing_inputs
services/api/app/rulespec/guide_dog_safety.py        门禁跑三种 holder 上下文
services/api/app/api/v1/v05.py                       holder_scopes 入参；missing/pending/duplicate 出参
tests/unit/test_adr030_holder_scope.py               新增：§22 的 13 项 + 安全计数矩阵
tests/unit/test_animal_scope.py                      test_02 补 holder 上下文 + 新增覆盖语义测试
tests/unit/test_jurisdiction_proviso.py              可达/未知/不匹配三态
tests/unit/test_rule_exceptions.py                   generic 查询改为 conditional
tests/integration/test_rule_exceptions.py            API 层四态
tests/fixtures/real_world_regression.json            3 处 generic working 查询期望改为 conditional
scripts/adr030_holder_scope_probe.py                 新增：真实运行时探针 + 已发布例外审计
docs/governance/LEGACY_EXCEPTION_MIGRATION_PLAN.md   新增
```

质量门：`pytest` 单元 600 passed · 集成 124 passed（含 worker）· `ruff check/format` PASS ·
`mypy` 86 文件 Success。

## 12. 追加：OPERATOR_POLICY 层实测（SCOPE-REMODEL-R2-BATCH-03 发布后）

前面 §8 的真实运行时矩阵覆盖的是 **LEGAL 层**的 11 个基底（JPROV-001 辖区级法定 but 书）。
本节补上此前缺失的一半：**OPERATOR_POLICY 层、且 but 书来自运营方自己**的场景
（上海迪士尼乐园 dog 基底 `892643b0…` + 例外 `a9f564bb…`，2026-09-18 16:36 UTC 发布）。

探针：`scripts/verify_scope_r2_disney_matrix.py`，走真实消费路径
`POST /api/v1/places/{place_id}/effective-rules`（生产库）。

| 查询 | effect | applied_exceptions | missing_inputs |
|---|---|---|---|
| 普通犬 | `prohibited` | 0 | — |
| 导盲犬，**未提供 holder** | `conditional` | 0 | `['holder_scope']` |
| 导盲犬 + `person_with_disability` | `conditional`（例外**已应用**） | 1（`a9f564bb…`） | — |
| generic `service_dog`（未点名角色） | `prohibited` | 0 | — |
| `police_dog` | `prohibited` | 0 | — |
| `military_working_dog` | `prohibited` | 0 | — |

三点值得单独记录：

1. **holder 未知 ⇒ conditional，不是 allowed 也不是 prohibited** —— 与 §7-C 一致，
   且这次发生在 OPERATOR_POLICY 层，证明语义不是 LEGAL 层的特例。
2. **holder 满足时 effect 仍是 `conditional` 而不是 `allowed`** —— 因为这份 but 书自带条件
   （须栓系绳、部分游乐项目可能不允许）。「例外已应用」与「无条件允许」是两件事：
   `applied_exceptions` 里有它就说明应用了，条件仍然成立。消费者**不得**把 conditional 渲染成 allowed。
3. **generic `service_dog` 在此处是 `prohibited` 而不是 `conditional`** —— 与 §7-D 的
   `conditional` 不同，因为这里的基底是「禁止」而非「有条件的法定豁免」：
   例外没有完整覆盖查询（`query ⊄ carve-out`），所以基底的禁止照常生效。
   P0-02 修的是「存在性语义导致整体 allowed」，不是「所有未点名查询都必须 conditional」。
