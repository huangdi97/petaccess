# 生产完整性遗留项收口（PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE）

- 轮次：`PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE_R1`
- 目标库：`petaccess`（角色 `PRODUCTION`）
- 签署修订：`R2-FINAL-R3` · 复核人：`huangdi97`（未改动）
- 执行时间：2026-09-17
- 证据目录：`artifacts/integrity_final_closure/`
- 还原点：`artifacts/integrity_final_closure/petaccess_before_integrity_closure.dump`（`pg_dump -Fc`）

---

## 0. 结论

| 闸门 | 结果 |
|---|---|
| `PRODUCTION_DATA_ISOLATION_GATE` | **PASS** |
| `PRODUCTION_INTEGRITY_GATE` | **PASS** |
| `PRODUCTION_INTEGRITY_CRITICAL` | 0 |
| `PRODUCTION_INTEGRITY_HIGH` | 0 |
| `PRODUCTION_INTEGRITY_MEDIUM` | 1（已解释，见 §5） |
| `FIRST_REAL_BATCH_INTACT` | PASS |
| `HUMAN_SIGNATURE_INTACT` | PASS |
| `30_50_PLACE_EXPANSION` | `READY_TO_START`（**未启动**） |
| `SEMANTIC_REMODEL_ISSUE` | `OPEN`（本轮不处理） |

本轮**没有**新增场所、没有抓数据、没有新发布、没有新人工复核。

---

## 1. 收口前快照（§3）

`PROD_PRE_INTEGRITY_FINAL_CLOSURE` 指纹：`3c8c5306…31fb`，与上一轮收尾时**逐字节一致**——
证明自上一轮以来生产库未被任何东西改动，本轮取证起点是干净的。

---

## 2. L1 — 青岚公园·演示 的重复 current 规则

`L1_PLACE = 青岚公园·演示`（`9152b7dc`），`zone = 645e539f`。

`L1_DUPLICATE_COUNT = 2`：

| 规则 | animal_scope | effect | recorded_at | rule_origin | Source | EvidenceBundle | Candidate |
|---|---|---|---|---|---|---|---|
| `decd5051` | `ordinary_pet` | `conditional` | 2026-05-15 | `official_regulation` | 演示市绿化市容管理局（虚构），URL `demo-gov.example` | 无 | 无 |
| `440e419e` | `ordinary_pet` | `prohibited` | 2026-08-13 | `onsite_signage` | 青岚公园入口告示（用户上传，虚构），无 URL | 无 | 无 |

**判定依据**：两条的签发方都**在字段里显式自述为虚构**，来源 URL 落在保留域
`demo-gov.example`；二者均无 `EvidenceBundle`、无 `RuleCandidate` 血缘、
审计只有演示性的 `dispute.submit`（`actor_role=admin`）。
既不是真实业务规则，也不是真实的版本冲突——`supersedes_rule_id` 与
`superseded_by_rule_id` 全为空，从未存在过替代关系。

`L1_CLASSIFICATION = B / CONFIRMED_DEMO_SEED`（两条同）
`L1_ACTION = CLEANED`（随同一场所的 demo 数据一并清理）
`L1_DUPLICATE_CURRENT_RESOLUTION = CLEANED`

| 指标 | 值 |
|---|---|
| `L1_RESOLVER_BEFORE` | 2 条 current 同时作用于同一 zone（`conditional` 与 `prohibited` 并存） |
| `L1_RESOLVER_AFTER` | 该场所已不存在，无规则可冲突 |
| `L1_CURRENT_AFTER` | 0 |
| `L1_DUPLICATE_CURRENT_GROUPS`（全库） | 清理前 1 → **清理后 0** |

§6 的三个前置条件全部满足：无真实 Evidence、无真实 Source 依赖、
无真实生产消费方（零 `watch_subscription`、零 `verification_event`、
零 `dispute_case` 指向这两条）。

---

## 3. L2 — 5 个 demo 场所 + 4 条 demo 法律层规则

`DEMO_SEED_PLACES_FOUND = 5` · `DEMO_SEED_PLACES_CONFIRMED = 5` ·
`DEMO_SEED_PLACES_REMOVED = 5` · `DEMO_SEED_PLACES_RETAINED = 0`

全部 5 个都命中 canonical seed 注册表 `services/api/app/db/seed.py`
（另有 `scripts/production_fixture_cleanup.py` 二次命中），满足 §9 的清理前提。

| place_id | 名称 | 类型 | zones | rules | cands | Seed 命中 | Git 引用 |
|---|---|---|---|---|---|---|---|
| `8412b521` | 星河咖啡·测试店 | cafe | 2 | 4 | 0 | ✅ `seed.py` | `scripts/perf_baseline.py`、`tests/e2e/h5-journey.spec.ts` |
| `c2223bd1` | 松风社区·演示 | residential_community | 4 | 3 | 0 | ✅ `seed.py` | — |
| `5a9084d0` | 云栖中心·测试商场 | mall | 5 | 8 | 0 | ✅ `seed.py` | `scripts/a11y_audit.mjs`、`tests/visual/fixtures.ts` |
| `9152b7dc` | 青岚公园·演示 | park | 4 | 6 | 0 | ✅ `seed.py` | 既有污染审计文档 |
| `3b5a341a` | 星河咖啡·栖霞分店 | cafe | 0 | 0 | 0 | ✅ `seed.py` | `scripts/a11y_audit.mjs` |

`DEMO_LEGAL_RULES_FOUND = 4` · `DEMO_LEGAL_RULES_CONFIRMED = 4` ·
`DEMO_LEGAL_RULES_REMOVED = 4`

4 条全在 `jurisdiction_rule`，签发方一律自述为「（虚构）」，
且都**不引用真实法规 Source**。全部随夹具一并清除。

`SHARED_REAL_SOURCES_DELETED = 0`

清理对 Source 的处理是「先删引用者，再删**无人再引用**的 Source」：
本轮 `sources_considered = 10`，`sources_deleted = 10`，`sources_retained_shared = 0`
——被删除的 10 个在被删那一刻已经零引用；任何仍被真实实体引用的 Source 都会被保留
（该行为已由 §20 回归测试双向锁定）。

**清理后仍保留的 10 个场所**（全部为真实业务场所）：

```
前滩太古里 / 上海迪士尼乐园 / 广场公园（黄浦段） / 大吉路公园 / 港汇恒隆广场
上海图书馆东馆 / 和平饭店（费尔蒙） / 星巴克臻选上海烘焙工坊
Manner咖啡（凯德虹口商业中心店） / 星巴克咖啡（徐汇西岸梦中心店）
```

---

## 4. L3 — 三个 UNKNOWN 场所

| place_id | 名称 | 分类 | 处置 |
|---|---|---|---|
| `466969e5` | DBG咖啡1789275599 | `CONFIRMED_TEST_FIXTURE` | 已清理 |
| `19db2566` | T商场6ad9c1 | `CONFIRMED_TEST_FIXTURE` | 已清理 |
| `1aa219c1` | T3商场d14555 | `CONFIRMED_TEST_FIXTURE` | 已清理 |

`UNKNOWN_AUTO_DELETED = 0`——三者都不是以「UNKNOWN」身份被删的，
而是先各自取得确定分类，再按分类处置。

**证据链**（每个都逐条核对，不是看名字难看）：

1. **名称是机器生成的**：`DBG` + unix 秒、`T`/`T3` + hex6。真实场所不会有这种名字。
2. **零真实场所属性**：三者均无 `canonical_address`、无 `location` 几何、无 `operator_id`、无 `parent_place_id`。（已与 10 个保留场所逐一对比。）
3. **无真实来源**：`T条例` / `T3条例` 没有 `source_url`、没有法规文件、签发未核验；
   `DBG` 场所的 source/artifact/evidence/candidate 在 **550 ms 内**与 place 一起出现——脚本化爆发，不是人工录入。
4. **零生产依赖**：无 `watch_subscription`、无 `verification_event`、无 `observation_claim`、
   无 `place_geometry`、无 `external_place_ref`；其规则上无 `rule_exception`；无已发布候选指向它们。
5. **不进候选/复核流程**：`T`/`T3` 各挂 1 条 `access_rule` 但 `rule_candidate = 0`
   ——直接建规则，绕过了治理链路。

**保留的残余不确定性（不粉饰）**：这三个在 canonical seed 注册表里**没有命中**
（`registry_hits = 0`，它们出自一次性脚本而非 `seed.py`），
且审计溯源受 §5 的 `target_id` 缺陷影响而不完整。
因此它们是按「属性证据链」而非「注册表」定级的。若事后判断需要回看，
`artifacts/integrity_final_closure/petaccess_before_integrity_closure.dump` 是完整字节级还原点。

---

## 5. 剩余 MEDIUM 一项：`AUDIT_TARGET_ID_UNUSABLE`

`2647 行 / 4 组`（`place` 1185、`source` 1379、`jurisdiction_rule` 68、`zone` 15）。

- **根因（活跃缺陷，非纯历史）**：ORM 对象 `db.add()` 后未 `flush()`，主键尚不存在，
  `str(obj.id)` 得到字符串 `"None"` 并被写入 `audit_log.target_id`。
- **已修三层**：
  1. 13 处 `record_audit` 调用点补 `db.flush()`
     （`places` / `sources` / `rules` / `regulations` / `disputes` / `operators` / `v05`）；
  2. `record_audit` 写入时断言——`"None"` / 空值直接 `ValueError`，
     在还能拿到对象的那一刻失败，不等下一轮扫描；
  3. 静态回归锁 + 运行时断言测试（见 §7）。
- **历史行不回填**：没有任何确定性来源能还原这 2647 行本该指向谁，按 §17 只保留并解释。
- **最后一条 `"None"` 行**产生于 `2026-09-17 07:40`，早于本轮修复；修复后无新增。

契约全文见 `docs/governance/AUDIT_EVENT_CONTRACT.md`。

---

## 6. L4 — 发布审计契约统一

| 指标 | 结果 |
|---|---|
| `CLI_RULE_EXCEPTION_AUDIT_CONTRACT` | **PASS**（发布器新增自检，缺失即 FAIL 并列出） |
| `HTTP_CLI_AUDIT_EVENT_PARITY` | **PASS**（同一 `AuditEvent` 常量，禁止字面量） |
| `BATCH01B_RULE_EXCEPTION_AUDIT` | **3 / 3** |
| `AUDIT_BACKFILL_COUNT` | **3** |
| `AUDIT_HISTORY_DELETED` | **0** |
| `VERIFY_PUBLISH_R3_AUDIT_LINKAGE` | **PASS** |

关键点：**不是**放宽校验器换来的绿灯。`verify_publish_r3.py` 未改判定逻辑；
是发布器补上了本该写的事件。

生产库现有 `candidate.publish_exception` 行：

```
action                      | target_type    | count | backfilled | reason
candidate.publish_exception | rule_exception |     3 | true       | CLI_AUDIT_EVENT_CONTRACT_RECONCILIATION
```

每条都带 `rule_exception_id` / `base_rule_id` / `reviewer` / `batch_id`
与 `original_publish_at`；`created_at` 用回填当时时刻，不伪造原始时间。

---

## 7. 本轮新增的永久锁

| 文件 | 锁住什么 |
|---|---|
| `tests/integration/test_production_integrity_closure.py` | §19 回滚是真的（**另开连接**验证，不断言日志文本）；§20 夹具法律层 Source 随夹具清除，共享 Source 必须保留；§24 清理只追加审计 |
| `tests/unit/test_audit_event_contract.py` | §14–16 事件词表唯一、发布器与校验器同源、回填必须自标注、`target_id` 写入时断言 |
| `tests/unit/test_dev_api_psycopg_url.py` | §21 URL 转换只有一处实现（`app.core.config.psycopg_url`），脚本侧不得再抄一份 |
| `services/api/app/core/audit_events.py` | canonical 事件词表（唯一权威） |
| `scripts/backfill_publish_exception_audit.py` | 受治理的 append-only 回填 |
| `scripts/demo_closure_cleanup.py` | 受治理清理：`mutate → 校验 → COMMIT`（顺序即语义） |
| `scripts/forensics_provenance.py` | 可复用的取证工具（L1/L2/L3 全部结论由它产出） |

顺带修掉的真实问题：`scripts/check_production_integrity.py` 对聚合型检查把
`count(*)` 的结果当行数，会在值为 0 时报「发现 1 条」。已改为逐行输出。

---

## 8. 保护验证

| 项 | 结果 |
|---|---|
| `FIRST_REAL_BATCH_INTACT` | **PASS**——8/8 候选仍 `PUBLISHED`，5 条 `AccessRule` + 3 条 `RuleException` 仍 `current`，ID 未变 |
| `HUMAN_SIGNATURE_INTACT` | **PASS**——37 行 / 23 APPROVED / 9 HOLD / 5 REJECTED / reviewer `huangdi97` |
| Source / Evidence / Artifact | 清理前后 `3 / 8 / 10` 全数不变 |
| `audit_log` | 9254 → 9259（+3 回填 +2 治理记录），**零删除** |
| Resolver（15 项观测） | `mismatches = 0`；费尔蒙 普通宠物 `prohibited` / `dog` `prohibited` / `guide_dog` `allowed`；上图 五个 subject 全对；星巴克臻选 `dog` `prohibited` / `guide_dog` `allowed` |
| `HOLD_PUBLISHED` / `REJECTED_PUBLISHED` | 0 / 0 |

---

## 9. 全量回归（本轮真实数字，不引用旧值）

| 项 | 结果 |
|---|---|
| pytest | **643 passed / 2 skipped** |
| ruff check | **PASS** |
| ruff format --check | **PASS**（195 files） |
| mypy | **PASS**（79 files） |
| ESLint | **PASS** |
| Prettier | **PASS** |
| H5 build | **PASS**（E2E 与视觉两种配置各一次） |
| Admin build | **PASS** |
| E2E | **18 passed** |
| Visual | **47 passed** |
| a11y | **0 issues** |
| Publisher critical ×3 | **PASS**（执行 / 幂等 NOOP=8 / 校验 8 项全 PASS，含 `AUDIT_LINKAGE`） |
| DB isolation proof | **18 passed** |
| `BACKGROUND_TEST_PROCESS_LEAKS` | **0** |

a11y 的一个公开问题：首次冷启动跑出 1 项 `serious`（`place-restricted` 无可见 `<h1>`），
复核后确认是**冷启动时序抖动**——页面首屏数据未回来就被测量，
而非真实缺陷（DOM 抓取证明 `<h1>云栖中心·测试商场` 可见且 controls=24）。
已做两处不掩盖缺陷的加固：审计前预热 API；
以及把「页面根本没渲染出来」与「测出了缺陷」分开——
后者报缺陷，前者标 `NA` 并让进程**以失败退出**（空文档上的 0 issues 绝不能算绿）。
加固后冷启动重跑：**0 issues**。

---

## 10. 零差异证明（§39）

| 指纹 | 值 |
|---|---|
| `PROD_FINGERPRINT_QA_BEFORE` | `19f9f54236bba7563ca21105cf2506b00a064890b43c64160cc5c8bb199ed742` |
| `PROD_FINGERPRINT_QA_AFTER` | `19f9f54236bba7563ca21105cf2506b00a064890b43c64160cc5c8bb199ed742` |
| `PRODUCTION_DB_ROW_DIFF_AFTER_FULL_QA` | **0** |
| `PRODUCTION_DB_SEMANTIC_DIFF_AFTER_FULL_QA` | **0** |

覆盖的完整 QA：pytest（含隔离证明）、ruff、mypy、ESLint、Prettier、H5/Admin build、
E2E、visual、a11y、Publisher critical ×3。

---

## 11. 下一状态

```
PRODUCTION_DATA_ISOLATION_GATE = PASS
PRODUCTION_INTEGRITY_GATE      = PASS
30_50_PLACE_EXPANSION          = READY_TO_START   # 未启动
SEMANTIC_REMODEL_ISSUE         = OPEN             # 下一条独立工作流
```

按 §44 停止：不进入 30–50 扩张、不做语义重构、不做新发布、不开新人工复核。

进入扩张前仍待人类裁决的一件事：生产库里 10 个真实场所中，
只有 3 个（费尔蒙 / 上图 / 星巴克臻选）带有已发布规则，
其余 7 个是真实场所但**尚无规则数据**。这是扩张阶段的输入，不是本轮的缺陷。
