# WAVE01 真实发布前语义桥接报告

`WAVE01_PRE_REAL_PUBLISH_SEMANTIC_BRIDGE_R1` · 2026-09-18

---

## 0. 一句话结论

人类签署未被触碰（15/14/2 不变），但**真实可执行集合从规划的 13 条降到 5 条**。差额不是新的审查判断，而是三处「审阅时的信念」被运行时测量推翻：两个作用域归一化其实不成立、一个 carve-out 其实永不生效、六条 LEGAL 禁犬规则缺少可执行法定导盲犬例外路径。

---

## 1. 审阅时的信念 vs 运行时证明（§21）

保留历史材料，不改写当时的 Review Packet。当时的判断在当时的证据下是合理的；改变的是可用事实。

| # | 审阅时的信念 | 运行时的实际 | 影响 |
|---|---|---|---|
| 1 | 迪士尼 #19 的 `guide_dog` carve-out 相对其基底**可达**（Review Packet 如此记载） | `rule_governs({guide_dog}, 'other','other','exact') = False`。`other` 只覆盖 `{other_pet}`。该 carve-out **永不生效** | Review Packet 前提错误，已在工程侧记录 |
| 2 | 上海动物园 #6 把来源「动物」归一为 `other` 并标 `exact`，视为忠实 | 「动物」是全域；`other` 是 `{other_pet}`。这是**收窄**被标成等价 | 作用域语义不兼容 |
| 3 | 迪士尼 #18 把来源「动物（导盲犬除外）」归一为 `other` 并标 `exact` | 同上，且**内嵌但书未建模**为 RuleException | 双重缺陷 |
| 4 | 10 条 LEGAL 犬类禁入规则可随基底一并发布 | 平台**没有 jurisdiction 级法定例外机制**；但书以 place 级 `rule_exception` 绑定到具体 rule_id。未显式绑定该 rule_id 的基底，其导盲犬查询解析为 `prohibited` | 6 条基地缺可执行安全路径 |
| 5 | 世纪公园可通过规范预发布闸门 | 通过闸门，但发布器 ADR-021 原子前置拒绝（`search_snippet` + `needs_verification=True`） | 执行层拒绝 |

**没有任何一条推翻人类决定。** 15 条 APPROVED 全部保持 APPROVED。

---

## 2. 人类决定不可变（§1）

```
SIGNED_REVISION = EXP-R1-W01-REVIEW-R1
HUMAN_REVIEWER  = huangdi97
APPROVED = 15 ; HOLD = 14 ; REJECTED = 2 ; APPROVED_WITH_NOTE = 0
```

签署登记表 `docs/expansion/review_decisions_expansion_r1_wave01.json` **本轮零字节改动**。桥接脚本只读该文件；回归测试 `test_bridge_never_writes_a_human_field` 结构性锁死「不得写 `final_decision` / `decided_at`」。

`APPROVED` 是历史事实；`PUBLISHABLE` 是技术判定。二者可以不一致，且不得相互覆盖。

---

## 3. 本轮新增的三道发布安全门

### 3.1 来源作用域语义等价（§4–§6）

模块：`services/api/app/rulespec/source_scope_semantics.py`

`exact` 是**等价声明**。ADR-025 下只有 `exact` / `compound_term_split` 能让存储作用域顶替来源的法律含义。因此把「动物」存成 `other` 并标 `exact`，是在声称两者指同一集合 —— 而它们不是。

实现方式与 `COMPOUND_TERM_SPLIT_MEANINGS` 一致：把术语读法**显式声明**在 `SOURCE_TERM_READINGS`，可复核、可测试，不藏在审查表格里。未声明的术语 fail closed（`SEMANTIC_REMODEL_REQUIRED`）——因为「无法证明等价」不是「等价」的证据。

一个重要取舍：第一版实现把 fail-closed 做成了默认，结果连 `犬只→dog`、`导盲犬→guide_dog` 这类真等价也被拒，会拦掉全部 15 条。**过宽的闸门与过窄的闸门同样是错的**，因此改为「声明词表 + 未声明即拒」。

### 3.2 可执行法定导盲犬安全路径（§10–§12）

模块：`services/api/app/rulespec/guide_dog_safety.py`

不读文档、不做法律推理，而是构造真实的 `LayeredRule`/`LayeredException` 并调用规范 `v05_resolver.resolve` 两次：

- 普通犬 → 必须 `prohibited`（基底仍生效）
- 导盲犬 → 必须**不**为 `prohibited`（但书生效）

解析器会拒绝的例外，这里也会失败 —— 因为没有第二套作用域算法、没有第二套例外机制。

**本轮最重要的架构发现**：`《上海市养犬管理条例》第二十三条` 的但书「盲人携带导盲犬的，不受本条规定的限制」在平台中被建模为 **3 条 place 级 `rule_exception`**，分别绑定到和平饭店、上海图书馆东馆、星巴克烘焙工坊三个具体 `rule_id`。平台**没有** jurisdiction 级例外机制。实测：

```
新建一个无绑定例外的 LEGAL 犬类禁入基底，
查询导盲犬 → effect = prohibited，applied_exceptions = []
```

即：**任何新的 LEGAL 犬类禁入规则，在没有显式绑定该 rule_id 的 carve-out 时，都会向导盲犬使用者返回「禁止」** —— 而这与它自己援引的法条相矛盾。这不是本轮引入的缺陷，是本轮才测量到的既有架构缺口。

按 §12，本轮**不自动生成**例外。缺失者输出 `GuideDogExceptionProposal`，人类字段（`final_decision`/`reviewer`/`decided_at`）全部留空，留待后续人工复核。

### 3.3 条件键 ingest 边界修复（§7–§8）

模块：`services/api/app/services/condition_ingest.py`

31 条 Wave01 候选中 10 条把条件写在 `type` 键下，规范闸门要求 `condition_type`。

原实现在 `candidate_service.publish` 里写 `cond.get("condition_type") or cond.get("type")` —— 这是把「旧输入格式的翻译」永久放进领域层，两个规范键从此长期共存，下一个忘记兼容的消费者会把「必须牵绳」静默读成无条件。`answerability.py` 也有同样的一处。

正确做法（§8）：**翻译只在数据入口发生一次**。`normalize_conditions()` 现在挂在 `create_from_extraction`（所有 API 导入的必经点），领域层与发布器只认 `condition_type`。歧义输入（两键并存且不一致）**拒绝导入而非猜测**；未知条件类型同样拒绝，避免拼写错误变成永不生效的规则。

已签候选**不原地修改**（§9）。若 #19 未来需要按修正后的 schema 重建，须新建候选 + 新审查 revision + 新人工审查。

---

## 4. 分层计数（§14）

`PREPUBLISH_PASS` 一个数字会掩盖执行层的额外拒绝，因此拆成四层：

```
HUMAN_APPROVED           = 15
PREPUBLISH_POLICY_PASS   =  7
EXECUTION_CONTRACT_PASS  = 14
FINAL_EXECUTABLE         =  5   （AccessRule 3 + RuleException 2）
EXCLUDED_APPROVED        = 10
```

各层含义：

- **HUMAN_APPROVED** — 人类签署的批准数
- **PREPUBLISH_POLICY_PASS** — 通过作用域语义 + 导盲犬安全门者
- **EXECUTION_CONTRACT_PASS** — 未被发布器 ADR-021 原子前置拒绝者
- **FINAL_EXECUTABLE** — 三者皆过，且 carve-out 依赖闭包完整者

---

## 5. 安全批次（§15–§17）

新清单 `docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_01A.json`（**不覆盖**已审计的 `BATCH_01`）。

```
supersedes_planning_manifest = EXP_R1_W01_REVIEW_R1_BATCH_01.json
supersede_reason             = PRE_REAL_PUBLISH_SEMANTIC_BRIDGE
size = 5
```

执行顺序（位置即顺序，基底先于例外）：

| # | rule_id | 场所 | 层 | 类型 |
|---|---|---|---|---|
| 1 | `w01-1fb3d7f1c7` | 兴业太古汇 | LEGAL | CREATE_ACCESS_RULE |
| 2 | `w01-4710a68f56` | 上海博物馆东馆 | OPERATOR_POLICY | CREATE_ACCESS_RULE |
| 3 | `w01-fa5f33f122` | 上海博物馆东馆 | LEGAL | CREATE_ACCESS_RULE |
| 4 | `w01-6482477d8d` | 兴业太古汇 | LEGAL | CREATE_RULE_EXCEPTION（dep=#1） |
| 5 | `w01-73de8e3357` | 上海博物馆东馆 | LEGAL | CREATE_RULE_EXCEPTION（dep=#3） |

依赖闭包校验：`BATCH_DEPENDENCY_CLOSED = PASS`。

### 被排除的 10 条及原因（全部保持 APPROVED）

| reason | 条数 | rule_id |
|---|---|---|
| `REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE` | 6 | `w01-052d19ccba`(CHARLIE'S)、`w01-7de2f5d75b`(omitofee)、`w01-df1645fe68`(朗廷)、`w01-8ba2b49b01`(苏河湾)、`w01-d1aee78159`(前滩太古里)、`w01-e951785d1b`(港汇恒隆) |
| `SOURCE_SCOPE_NORMALIZATION_NOT_SEMANTICALLY_EQUIVALENT` | 2 | `w01-6f2bfd39d7`(上海动物园)、`w01-3a04d4d1aa`(迪士尼基底) |
| `INREACHABLE_APPROVED_CARVE_OUT` | 1 | `w01-305fa08c1e`(迪士尼导盲犬 carve-out) |
| `ADR021_UNVERIFIED_SEARCH_SNIPPET` | 1 | `w01-4e217d5810`(世纪公园) |

**注意 #19 的双重失效**：迪士尼 carve-out 既因缺少可执行基底而不可达（`other` 不 govern `guide_dog`），也是 §3 明确要求排除的对象。其唯一候选基底 #18 已因作用域不兼容被排除，因此它在本批中是**没有基底的 carve-out**。

---

## 6. 零变更证明（§19）

```
dry-run 前指纹 = 584c97ba084744665ab0da2dcf9164f5cfcca0d3fb996cc42c3540450b345308
dry-run 后指纹 = 584c97ba084744665ab0da2dcf9164f5cfcca0d3fb996cc42c3540450b345308
SEMANTIC_DIFF = 0 ; ROW_DIFF = 0
access_rule = 5（未变）; rule_exception = 3（未变）
candidate publish state = 未变
```

dry-run 与 execute 走**同一条** pipeline（同一 `evaluate_for_publish`），dry-run 仅跳过写入。

---

## 7. 测试与质量

```
pytest          695 passed / 2 skipped   （本轮前 643）
ruff check      All checks passed
ruff format     219 files already formatted
新增回归锁       26 项（tests/unit/test_wave01_semantic_bridge.py）
```

§20 要求的九类针对性测试全部落地：

1. `other` 不 govern `guide_dog`（ADR-025）
2. 宽泛「动物」不得静默 exact 归一到 `other`；同时锁死**真等价仍必须通过**
3. 不可达 carve-out 不可执行（含可达对照，证明是区分而非缺陷）
4. 已签候选字段不可变（结构性锁）
5. 旧 `type` 仅在 ingest 边界归一
6. 领域层不得同时接受两个规范键
7. LEGAL 禁犬需可执行法定例外（含「别家规则的例外不算路径」「无出处例外不算路径」）
8. `search_snippet` + `needs_verification` 不可执行
9. planning PASS 与 execution PASS 不可混同；安全清单不得大于原清单

---

## 8. 遗留与后续

| 项 | 状态 | 说明 |
|---|---|---|
| 6 条 LEGAL 禁犬基底 | BLOCKED | 缺可执行法定导盲犬例外；需为每个场所新建 carve-out 候选并人工审查 |
| 2 条作用域不兼容基底 | SEMANTIC_REMODEL_REQUIRED | 「动物」需要能表达全域的作用域，或改标非等价归一化；须新建候选（已签字段不可改） |
| jurisdiction 级法定例外机制 | **OPEN（架构缺口）** | 平台无法表达「法条本身的但书自动适用于所有援引该法条的规则」 |
| 10 条条件的 `type` 键 | 已修复（ingest 边界） | 已签候选保持原字节 |
| 世纪公园 | BLOCKED | 需一手来源重新采集，而非重新审查 |
| `PLACE_GEO_PENDING` | OPEN | 阻断 Phase F |
| `SEMANTIC_REMODEL_ISSUE` | OPEN | 现在明确包含迪士尼 `other` 基底 carve-out |

---

## 9. 本轮边界

未执行：`--execute`、真实 Publish、Phase B、Wave02、Real Map、Public Beta Release。

未做：修改任何 `final_decision`/`reviewer`/`decided_at`；重新签署；重写历史 Review Packet；为扩大批次而放宽任何闸门；自动生成并批准缺失的导盲犬例外。
