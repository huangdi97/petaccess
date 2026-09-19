# R2-FINAL-R3-BATCH-02 执行 & 遗留闭环报告

轮次：`R2_FINAL_R3_BATCH_02_EXECUTION_AND_BACKLOG_CLOSURE_R1`
基线：`a3e7dae`（本轮开始时 HEAD）
生产库：`petaccess`（PRODUCTION）· alembic `f2a1c7d9e034` 前后一致
生产写入：**9 行**（6 AccessRule + 3 RuleException）· 授权来源：`huangdi97` 已签登记表 `review_decisions_r2_final.json`

---

## 0. 结论指标

```
# --- 发布 -------------------------------------------------------------------
REAL_PUBLISH_EXECUTED          = YES
BATCH_ID                       = R2-FINAL-R3-BATCH-02
BATCH_SELECTED                 = 9
ACCESS_RULE_CREATED            = 6
RULE_EXCEPTION_CREATED         = 3
FAILED                         = 0
CLI_PUBLISH_AUDIT_CONTRACT     = PASS（checked=9 / missing=0 / exception_audit_without_base=0）
SECOND_EXECUTE_NOOP            = 9
SECOND_EXECUTE_NEW_WRITES      = 0

# --- 指纹 -------------------------------------------------------------------
FINGERPRINT_PRE                = 67f7b19ef3c310ad6b07df749ac76fe4862f82653aa723ed900a4cbc083e853d
FINGERPRINT_POST               = 0712cc3c9709d54c723ba71a2c0e68f098e6be3b658390987eccaeec8eb03b3c
access_rule                    = 20 → 26   (+6 -0 ~0)
rule_exception                 =  6 →  9   (+3 -0 ~0)
rule_condition                 =  0 →  3
audit_log                      = 9668 → 9686 (+18 -0 ~0)
rule_candidate                 = 75 → 75   (+0 -0 ~9，唯一 mutated = 本批 9 条)
duplicate_current_groups       = 0 → 0

# --- 完整性（生产） ---------------------------------------------------------
PRODUCTION_INTEGRITY_SCAN      = PASS
CRITICAL / HIGH                = 0 / 0
MEDIUM                         = 1（AUDIT_TARGET_ID_UNUSABLE 2647 rows，历史项）

# --- 解析器（克隆 vs 生产，180 个 case 投影比对） ---------------------------
RESOLVER_MATRIX_CASES          = 90 × 2 次
REHEARSAL_PREDICTS_PRODUCTION  = PASS（语义投影 diff = 0）
MATRIX_PROBLEMS                = 0（无但书外溢、无未声明 holder 的无条件允许、无 zone 压平）
RULE_COUNT_DISTRIBUTION        = clone 与 prod 完全一致（0:55 / 1:30 / 2:5）

# --- 遗留闭环（两套登记表都实测重跑） ---------------------------------------
R2_FINAL_R3_APPROVED_TOTAL     = 23
R2_FINAL_R3_ALREADY_PUBLISHED  = 17
R2_FINAL_R3_SUPERSEDED         = 2   （新增登记：ALREADY_SATISFIED / BASE_ALREADY_SATISFIED）
R2_FINAL_R3_PUBLISH_BLOCKED    = 4   （真实阻塞：SEMANTIC_REMODEL_REQUIRED）
R2_FINAL_R3_CURRENT_EXECUTABLE = 0   ✅
WAVE01_APPROVED_TOTAL          = 15
WAVE01_CURRENT_EXECUTABLE      = 0   ✅（保持）

# --- Wave-02 ---------------------------------------------------------------
ANIMAL_SCOPE_REMODEL_GATE      = PASS
PILOT_REVIEW_PUBLISH_GATE      = PASS
30_50_PLACE_EXPANSION          = ALLOWED
```

---

## 1. 批次与授权

`docs/governance/publish_batches/R2_FINAL_R3_BATCH_02.json` —— revision `R2-FINAL-R3`、
reviewer `huangdi97`、9 条 `candidate_rule_ids`（按执行依赖顺序，基底在但书之前）。

清单是**三层收窄**的结果，三层都写进了 `note`（顶层键不能加，见陷阱 #103）：

| 层 | 依据 | 剩 |
|---|---|---|
| 单行 canonical gate | `wave01_approved_disposition_audit.py` 重跑全部闸门 | 13 |
| 计划层 | `publish_reviewed_r1 --dry-run`：2 条但书语义不可达 | 11 |
| 批次安全 | **克隆真执行**：1 条会产生重复现行规则 | 9 |

---

## 2. 生产发布前的闸门（dry-run，零写入）

```
BATCH_SELECTED              = 9
BATCH_DEPENDENCY_CLOSED     = PASS
ZERO_INERT_RULES            = PASS
BATCH_VALIDATION            = PASS
PREPUBLISH_PASS             = 9 / PREPUBLISH_BLOCKED = 0
ACCESS_RULE_CREATE_COUNT    = 6
RULE_EXCEPTION_CREATE_COUNT = 3
SELECTED_BUT_BLOCKED        = 0
DRY_RUN_ZERO_DB_MUTATION    = true
```

旁注：计划同时报出两条**未被选中**的不可达但书
（`dl-pet-ban→dl-sd-op`、`qt-indoor-op→qt-sd-op` → `SEMANTIC_REMODEL_REQUIRED`）——
它们不在本批里，但提示了系统仍知道它们的存在。

---

## 3. 发布结果

```
published = 9 · failed = 0 · held = 0 · rejected = 0
  dl-pet-ban         CREATE_ACCESS_RULE      （上海迪士尼乐园 · ordinary_pet · prohibited · OPERATOR_POLICY）
  gh-legal-dog       CREATE_ACCESS_RULE      （港汇恒隆广场 · dog · prohibited · LEGAL）
  mn-legal-dog       CREATE_ACCESS_RULE      （Manner咖啡 凯德虹口 · dog · prohibited · LEGAL）
  qt-indoor-op       CREATE_ACCESS_RULE      （前滩太古里 商场室内空间 · ordinary_pet · prohibited）
  qt-outdoor-op      CREATE_ACCESS_RULE      （前滩太古里 户外开放区域 · ordinary_pet · conditional）
  xm-legal-dog       CREATE_ACCESS_RULE      （星巴克 徐汇西岸梦中心 · dog · prohibited · LEGAL）
  gh-sd-legal        CREATE_RULE_EXCEPTION   （base gh-legal-dog）
  mn-sd-legal        CREATE_RULE_EXCEPTION   （base mn-legal-dog）
  xm-sd-legal        CREATE_RULE_EXCEPTION   （base xm-legal-dog）
```

二次 execute：`NOOP = 9`，`ACCESS_RULE_CREATE = 0`、`RULE_EXCEPTION_CREATE = 0`、`SUPERSEDE = 0`。

---

## 4. 解析器：演练是否真的预测了生产

同一个脚本 `scripts/verify_r3_safe9_matrix.py` 跑两次：一次打克隆（已含本批）、一次打生产（发布后）。
5 个受影响场所 × 6 种查询 ×（place 级 + 各 zone），共 **90 个 case**。

```
语义投影比较（effect / compliance_state / normative_effects / missing_inputs / 规则数 / 生效例外数）
semantic diffs = 0
```

**为什么必须用投影而不是逐字比较**：两次独立写入各自生成 rule UUID，跨库比较身份必然不等。
第一版比较直接比了整行，得出 24 处「差异」——全部只是 UUID 不同，语义完全一致。
**这是我的比较器写错了，不是发布出了问题**；已改为语义投影。

关键格的实测结果（生产）：

| 场所 · zone | ordinary dog | guide_dog（无 holder） | guide_dog（法定 holder） | generic service_dog | police_dog |
|---|---|---|---|---|---|
| 港汇恒隆 · 室内商业空间 | prohibited | conditional + missing | allowed（例外生效） | prohibited | prohibited |
| Manner · 室内 | prohibited | conditional + missing | allowed（例外生效） | prohibited | prohibited |
| 星巴克西岸 · 室内 | prohibited | conditional + missing | allowed（例外生效） | prohibited | prohibited |
| 前滩太古里 · 商场室内空间 | prohibited | conditional + missing | allowed（JPROV-001） | prohibited | prohibited |
| 前滩太古里 · 户外开放区域 | conditional | unknown | unknown | conditional | unknown |
| 任意场所 · **不带 zone** | unknown | unknown | unknown | unknown | unknown |

`MATRIX = PASS`：没有但书外溢到 generic service_dog / police_dog；没有「未声明 holder 却无条件允许」；
zone 规则没有被压平成场所级禁止（place 级一律 unknown）。

---

## 5. 遗留闭环：两套登记表都归零

发布后重跑全部闸门（`wave01_approved_disposition_audit.py`，只读）：

| revision | APPROVED | 已发布 | 被取代/已满足 | 阻塞 | **可执行** |
|---|---|---|---|---|---|
| `R2-FINAL-R3` | 23 | 17 | 2 | 4 | **0** ✅ |
| `EXP-R1-W01-REVIEW-R1` | 15 | 12 | 3 | 0 | **0** ✅ |

### 5.1 新增两条登记（事实性，不改人类决定）

`docs/governance/superseded_semantics.json` 现 5 条。

**`qt-indoor-legal` → `ALREADY_SATISFIED_BY_PRIOR_PUBLICATION`**

前滩太古里 zone `12690b48` 上已有一条 current `(LEGAL, dog, enter, prohibited)`：
`42c9a35e-a5c3-4fd3-ab5c-9c211e1ffda5`，由候选 `d1aee781-…` 发布 ——
该候选正是 **另一个登记表**的 `w01-d1aee78159`（`EXP-R1-W01-REVIEW-R1`）。

即：**同一条规范陈述被两个登记表各批准了一次**，其中一个先发布了。
克隆实测：发布 `qt-indoor-legal` 会产生 `HIGH DUPLICATE_CURRENT_RULE = 2 rows / 1 group`。

**`qt-sd-legal` → `BASE_ALREADY_SATISFIED_NON_EXECUTABLE`** —— 两个独立理由：
1. 它登记的基底就是上面那条不可执行的 `qt-indoor-legal`；
2. 它想给予的效果已由更高的法律层提供：生产实测「导盲犬 + `person_with_disability`」在
   该 zone 由 `JPROV-001`（`applies_to_layer=LEGAL`）给出 `allowed`，
   `applied_exceptions=['JPROV-001']`；不带 holder 时为 `conditional + missing=['holder_scope']`。
   **发布它不提供任何新增的消费者可见结论。**

两条的人类 `APPROVED` 决定**一字未改**，改变的只是执行状态——与既有三条记录同一机制。
拒绝文案现在按理由分流（`ALREADY_SATISFIED*` → 「已由先前的发布实现」，
`SUPERSEDED*` → 「已被更新的 revision 取代」），不再把两种事实说成同一句话。

### 5.2 真实阻塞：4 条（不可由收窄或授权解决）

`dl-sd-op`、`qt-sd-op`、`fp-sd-op-firstparty`、`lib-sd-op-guide`
—— 单独进批实测，计划层全部给出：

```
UNREACHABLE_SELECTED = 4 · BATCH_VALIDATION = FAIL · exit 4
  dl-sd-op:            该例外语义不可达（bases=['dl-pet-ban']）
  qt-sd-op:            该例外语义不可达（bases=['qt-indoor-op']）
  fp-sd-op-firstparty: 该例外语义不可达（bases=['fp-pets-op-firstparty']）
  lib-sd-op-guide:     该例外语义不可达（bases=['lib-pets-op']）
  全部 → SEMANTIC_REMODEL_REQUIRED
```

原因：这些但书的基底是 `OPERATOR_POLICY` 且 scope 够不到但书的主体
（`ordinary_pet` base 管不到 `service_dog` 主体），发布后永不生效 —— 惰性规则。
正确路径是**语义改造 + 新候选 + 新人工审查**；放宽 base scope 或跳过适用性判断都被禁止。

---

## 6. 本轮发现（工具缺陷与根因）

| ID | 内容 | 处置 |
|---|---|---|
| `WAVE02_FINDING_R1` | **发布器的重复检查只比对「本计划内部」的写**，不比对「库中是否已有等价现行规则」。因此跨登记表的同实质候选不会被拦下——`qt-indoor-legal` 就是这类，`BATCH_VALIDATION = PASS` 而实际会造出重复规则。第三层（演练）是当前唯一的发现手段。 | 已登记；根治需在 `plan_integrity` 增加「计划内写入 vs 库中现行规则」的等价性检查 |
| `WAVE02_FINDING_R2` | `wave01_approved_disposition_audit.py` 对 4 条阻塞行的理由串写成「base 不可发布（NOOP_ALREADY_EXISTS）」——那是**第二次 execute 的 NOOP 态**，不是真实原因（真实原因是 `UNREACHABLE`）。分桶结果正确，理由串误导。 | 已记录；权威理由以计划层探针为准（本报告 §5.2） |

---

## 7. Wave-02

```
ANIMAL_SCOPE_REMODEL_GATE = PASS
PILOT_REVIEW_PUBLISH_GATE = PASS
30_50_PLACE_EXPANSION     = ALLOWED
```

两 Gate 同时 PASS，Wave-02 在治理上解锁。当前覆盖情况：

```
place = 20，其中有现行规则的 = 16（本批新增覆盖：Manner咖啡、星巴克西岸梦中心）
rule_candidate = 75，已发布 26
「已批准且当前可执行但未处理」= 0（两套登记表均归零）
```

**场所采集（30–50 的下一波）尚未启动**，这是本轮唯一的剩余工作项；
它需要为每个新场所采集真实可核验来源（Wave01 的硬约束），且必然以
`BLOCKED_HUMAN`（人工审查）收尾，不是机器能单方面完成的。

---

## 8. 质量基线

发布后有 **2 个测试失败**，且都是**断言把发布前的状态写死了**——属于必须更新的陈旧断言，不是回归：

| 测试 | 原断言 | 现在的事实 | 更新后 |
|---|---|---|---|
| `test_publish_plan.py::…plans_twelve_rules_and_eleven_carve_outs` | 计划 12 规则 + 11 但书 = 23 | `qt-indoor-legal` / `qt-sd-legal` 被作废登记后，23 条 APPROVED 里只剩 21 条可写 | 改名 `…plans_eleven_rules_and_ten_carve_outs`，**新增**断言 `retired == {qt-indoor-legal, qt-sd-legal}` 与 11/10 分项，避免数字日后悄悄漂回 23 |
| `test_superseded_semantics_and_evidence_acceptance.py::…names_the_three_rows_it_retired` | 登记表恰好 3 条 | 现为 5 条 | 改名 `…names_every_row_it_retired`，**新增**逐条断言 `reason` / `superseded_by` / `measured_evidence` 均非空、`human_decision == APPROVED` 未被改写，并按理由把两类作废分辨开 |

两处都是**收紧**而不是放宽：更新后仍固定「23 条 APPROVED 减去 2 条作废 = 21 条可写」这一不变量。

**顺带解决**：`WAVE01_FINAL_CLOSURE_FINDING_R1` 登记的 3 项既有 E501
（`tests/unit/test_superseded_semantics_and_evidence_acceptance.py`）已随之消失——
本轮为新增登记条目必须编辑该文件，编辑时跑了 `ruff format`，把 3 处超长行折了行。
`git diff` 该文件只有「折行」+「本节所列断言改动」两类变更，无逻辑改写。
因此 `ruff check .` 现在**全仓 All checks passed**。

```
PYTEST     = 825 passed / 2 skipped
RUFF       = 全仓 All checks passed（含此前 3 项既存 E501，已随折行消失）
MYPY       = Success（87 files）
守卫复验   = 3 个旧 manifest + 反事实重列 → exit 4（4/4），未被本轮改动破坏
端口收尾   = 8010/8011/8012 无残留
```

---

## 9. 产物

- 清单：`docs/governance/publish_batches/R2_FINAL_R3_BATCH_02.json`
- 登记：`docs/governance/superseded_semantics.json`（5 条）
- 脚本：`scripts/verify_r3_safe9_matrix.py`
- 证据（`artifacts/wave02/`）：`r3_batch02_{pre,post}.json` · `r3_batch02_dryrun.out` ·
  `r3_batch02_execute{,_2nd}.txt` · `r3_batch02_snapshot{,_2nd}.json` · `r3_batch02_integrity.json` ·
  `safe9_matrix_{clone,prod}.json` · `probe_carveouts.out` · `probe_qt_pair.out` ·
  `final_r3_disposition.json` · `final_w01_disposition.json`
