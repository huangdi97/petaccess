# 生产数据隔离与完整性收口 —— 闸门报告 R1

轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`
日期：2026-09-17
闸门结论：**PASS_WITH_LIMITATIONS**（判定依据见 §5）

---

## 1. 本轮做了什么

| 区块 | 内容 |
| --- | --- |
| §4–§8 角色模型 | 新增 `services/api/app/db/safety.py`：8 种 `DatabaseRole`、`ROLE_REGISTRY` 正向白名单、import 期互斥校验 |
| §6–§7 中心闸门 | 唯一权威 `DatabaseSafetyGuard`；未知库名拒绝；PRODUCTION 通用破坏性断言恒 False，清理走专用受治理入口 |
| §9–§13 负载隔离 | pytest session 守卫（exit 4）、E2E globalSetup、visual rehearsal、celery 队列 = 库名、redis DB 按负载分 |
| §18–§22 清单与分类 | `scripts/production_fixture_cleanup.py` inventory：1,231 CONFIRMED / 3 UNKNOWN / 10 REAL / 5 HISTORICAL |
| §25–§28 受治理清理 | 两批共 13,019 行；各有 pg_dump 还原点、dry-run 复核且确定性已证明、A/B 差异 PASS |
| §29–§30 重复 current 审计 | `青岚公园·演示` zone `645e539f` 两条 current 打架 → `MANUAL_REVIEW_REQUIRED` |
| §31–§33 完整性扫描 | `scripts/check_production_integrity.py` 23 项只读检查 |
| §34/§51 零差异证明 | 全量 QA 前后指纹 `C` vs `E` 逐字节相同 |

新增工程文档（§52）：`DATABASE_ENVIRONMENT_MODEL.md` · `TEST_DATABASE_ISOLATION.md` ·
`PRODUCTION_DATA_INTEGRITY.md` · `PRODUCTION_CONTAMINATION_AUDIT.md` ·
`PRODUCTION_CLEANUP_REPORT.md` · `PRODUCTION_DB_RUNBOOK.md` ·
`PRODUCTION_DUPLICATE_CURRENT_AUDIT.md`。
更新：`TESTING.md` · `QUALITY_GATE.md` · `LOCAL_DEV_WINDOWS.md`。

---

## 2. §54 指标块

### 2.1 治理对象完整性

| 指标 | 值 | 判定 |
| --- | --- | --- |
| `FIRST_REAL_BATCH_INTACT` | 8/8 候选仍 `PUBLISHED`，8/8 带 `published_rule_id` | PASS |
| `BATCH_ACCESS_RULES_CURRENT` | 5/5 base + 3/3 carve-out 仍 `current` | PASS |
| `HUMAN_REGISTRY_SHA256` | `bd216afd…e1a5`（清理前后一致） | PASS |
| `BATCH_MANIFEST_SHA256` | `b81a97ad…ea78`（清理前后一致） | PASS |
| `NEW_PUBLISH_THIS_ROUND` | 0（无新发布，无 30–50 扩张，无语义重构） | PASS |
| `SEMANTIC_REMODEL_DECISION` | 未做（open issue 保留） | PASS |

### 2.2 隔离

| 指标 | 值 | 判定 |
| --- | --- | --- |
| `DB_PHYSICALLY_ISOLATED` | 8 角色各有独立库名模式，registry 互斥校验通过 | PASS |
| `UNKNOWN_DB_REFUSED` | 未登记库名 → `UnknownDatabaseRefused` | PASS |
| `PYTEST_REFUSES_PRODUCTION` | 指向 `petaccess` → exit 4（非 TEST 角色） | PASS |
| `E2E_REFUSES_PRODUCTION` | `globalSetup` 读 `/health/database`，非 E2E 拒绝 | PASS |
| `VISUAL_REFUSES_PRODUCTION` | `visual_db_reset.py` 只接受 VISUAL | PASS |
| `REHEARSAL_REFUSES_PRODUCTION` | `rehearsal_db.py` 只接受 REHEARSAL；克隆源只接受 PRODUCTION | PASS |
| `CLEANUP_REFUSES_WITHOUT_EVIDENCE` | 缺备份或缺已审阅 dry-run → 拒绝 | PASS |
| `§50_PROOF_TESTS` | `tests/isolation` **18 passed**（六种负载指生产库全部失败） | PASS |
| `PRODUCTION_CONNECTION_OPT_IN` | `--production-confirm` 缺失即拒绝，无默认路径 | PASS |

### 2.3 清理

| 指标 | 值 | 判定 |
| --- | --- | --- |
| `CONFIRMED_FIXTURES_REMOVED` | 13,019 行（12,883 + 136） | PASS |
| `UNKNOWN_AUTO_DELETED` | **0**（3 个 UNKNOWN 场所仍在库内） | PASS |
| `LIKELY_AUTO_DELETED` | 0 | PASS |
| `HISTORICAL_GOVERNANCE_DELETED` | 0（5 个 demo seed 场所保留） | PASS |
| `REAL_PRODUCTION_DELETED` | 0（10 个真实试点场所全在） | PASS |
| `AUDIT_LOG_DELETED` | 0（9,254 行，追加式） | PASS |
| `CLEANUP_DIFF` | **PASS**（无表增长、两哈希不变、批次对象不变、键集只减不增） | PASS |
| `CLEANUP_DETERMINISM` | 同参数重跑 0 结构差异 | PASS |
| `BACKUP_RESTORE_POINTS` | 2 份 `pg_dump -Fc`（1.6 MB + 0.7 MB） | PASS |

### 2.4 完整性

| 检查项 | 清理前 | 清理后 | 判定 |
| --- | --- | --- | --- |
| `TEST_FIXTURE_PLACE_IN_PRODUCTION` | 1,231 | **0** | PASS |
| `TEST_FIXTURE_SOURCE_IN_PRODUCTION` | 1,423 | **0** | PASS |
| `TEST_ACCOUNT_IN_PRODUCTION` | 1,636 | **0** | PASS |
| `PUBLISHED_WITHOUT_EVIDENCE` | 64 | **0** | PASS |
| `PUBLISHED_WITHOUT_SOURCE` | — | **0** | PASS |
| `PUBLISHED_WITHOUT_AUDIT` | 251（口径修正后 0） | **0** | PASS |
| `HOLD_OR_REJECTED_PUBLISHED` | 0 | 0 | PASS |
| `ORPHAN_RULE_EXCEPTION` | 0 | 0 | PASS |
| `SELF_SUPERSEDE` / `SUPERSESSION_CYCLE` | 0 | 0 | PASS |
| `CROSS_LAYER_EXCEPTION` | 0 | 0 | PASS |
| `CONFLICTING_CURRENT_RULES` | 2 | 2 | **LIMITATION**（已分类，人类裁决） |
| `DUPLICATE_CURRENT_RULE` | 2 | 2 | **LIMITATION**（同一组） |
| `AUDIT_TARGET_ID_UNUSABLE` | 4 | 4 | **LIMITATION**（追加式，不可修） |
| `ORPHAN_SOURCE` / `RULES_WITHOUT_PLACE` | — | 2 / 17 | INFO，demoseed zone 级规则 |

### 2.5 全量 QA 零改动

| 指标 | 值 | 判定 |
| --- | --- | --- |
| `PRODUCTION_DB_ROW_DIFF` | **0**（40 张表逐表比对） | PASS |
| `SEMANTIC_DIFF` | **0** | PASS |
| `FINGERPRINT_PRE` | `3c8c5306ec273c2e5220e97b1f00c5c41a2ab90232d7d099aecce9896ebd31fb` | — |
| `FINGERPRINT_POST` | `3c8c5306ec273c2e5220e97b1f00c5c41a2ab90232d7d099aecce9896ebd31fb` | — |
| `GOVERNED_SECTION_IDENTICAL` | true | PASS |
| `IDENTITY_IDENTICAL`（alembic `b8d2f4a1c556`） | true | PASS |

### 2.6 回归（最终状态实测）

| 项目 | 结果 |
| --- | --- |
| `pytest` | **622 passed, 2 skipped** |
| `ruff check` | All checks passed（188 files） |
| `ruff format --check` | 188 files already formatted |
| `mypy`（`services/api`） | Success: no issues found in 78 source files |
| `eslint` / `prettier` | 0 problems / all matched files use Prettier code style |
| `admin` build | OK |
| `client-h5` build | OK |
| Playwright E2E | **18 passed**（`globalSetup` 证明跑在 `petaccess_e2e` / E2E） |
| Playwright 视觉 | **47 passed** |
| a11y | **0 issues / 25 页面检查 + 3 键盘走查** |
| UI 采集 | 完成 |
| §50 隔离证明 | **18 passed** |
| 生产只读冒烟 | 执行完成（发现 1 项合约不一致，见 §4） |

---

## 3. 未处理的 CRITICAL：0 项

`CONFLICTING_CURRENT_RULES = 2` 与 `DUPLICATE_CURRENT_RULE = 2` 是**同一组对象**，
已完整分类并给出裁决建议（`PRODUCTION_DUPLICATE_CURRENT_AUDIT.md`）：

- 位置：`青岚公园·演示`（`9152b7dc`）的 zone `645e539f`「A 草坪」，
  `animal_scope = ordinary_pet` / `action = walk`；
- 两条 current：`decd5051`（`conditional`，2026-05-15）与 `440e419e`（`prohibited`，2026-08-13）；
- 判定：**HISTORICAL** —— 都属 `DEMO_SEED_PLACES`，发布时间早于本轮，
  且带 fixture 签发方来源。按 §30 归 `MANUAL_REVIEW_REQUIRED`，**不自动删除**；
- 删除它会连带删掉 §29 唯一可复核的现场，因此本轮保留现场、只出结论。

无其他未处理 CRITICAL / HIGH。

---

## 4. 本轮发现并记录的两项一致性问题

1. **发布器审计动作名不一致**：`candidate.publish_exception` 只有 HTTP 路由
   （`v05.py:560`）会写，CLI 发布器（`candidate_service.publish_exception`）**不写审计行**。
   3 条 carve-out 在发布时刻**确有** `candidate.transition` 审计（所以治理链完整），
   但缺 HTTP 路由专属的那个动作名——`verify_publish_r3.py` 的 `AUDIT_LINKAGE` 因此报 FAIL。
   这是**校验器与发布器的合约不一致**，不是审计缺失。本轮只记录，不改发布器
   （改它等于动已发布批次的语义，超出本轮授权）。
2. **`audit_log.target_id` 有 2,647 行是字面量 `'None'`**（`source` / `place` / `zone` /
   `jurisdiction_rule` 四类）。追加式表，不可修；影响的是"按审计反查"的可用性，
   不影响已发布对象本身。

---

## 5. 闸门判定

按 §55，PASS 需要同时满足：首批真实发布对象完整 · 数据库物理隔离 ·
pytest/E2E/视觉/演练对生产库 fail-closed · UNKNOWN 未被自动删除 · 重复 current 已分类 ·
完整性无未处理 CRITICAL · 全量 QA 语义差异 0 · 回归全绿。

其中**"完整性无未处理 CRITICAL"**这一条需区分两种含义：

- 未**处理**（未发现、未分类、未给裁决建议）→ **0 项**；
- 未**消除**（该项仍然存在）→ 2 项（同一组 `青岚公园·演示` 重复 current），
  且按 §30 明确规定这类必须 `MANUAL_REVIEW_REQUIRED` 而**不得自动改**。

另外 §0「`petaccess` 只承载真实业务数据」未 100% 达成：库内仍有
5 个 demo seed 场所 + 3 个 UNKNOWN 场所 + 4 条 demo 法律层规则。

因此本轮判定为 **PASS_WITH_LIMITATIONS**，而不是 PASS。
这不是把标准调低——是把"还没做完的事"和"做错了的事"分开记。

### Limitations 清单

| # | 内容 | 归属 |
| --- | --- | --- |
| L1 | `青岚公园·演示` zone `645e539f` 两条 current 冲突（发布前既有 demo 语义问题） | 人类裁决，见 `PRODUCTION_DUPLICATE_CURRENT_AUDIT.md` |
| L2 | 5 个 demo seed 场所 + 4 条 demo 法律层规则仍在生产库 | 下一轮决定是否迁移到 `petaccess_dev` |
| L3 | 3 个 UNKNOWN 场所（`DBG咖啡1789275599` / `T商场6ad9c1` / `T3商场d14555`）证据不足 | 人类逐个裁决 |
| L4 | `audit_log` 2,647 行 `target_id` 为 `'None'` | 不可修，接受 |
| L5 | `candidate.publish_exception` 审计动作 CLI 侧缺失 | 发布器合约修复，不在本轮范围 |
| L6 | `ORPHAN_SOURCE=2` / `RULES_WITHOUT_PLACE=17` | INFO，demoseed zone 级规则 |

---

## 6. 停止点

按 §58：**STOP**。不进入 30–50 场所扩张，不做语义重构，不做新发布。
下一步应由人类就 L1–L3 给出裁决。
