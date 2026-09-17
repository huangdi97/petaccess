# FIRST_REAL_PUBLISH_BATCH_PREPARATION_R1 — 结果报告

日期：2026-09-16（UTC 14:00–14:30）
签署基线：`R2-FINAL-R3` / `huangdi97` / 37 条决策（23 APPROVED · 9 HOLD · 5 REJECTED）
本轮结论：**未执行真实 Publish**，发布链路已就绪，两个与消费者可见正确性相关的检查未通过。

---

## 1. 结论概要

```
FIRST_REAL_PUBLISH_READINESS_GATE = PASS_WITH_LIMITATIONS
REAL_PUBLISH_EXECUTED             = NO
30_50_PLACE_ENTERED               = NO
```

判定理由：§0 列出的十项准备工作全部完成；发布写入链路（选择 → 闸门 → 事务 →
AccessRule → RuleVersion → RuleException → Evidence → Source → Audit）在专用
rehearsal 库中完整跑通且幂等、可回滚、可取代；但 §13 的 Resolver 行为验证与
§14 的双引擎一致性验证各有一项未达到要求，**且两者同源**。这两项属于「发布后
消费者看到什么」的正确性问题，不是写入链路问题。

为诚实起见：§26 规定「全部关键检查通过」才算 PASS。RESOLVER_POST_PUBLISH 与
ENGINE_CONSISTENCY 在 §25 明确要求 PASS/FAIL，本轮为 FAIL，因此本轮**不能**判
PASS。选 PASS_WITH_LIMITATIONS 而非 FAIL 的依据是：阻断点不在发布器械本身，
且在最重要的安全方向上（HOLD 的军警犬例外不得让警犬/军犬变为 allowed）实测
通过。

---

## 2. §25 要求的全部字段

### 冻结与签署

| 字段 | 值 | 证据 |
| --- | --- | --- |
| `SIGNED_REVISION` | `R2-FINAL-R3` | `docs/reality_audit/review_decisions_r2_final.json` |
| `HUMAN_REVIEWER` | `huangdi97` | 同上（37 行署名唯一） |
| `HUMAN_SIGNATURE` | PASS | 发布器 preflight：final_decision + reviewer + reviewed_at 齐全 |
| 决策分布 | 23 / 9 / 5 | 未修改，未重新生成 |

签署内容（Evidence / Source / Scope / RuleLayer / MandatoryLevel / RuleException
binding）本轮**未做任何修改**。

### 误创建数据库清理（§2）

```
ACCIDENTAL_DB_CLEANUP = PASS
```

| 校验项 | 结果 |
| --- | --- |
| 库是否真实存在 | 是，OID 80180，18 MB |
| 是否属于 protected DB | 否（不在 `petaccess` / `petaccess_dev` / `petaccess_pilot` / `petaccess_visual` / `postgres` / `template*` 中） |
| 是否有业务引用 | 无。全仓库 `petaccess_dev_only` 只作为 `POSTGRES_PASSWORD` 的值出现，`DATABASE_URL` 指向 `petaccess` |
| 是否有有效数据 | 无。5 place / 15 zone / 21 rule / 0 candidate / 0 evidence_bundle / 0 rule_exception，与 `petaccess_visual` 的种子指纹逐项相同 |
| 当前连接数 | 0 |
| 成因其 | `scripts/visual_db_reset.py --db-name` 收到了密码字符串作为库名 |

用带守卫的 `scripts/db_cleanup_accidental.py` 删除（拒绝受保护名 + 拒绝未知名 +
须 `--confirm-drop`），删除后复核 `pg_database` 已不含该库。
证据：`artifacts/accidental_db_cleanup_r3.json`。

### 批次选择（§3–§8）

```
BATCH_ID                      = R2-FINAL-R3-BATCH-01
BATCH_SELECTED                = 12
BATCH_ACCESS_RULE             = 6
BATCH_RULE_EXCEPTION          = 6
BATCH_DEPENDENCY_CLOSED       = PASS
HOLD_SELECTED                 = 0
REJECTED_SELECTED             = 0
UNAPPROVED_SELECTED           = 0
CROSS_LAYER_EXCEPTION         = 0
BASE_WITHOUT_APPROVED_EXCEPTION = 0
```

清单：`docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json`
（只含 `revision` / `batch_id` / `reviewer` / `candidate_rule_ids`——**不存
final_decision**；授权仍从签署登记表读取）。

执行顺序（清单位置即执行顺序，已校验 base 先于 exception）：

```
dl-pet-ban → dl-sd-op<-dl-pet-ban → fp-legal-dog → fp-sd-legal<-fp-legal-dog
→ fp-pets-op-firstparty → fp-sd-op-firstparty<-fp-pets-op-firstparty
→ lib-legal-dog → lib-sd-legal<-lib-legal-dog → lib-pets-op → lib-sd-op-guide<-lib-pets-op
→ sb-legal-dog → sb-sd-legal<-sb-legal-dog
```

- 另外 11 条已批准候选**未**被自动加入（断言 `23 - 12 = 11`）。
- HOLD / REJECTED 未进入批次（断言 0）。
- `lib-sd-op-police` / `lib-sd-op-military` 是 HOLD，**不构成**「base 不得先发布」
  的约束——这正是 §7 的意图，也因此它们不会让 `lib-pets-op` 被卡住。
- `--execute` 无 `--batch-file` 时一律拒绝（退出码 4）。
- 规范与命令形态：`docs/governance/PUBLISH_BATCHES.md`。

### 当次 Pre-Publish Gate（§9）

在 `petaccess` 上对选中 12 条重新调用真实 `publish_gate.evaluate_for_publish()`：

```
BATCH_PREPUBLISH_EVALUATED = 12
BATCH_PREPUBLISH_PASS      = 12
BATCH_PREPUBLISH_BLOCKED   = 0
PREFLIGHT_PROBLEMS         = []
DRY_RUN_ZERO_DB_MUTATION   = True
```

证据：`artifacts/batch01_prepublish_dryrun.json`。

### Rehearsal 执行（§10–§12）

```
REHEARSAL_EXECUTE              = PASS
REHEARSAL_ACCESS_RULE_CREATED  = 6
REHEARSAL_RULE_EXCEPTION_CREATED = 6
```

- 专用库 `petaccess_publish_rehearsal_r3`（TEMPLATE 物理克隆，含 PostGIS 与
  alembic 版本号 `b8d2f4a1c556`）。`scripts/rehearsal_db.py` 两道守卫：
  **denylist**（拒绝一切正式/试点/视觉库）+ **allowlist 正则**
  （只接受 `petaccess_publish_rehearsal_*`）。
- `access_rule` 975 → 981，`rule_exception` 110 → 116，`audit_log` 8191 → 8215（+24）。
- **顺序断言（§12）**：最后一条 base `recorded_at = 13:55:44.594933` <
  第一条 exception `created_at = 13:55:44.625343` ⇒ `BASE_BEFORE_EXCEPTION = True`。
- 走的正是未来正式 execute 的同一条代码：human signed registry → batch selection
  → prepublish → HTTP transition/publish → AccessRule → RuleException → Evidence
  → Source → Audit。

证据：`artifacts/rehearsal_execute_r3.json`、
`artifacts/rehearsal_order_and_counts.json`、
`artifacts/rehearsal_db_fingerprint.json`。

### 幂等（§17）

```
IDEMPOTENCY = PASS
```

同一 Batch 01 再执行一次：`NOOP_COUNT = 12`，`ACCESS_RULE_CREATE_COUNT = 0`，
`RULE_EXCEPTION_CREATE_COUNT = 0`，`SELF_SUPERSEDE = 0`，退出码 0；
`access_rule / rule_exception / rule_candidate / audit_log` 增量全为 **0**。
无重复 AccessRule、无重复 RuleException、无重复 current 版本。

> 演练过程中发现并修复了一个真实缺陷：发布器把「登记表里已发布的规则」也算作
> 「本计划要写入的规则」，导致一次干净的 NOOP 重跑被判 `SELF_SUPERSEDE = 6`
> 并以错误理由拒绝。已改为只对 `plan.writable` 的候选收集，并为批次选择逻辑
> 新增 15 条测试（`tests/unit/test_publish_batch_selection.py`）。

证据：`artifacts/rehearsal_idempotency.json`、`artifacts/rehearsal_idempotency_run2.txt`。

### 证据与来源链路（§15）

```
SOURCE_LINKAGE   = PASS
EVIDENCE_LINKAGE = PASS
```

12/12 均可回溯：candidate → published_rule_id → access_rule / rule_exception
→ source（issuer + url + availability）→ evidence_bundle（content_hash）
→ source_artifact（type + url + content_hash）。无孤儿已发布规则。

### 审计（§16）

```
AUDIT_LINKAGE = PASS
```

| 指标 | 值 |
| --- | --- |
| `candidate.transition` | 24（12 为入库期 `MATCH_PENDING→REVIEW_PENDING`，12 为本轮 `REVIEW_PENDING→APPROVED`） |
| `candidate.publish` | 6 |
| `candidate.publish_exception`（含 base 依赖） | 6 |
| before→after 状态对完整 | 12 |
| transition note 记录人类评审员 | 12 |
| 执行 actor 与人类评审员是否分列 | 是：`actor_user_id` = 执行管理员；评审员署名为 `after_state.note = "human review by huangdi97"` |

> 注：平台没有独立的 `RuleVersion` 表——「版本」即 `access_rule` 行 +
> `status` + `supersedes_rule_id`。§18/§19 中「RuleVersion retained」按
> 「版本行保留、不被删除」核验，已通过。

### Resolver / API（§13–§14）

见下节：两项 FAIL，同源。

### 回滚（§18）

```
ROLLBACK_DRILL = PASS
```

在 rehearsal 库对完整依赖对 `sb-legal-dog + sb-sd-legal`：

| 步骤 | 结果 |
| --- | --- |
| 通过 API 撤回 carve-out | `effect: allowed → prohibited`，例外不再生效 |
| 直接 DB 撤回 base（**没有 API 路径，见下**） | `effect → unknown`，`compliance_state = UNKNOWN` |
| **Withdrawn → ALLOWED** | 未发生 |
| 撤前后 access_rule 行 / rule_exception 行 / evidence_bundle / source / audit | 全部保留（audit 2 → 3） |

### 取代（§19）

```
SUPERSESSION_DRILL = PASS
```

fixture V1 → V2 经真实 API 发布：`V1.status = superseded`，`V2.status = current`，
`V2.supersedes_rule_id = V1.id`，同一身份的 current 版本恰好 1 条；
self-supersede 不可能（`V2.supersedes != V2.id`），环检测 0 个。

### Watch（§20）

```
WATCH_DRILL = PASS
```

首次 sweep 通知 1 次；retry sweep 通知 **0** 次；`last_notified_at` 两次读值相同；
投递只落在 mock sink（Redis `mock:notifications`），**未发真实外部通知**。

> 演练中发现并修复了一个真实缺陷：`notify_rule_changes` 用**进程**时钟写水位
> 线、却与**数据库**时钟写入的 `AccessRule.updated_at` 比较。本机容器比主机快
> 约 22 秒，于是每次 sweep 都会重复通知。已改为水位线也取自 `SELECT now()`，
> 并新增 `tests/integration/test_watch_notify_idempotency.py`（两条测试：普通
> 重跑不重复；把进程时钟挪后 1 小时仍不重复）。已验证这两条测试在旧实现下
> **会红**、在修复后变绿。

> 未覆盖：真实外部抓取这一步。`fetch_url_safely` 的 SSRF 守卫禁止访问
> 127.0.0.1，本地无法构造合法的"来源变更"抓取；演练改用 fixture 提供变更→
> 证据链，并在报告中标注。

### 回归（§24）

| 门禁 | 结果 |
| --- | --- |
| pytest（全量） | **579 passed** |
| Publisher 关键测试 ×3 | 104 / 104 / 104 passed |
| ruff check | All checks passed |
| ruff format --check | 177 files already formatted |
| mypy（`services/api`） | Success: 77 source files |
| ESLint (`pnpm lint:fe`) | 0 problems |
| Prettier (`pnpm format:check:fe`) | All matched files use Prettier code style |
| H5 build | ✓ built in 5.85s |
| Admin build | ✓ built in 5.00s |
| E2E | 18 passed |
| visual regression | 45 passed + 2 flaky（admin login，重跑 2 passed） |
| a11y | 15 consumer + 10 admin + 3 keyboard walkthrough；**1 serious**（既存，见下） |

证据：`artifacts/regression_pytest.txt`、`artifacts/regression_publisher_x3.txt`、
`artifacts/regression_visual.txt`、`artifacts/regression_a11y.json`。

---

## 3. 两个未通过项（同源）

### 3.1 现象

**§13 `RESOLVER_POST_PUBLISH = FAIL`**

| 场所 | 查询 | 期望（§13） | 实测 |
| --- | --- | --- | --- |
| DISNEY | ordinary_pet | prohibited | prohibited ✔ |
| DISNEY | guide_dog | 例外生效 | **unknown，applied_exceptions = []** ✘ |
| FAIRMONT | ordinary_pet / guide_dog | prohibited / 例外生效 | prohibited / allowed ✔ |
| 上海图书馆 | ordinary_pet / guide_dog | prohibited / 例外生效 | prohibited / allowed ✔ |
| 上海图书馆 | police_dog / military_working_dog | 不得因 HOLD 例外变 allowed | **prohibited / prohibited ✔**（安全方向通过） |
| 星巴克臻选 | dog / guide_dog | 法定禁令 / 法定例外 | prohibited / allowed ✔ |

**§14 `ENGINE_CONSISTENCY = FAIL`**

| 场所 | 查询 | `/effective-rules`（分层 resolver） | `/rules/evaluate`（消费者答案） |
| --- | --- | --- | --- |
| disney | dog + service_role=working | `unknown`（不允许） | **`MATCH`（允许）** ✘ |

其余三处两引擎一致。

### 3.2 根因（同一条）

发布器械本身没有错：`dl-sd-op` 已按签署内容正确发布为 RuleException，
层内一致地挂在 `dl-pet-ban`（OPERATOR_POLICY）上，证据链完整。

问题在**求解语义**：

1. **resolver 只对「在本次查询作用域内的 base」应用 carve-out**
   （`resolve()` 先 `in_scope(base_layer)` 再 `apply_exceptions`）。
   `dl-pet-ban` 作用域是 `ordinary_pet`，`dl-sd-op` 作用域是 `guide_dog`。
   服务犬查询里 base 不在范围内 ⇒ 例外永不触发 ⇒ **这条已发布的例外是死规则**
   ⇒ guide_dog 在迪士尼得到 UNKNOWN。
2. **`/rules/evaluate` 走的是另一套匹配**：它按 `animal_scope = 'service_dog'`
   粗匹配例外，**不要求 base 在范围内**，而且 API 构造例外载荷时根本没把
   ADR-025 的 `subject_scope_normalized` / `normalization_type` 传进去。
   于是它对任何服务犬查询都套用「导盲犬」的但书——正是 ADR-025 要防的那种
   未经证明的作用域扩张。

同一条数据，两部引擎给出相反结论，而消费者看到的是后者。

### 3.3 建议（**需要人类决定，本轮不擅自修改**）

任选其一，都属语义变更，需评审：

- **A. 先修语义再发布**
  - 让 resolver 支持「base 不在查询作用域内时，carve-out 仍可作为独立许可生效」，或
  - 让 `/rules/evaluate` 改用与 resolver 相同的 `rule_governs` 精确匹配，
    并在载荷中补上 ADR-025 的 scope 字段。
  - 前者会改变迪士尼的既有答案（UNKNOWN → 有条件允许），后者会收紧消费者答案。
- **B. 重划批次**：把 `dl-sd-op`（必要时连同 `dl-pet-ban`）从 Batch 01 移出，
  先发布其余 10 条。迪士尼条目回到人工复核，待迪士尼的 LEGAL 对
  （`dl-legal-dog` / `dl-sd-legal`，目前都是 HOLD）有结论后再一起处理。

我倾向 **B**：它是收窄而不是放宽，不需要先动求解器语义，
而且 §13 里最关键的安全方向（军警犬不得被放宽）本来就已经通过。

### 3.4 a11y 的既存问题（与发布无关）

`place-restricted` 页「no visible `<h1>`」。本轮未改动任何前端代码
（`git status -- apps/` 为空），因此属于既存缺陷，不在本轮范围内。

---

## 4. 待你授权

本轮**没有**对正式目标数据库执行任何 `--execute`。正式发布命令形态（未执行）：

```bash
python scripts/publish_reviewed_r1.py \
  --execute \
  --batch-file docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json \
  --max-approve 12 \
  --reviewer huangdi97
```

请选择：

1. 按 §3.3 **B** 重划批次后授权发布；或
2. 按 §3.3 **A** 先修求解语义（需新一轮复核 + 重新演练）；或
3. 维持 12 条不变直接授权发布（则迪士尼条目在 resolver 中会是死规则，
   且消费者答案与 resolver 不一致——我不建议）。

---

## 5. 交付物

### 代码 / 文档

| 文件 | 作用 |
| --- | --- |
| `docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json` | 批次清单（12 条） |
| `docs/governance/PUBLISH_BATCHES.md` | 批次选择规范、拒绝项、命令形态、演练流程 |
| `scripts/publish_batch.py` | 清单解析 + 四类拒绝（身份 / 选择 / 依赖闭包 / base 无批准例外） |
| `scripts/publish_reviewed_r1.py` | 新增 `--batch-file`、`--database-name`、`--snapshot-out`；`--execute` 强制要求清单；修 `SELF_SUPERSEDE` 误报 |
| `scripts/db_cleanup_accidental.py` | 带守卫的误创建库清理（本次事故的处理工具） |
| `scripts/rehearsal_db.py` | 演练库创建/克隆/删除，denylist + allowlist 双守卫 |
| `scripts/dev_api_server.py` | 不回显凭据地把 API 指向指定库 |
| `scripts/verify_publish_r3.py` | §13–§20 验证（含 `--skip-drills`） |
| `scripts/rehearsal_r3_runbook.sh` | 两阶段演练脚本 |
| `services/api/app/worker/tasks.py` | 修复 watch 水位线的跨时钟域缺陷 |
| `tests/unit/test_publish_batch_selection.py` | 15 条批次选择测试 |
| `tests/integration/test_watch_notify_idempotency.py` | 2 条 watch 幂等回归测试 |
| `.prettierignore` | 生成物 `PUBLISHED_RULES_SNAPSHOT_*.json` 不进前端闸门 |

### 证据（全部在 `artifacts/`）

`accidental_db_cleanup_r3.json` · `batch01_prepublish_dryrun.json` ·
`rehearsal_db_fingerprint.json` · `rehearsal_execute_r3.json` ·
`rehearsal_execute_r3_receipt.json` · `rehearsal_idempotency.json` ·
`rehearsal_idempotency_run2.txt` · `rehearsal_order_and_counts.json` ·
`publish_rehearsal_r3_verification.json` · `regression_pytest.txt` ·
`regression_publisher_x3.txt` · `regression_visual.txt` · `regression_a11y.json`

### 清理

- `petaccess_dev_only`（误创建库）已删除并复核。
- 根目录下由早期演练产生的 `PUBLISHED_RULES_SNAPSHOT_R1.json` 已删除——
  演练回执不应写成看起来像正式回执的文件（后续演练用 `--snapshot-out` 指向
  `artifacts/`）。
- `petaccess_publish_rehearsal_r3` 保留，可随时重建重跑。
