# FIRST_REAL_PUBLISH_BATCH_01B_FINAL_CLOSURE

- `SIGNED_REVISION = R2-FINAL-R3`
- `HUMAN_REVIEWER = huangdi97`
- `BATCH_ID = R2-FINAL-R3-BATCH-01B`
- 清单：`docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json`
- 生成日期：2026-09-17

## 0. 结论

| 项 | 值 |
| --- | --- |
| `FIRST_REAL_PUBLISH_BATCH_01B_GATE` | **PASS** |
| `REAL_PUBLISH_EXECUTED` | **NO**（仅生成命令，未执行） |
| 批次数 | **8**（5 AccessRule + 3 RuleException） |
| 发布前预检 | **8 / 8 / 0**（evaluated / pass / blocked） |
| `CARVE_OUT_REACHABILITY` | **PASS** |
| `ZERO_INERT_RULES` | **PASS** |
| `UNREACHABLE_SELECTED` | **0** |
| 幂等复跑 | `NOOP_COUNT = 8`，新增写入 0 |
| 全量回归 | 606 passed / ruff / mypy / eslint / prettier / H5 / Admin / E2E / 视觉 / a11y 全绿 |

本轮**不接受** `PASS_WITH_LIMITATIONS`：`CARVE_OUT_REACHABILITY` 与 `ZERO_INERT_RULES`
只在恰好 `PASS` 时放行（见 §3）。

---

## 1. 本轮的决策

上一轮（BATCH-01A）以「最终用户答案目前正确」为由，接受了
`CARVE_OUT_REACHABILITY = PASS_WITH_LIMITATIONS`（2 条不可达 carve-out）。
**该理由被明确否决**：

> 不接受"最终用户答案目前正确"作为发布不可达 `RuleException` 的理由。

理由本身站不住：费尔蒙 / 上图的正确答案来自**独立的 LEGAL 层**
（`dog` base + `guide_dog` exception），不是来自那条运营层 carve-out。
**答案正确 ≠ carve-out 生效。** 一条发布后永不生效的规则会被发布、链接、审计、计数，
却提供不了任何效力——比不发布更糟。

因此本轮：

1. 收窄到 **8 条**；
2. 把闸门从"无批准例外不得发布禁令"升级为"无**可达**批准例外不得发布禁令"；
3. 新增一等闸门 **ZERO INERT RULES**：批次内不得含不可达 carve-out。

---

## 2. 批次 01B 成员（8 条，位置即执行顺序）

| # | rule_id | 类型 | 层 | scope | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | `fp-legal-dog` | AccessRule | LEGAL | `dog` | 费尔蒙 法定犬只禁令 base |
| 2 | `fp-pets-op-firstparty` | AccessRule | OPERATOR_POLICY | `ordinary_pet` | 费尔蒙 运营宠物禁令 base |
| 3 | `fp-sd-legal` | RuleException | LEGAL | `guide_dog` | ← `fp-legal-dog`，**可达** |
| 4 | `lib-legal-dog` | AccessRule | LEGAL | `dog` | 上图 法定 base |
| 5 | `lib-pets-op` | AccessRule | OPERATOR_POLICY | `ordinary_pet` | 上图 运营 base |
| 6 | `lib-sd-legal` | RuleException | LEGAL | `guide_dog` | ← `lib-legal-dog`，**可达** |
| 7 | `sb-legal-dog` | AccessRule | LEGAL | `dog` | 星巴克 法定 base |
| 8 | `sb-sd-legal` | RuleException | LEGAL | `guide_dog` | ← `sb-legal-dog`，**可达** |

### 延期的 4 条：`DEFERRED_APPROVED_SEMANTIC_REMODEL`

| rule_id | 角色 | 为什么延期 |
| --- | --- | --- |
| `dl-pet-ban` | base (OPERATOR, `ordinary_pet`) | 其唯一 carve-out 不可达；迪士尼无 LEGAL 层兜底 ⇒ 会得到错误用户状态 `UNKNOWN` |
| `dl-sd-op` | carve-out (`guide_dog`) | 不可达：`ordinary_pet` 不覆盖 `guide_dog` |
| `fp-sd-op-firstparty` | carve-out (`guide_dog`) | 同上 |
| `lib-sd-op-guide` | carve-out (`guide_dog`) | 同上 |

**延期 ≠ HOLD ≠ REJECTED。** 四条在签署登记表中的 `final_decision` **保持 `APPROVED` 原样**：
不重新签署、不重写 Evidence、不改 `RuleException` binding。已由测试
`test_the_deferred_rules_are_named_and_still_approved` 锁定。

清单新增 `deferred` 字段承载这一事实（`OPTIONAL_KEYS` 已扩展）。

---

## 3. 闸门升级（§4 + §5）

### 3.1 升级后的第 4 条拒绝

```
旧：No prohibition without its approved carve-out.
新：No prohibition without its REACHABLE approved carve-out.
```

可达性由 `scripts/publish_batch.py::carve_out_reachability` **实测**，
它 **复用 ADR-025 的权威匹配器** `app.rulespec.animal_scope.rule_governs`
（`_canonical_rule_governs()` 延迟导入，兼容按文件路径加载），
**不复制第二套作用域算法**——复制品会在本体第一次变动时漂移，
然后"可达"就变成一个没人维护的副本所做的断言。

三态判定，不允许折叠：

| (base, carve-out) 状态 | 对 base 的作用 |
| --- | --- |
| `reachable` | 义务成立：carve-out 必须同批或已发布 |
| `unreachable` | 记为 `UNREACHABLE_APPROVED_CARVE_OUT` → `SEMANTIC_REMODEL_REQUIRED`，**不阻断 base** |
| `unevaluable`（scope 数据缺失） | 义务仍成立：「无法证明其惰性」不是放行理由 |

`is_reachable_carveout()` 返回 `bool | None`——`None` 故意不等于 `True`。

### 3.2 新增第 5 条拒绝：ZERO INERT RULES

批次**内**不得含 `unreachable` / `unevaluable` 的 carve-out。
语义不可达的 carve-out **不得被规划为 `CREATE_RULE_EXCEPTION`**。

### 3.3 新闸门 `ZERO_INERT_RULES`（verify_publish_r3.py）

与 `CARVE_OUT_REACHABILITY` 一起成为一等闸门，两者**都要求恰好 `PASS`**：

```python
strict = ("CARVE_OUT_REACHABILITY", "ZERO_INERT_RULES")
ok = all(v in ("PASS", "PASS_WITH_LIMITATIONS") for v in checks.values()) and all(
    checks[name] == "PASS" for name in strict
)
```

不可达 carve-out 现为 **`FAIL`**（不再是 `PASS_WITH_LIMITATIONS`）；
`unevaluable` 单列为 `PASS_WITH_LIMITATIONS`（测量缺口，不是已测缺陷），
同样不算通过。

### 3.4 闸门确实咬人：01 与 01A 现在被拒绝

| 批次 | 条数 | 惰性 carve-out | 结果 |
| --- | --- | --- | --- |
| `R2-FINAL-R3-BATCH-01` | 12 | 3（`dl-sd-op` / `fp-sd-op-firstparty` / `lib-sd-op-guide`） | **REFUSED** |
| `R2-FINAL-R3-BATCH-01A` | 10 | 2（`fp-sd-op-firstparty` / `lib-sd-op-guide`） | **REFUSED** |
| `R2-FINAL-R3-BATCH-01B` | 8 | 0 | **PASS** |

两个历史清单作为演练历史**保留不删、不覆盖**，
并由 `test_batch_01_and_01a_are_refused_by_the_zero_inert_gate` 锁定——
防止闸门日后变软。

---

## 4. 测试证据（新增 12 条，全量 606 passed）

### 语义独立性（必须有测试证明，不能靠推断）

`tests/unit/test_animal_scope.py` §12，4 条：

| 测试 | 断言 |
| --- | --- |
| `test_12_ordinary_pet_base_never_governs_a_guide_dog` | `ordinary_pet` base 对 guide_dog 查询 → `unknown`，**不是** `prohibited` |
| `test_12b_a_guide_dog_carve_out_of_an_ordinary_pet_base_is_inert` | 挂上 carve-out 后仍 `unknown`，`applied_exceptions == []`，`suppressed_rules == []` |
| `test_12c_the_same_carve_out_fires_when_its_base_actually_governs` | 对照：base 换成 `dog` → `allowed`，`applied_exceptions == ["exc-guide-op"]`（证明判定不是"一律不可达"） |
| `test_12d_the_ordinary_pet_base_still_governs_ordinary_pets` | 独立不等于失效：对 `ordinary_dog` 仍 `prohibited` |

### 闸门行为（`tests/unit/test_publish_batch_selection.py`，8 条新增/改写）

- `test_the_shipped_batch_is_eight_with_a_closed_dependency` — 8 / 5 / 3，依赖闭包 PASS，`zero_inert_rules`
- `test_the_deferred_rules_are_named_and_still_approved` — 4 条延期仍为 `APPROVED`
- `test_the_shipped_batch_records_its_two_unreachable_carve_outs` — 2 条 `SEMANTIC_REMODEL_REQUIRED` 被记录
- `test_batch_01_and_01a_are_refused_by_the_zero_inert_gate` — 3 / 2 条惰性 ⇒ 拒绝
- `test_an_unreachable_approved_carve_out_does_not_block_its_base` — 不阻断 base
- `test_an_unreachable_carve_out_may_not_be_selected` — 但不得进批
- `test_reachability_reuses_the_canonical_adr025_matcher` — dog→可达 / ordinary_pet→不可达
- `test_a_carve_out_without_scope_data_is_unevaluable_and_blocks` — 无法判定 ⇒ 阻断

---

## 5. 发布前重评（当前时间，非复用旧结果）

`artifacts/batch01b/prepublish_batch01b.json`：

```
PREPUBLISH_APPROVED_EVALUATED = 8
PREPUBLISH_PASS               = 8
PREPUBLISH_BLOCKED            = 0
gate_status_counts            = {"PASS": 8}
access_rule_create_count      = 5
rule_exception_create_count   = 3
noop_count / blocked_count    = 0 / 0
publication_types             = {"CREATE_ACCESS_RULE": 5, "CREATE_RULE_EXCEPTION": 3}
DRY_RUN_ZERO_DB_MUTATION      = true
```

批次校验输出：

```
BATCH_ID                    = R2-FINAL-R3-BATCH-01B
BATCH_SELECTED              = 8
BATCH_ACCESS_RULE           = 5
BATCH_RULE_EXCEPTION        = 3
BATCH_DEPENDENCY_CLOSED     = PASS
HOLD_SELECTED               = 0
REJECTED_SELECTED           = 0
CROSS_LAYER_EXCEPTION       = 0
BASE_WITHOUT_APPROVED_EXCEPTION = 0
UNREACHABLE_SELECTED        = 0
ZERO_INERT_RULES               = PASS
BATCH_EXECUTION_ORDER = fp-legal-dog -> fp-pets-op-firstparty -> fp-sd-legal<-fp-legal-dog
  -> lib-legal-dog -> lib-pets-op -> lib-sd-legal<-lib-legal-dog
  -> sb-legal-dog -> sb-sd-legal<-sb-legal-dog
  UNREACHABLE_APPROVED_CARVE_OUT = fp-pets-op-firstparty->fp-sd-op-firstparty -> SEMANTIC_REMODEL_REQUIRED
  UNREACHABLE_APPROVED_CARVE_OUT = lib-pets-op->lib-sd-op-guide -> SEMANTIC_REMODEL_REQUIRED
BATCH_VALIDATION = PASS
```

---

## 6. 演练（全新克隆库，非复用）

`bash scripts/rehearsal_r3_runbook.sh phase0`（`ART=artifacts/batch01b`）→
`CREATE DATABASE ... TEMPLATE` 物理克隆 `petaccess` → `petaccess_publish_rehearsal_r3`：

```
alembic_version = b8d2f4a1c556
place 1189 / zone 30 / access_rule 1057 / rule_exception 122
rule_candidate 432 / evidence_bundle 703 / source 1380 / audit_log 8825
```

`phase1`（`MANIFEST=...01B.json MAX_APPROVE=8`）：

```
-- 1/3 execute --
PREPUBLISH_PASS = 8   PREPUBLISH_BLOCKED = 0
ACCESS_RULE_CREATE_COUNT = 5   RULE_EXCEPTION_CREATE_COUNT = 3
NOOP_COUNT = 0   BLOCKED_COUNT = 0
ACCESS_RULE_SUPERSEDE_COUNT = 0
integrity: SELF_SUPERSEDE 0 / DUPLICATE_PLAN 0 / CROSS_LAYER 0 / SUPERSESSION_CYCLE 0

-- 2/3 idempotency --
ACCESS_RULE_CREATE_COUNT = 0   RULE_EXCEPTION_CREATE_COUNT = 0
NOOP_COUNT = 8   SELF_SUPERSEDE 0   DUPLICATE_PLAN 0

-- 3/3 verification drills --
SOURCE_LINKAGE         = PASS      RESOLVER_POST_PUBLISH = PASS
EVIDENCE_LINKAGE       = PASS      EFFECTIVE_RULES_API   = PASS
AUDIT_LINKAGE          = PASS      ENGINE_CONSISTENCY    = PASS
CARVE_OUT_REACHABILITY = PASS      ZERO_INERT_RULES      = PASS
ROLLBACK_DRILL         = PASS      SUPERSESSION_DRILL    = PASS
WATCH_DRILL            = PASS
[carve_out] 已发布 carve-out 3 条，可达 3 条，
            UNREACHABLE_SELECTED = 0，UNEVALUABLE_SELECTED = 0
```

### 三条已发布 carve-out 实测（`rule_governs`）

| carve-out | base | base scope | carve-out scope | base 覆盖该 subject | 附加例外数 |
| --- | --- | --- | --- | --- | --- |
| `fp-sd-legal` | `fp-legal-dog` | `dog` | `guide_dog` | ✅ True | 1 |
| `lib-sd-legal` | `lib-legal-dog` | `dog` | `guide_dog` | ✅ True | 1 |
| `sb-sd-legal` | `sb-legal-dog` | `dog` | `guide_dog` | ✅ True | 1 |

### 延期的 4 条确认未发布

```
dl-pet-ban           published_rule_id = None   review_status = REVIEW_PENDING
dl-sd-op             published_rule_id = None   review_status = REVIEW_PENDING
fp-sd-op-firstparty  published_rule_id = None   review_status = REVIEW_PENDING
lib-sd-op-guide      published_rule_id = None   review_status = REVIEW_PENDING
```

8 条批次成员全部 `PUBLISHED` 且 `published_rule_id` 非空。
（`access_rule` 1057→1063、`rule_candidate` 432→433 的增量来自 rollback /
supersession drill 的故意写入，而非发布器：`ACCESS_RULE_SUPERSEDE_COUNT = 0`。）

---

## 7. 全量回归（本轮实跑，未引用旧数字）

| 门禁 | 结果 |
| --- | --- |
| `pytest -q`（全量，含集成；celery worker 已启动） | **606 passed** |
| `ruff check services/api services/worker tests scripts` | All checks passed |
| `ruff format --check`（同上范围） | 178 files already formatted |
| `mypy .`（`services/api`） | Success: no issues found in 77 source files |
| `pnpm lint:fe`（eslint） | clean |
| `pnpm format:check:fe`（prettier） | All matched files use Prettier code style |
| H5 build（E2E，`VITE_API_BASE` 指向 8010） | ✓ built |
| H5 build（视觉，`env -u VITE_API_BASE`） | ✓ built |
| `pnpm admin:build` | ✓ built |
| `pnpm exec playwright test` | **18 passed** |
| `pnpm exec playwright test --config playwright.visual.config.ts` | **47 passed** |
| `node scripts/a11y_audit.mjs` | **TOTAL issues: 0**（serious=0 moderate=0 minor=0），键盘走查 `invisibleFocus=0` |
| Publisher ×3（dry-run / execute / 幂等复跑） | 8/8/0 · 5+3 写入 · NOOP=8 |

全过程 `apps/` 下**零改动**（仅 `scripts/`、`tests/`、`docs/`），
所以前端三项门禁的结果变化只可能来自渲染环境，而不是代码。

---

## 8. 语义改造（本轮**不决定** OPTION）

`docs/governance/OPERATOR_PET_GUIDE_DOG_SEMANTIC_REMODEL.md`（新建）收录完整缺陷族：
6 条受影响规则（4 已批准 + 2 HOLD：
`lib-sd-op-police` / `lib-sd-op-military`），3 个场所，3 个后续模型，
以及"明确禁止的三条捷径"和关闭条件。

`DISNEY_SCOPE_EXCEPTION_SEMANTIC_ISSUE.md` 保留为迪士尼实例，并已加上指向家族文档的指针。

本轮**不决定** OPTION 1 / 2 / 3。

---

## 9. 真实发布命令（**已生成，未执行**）

`REAL_PUBLISH_EXECUTED = NO`。以下命令需要在人类明确授权后、在**正式库**上执行，
本轮不执行。

前置：

```bash
# 1) 停止一切占用 8010 的服务（克隆需要独占源库）
# 2) 全新克隆演练库
python scripts/rehearsal_db.py --db-name petaccess_publish_rehearsal_r3 \
  --source petaccess --clone --force-terminate --confirm --json

# 3) API 指向演练库
python scripts/dev_api_server.py --db-name petaccess_publish_rehearsal_r3 --port 8010

# 4) 演练：执行 + 幂等 + 验收（应先全绿，再考虑正式库）
ART=artifacts/batch01b \
MANIFEST=docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
MAX_APPROVE=8 \
  bash scripts/rehearsal_r3_runbook.sh phase1
```

正式库发布（**需人类明确授权**）：

```bash
TOKEN="<admin JWT>"

python scripts/publish_reviewed_r1.py \
  --execute \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
  --max-approve 8 \
  --database-name petaccess \
  --registry docs/reality_audit/review_decisions_r2_final.json \
  --reviewer huangdi97 \
  --token "$TOKEN" \
  --snapshot-out artifacts/batch01b/real_publish_receipt.json

python scripts/verify_publish_r3.py \
  --db-name petaccess \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01B.json \
  --out artifacts/batch01b/real_publish_verification.json
```

四个条件缺一不可：`--execute` + `--batch-file`（裸 `--execute` 一律拒绝）、
`--max-approve 8`（第二层上限，必须 ≥ 清单大小）、
`--reviewer huangdi97`（与登记表署名不一致即拒绝）、`--registry`（不按文件名猜登记表）。

---

## 10. 已知未决

1. 运营层 `ordinary_pet` + `guide_dog` 的建模形状（OPTION 1/2/3）——**本轮不决定**。
2. 两条引擎路径对迪士尼的分歧（resolver `UNKNOWN` vs `/rules/evaluate` `MATCH`）——
   随 OPTION 一并解决，与选哪个方案无关。
3. 真实正式库发布未执行，等人类明确授权。
