# 生产库运维手册（PRODUCTION_DB_RUNBOOK）

面向 `petaccess`（角色 `PRODUCTION`）的**每一次**操作。
本手册的前提：`services/api/app/db/safety.py` 里的 `DatabaseSafetyGuard` 是唯一权威，
**不要绕过它，也不要在别处再写一份"禁止库名"清单**。

---

## 0. 三条不可协商的规则

1. **角色判定只信服务端探针**。`classify_database_name(current_database())`，
   不解析连接串、不信环境变量、不信调用方自称。
2. **未知库名一律拒绝**（`UnknownDatabaseRefused`）。白名单是正向的，
   没登记过的库名不是"应该允许"，是"必须拒绝"。
3. **PRODUCTION 的通用破坏性断言恒为 False**。任何 `assert_destructive_allowed()`
   对 `petaccess` 都会抛异常——这是设计，不是 bug。需要破坏性操作时走下面的专用入口。

---

## 1. 角色速查

| 角色 | 库名模式 | 夹具写入 | 破坏性重置 | 真实发布 | 真实数据 |
| --- | --- | --- | --- | --- | --- |
| `PRODUCTION` | `petaccess` | ✗ | ✗ | ✓ | ✓ |
| `TEST` | `petaccess_test[_…]` | ✓ | ✓ | ✗ | ✗ |
| `E2E` | `petaccess_e2e[_…]` | ✓ | ✓ | ✗ | ✗ |
| `VISUAL` | `petaccess_visual` | ✓ | ✓ | ✗ | ✗ |
| `REHEARSAL` | `petaccess_publish_rehearsal_[a-z0-9_]{1,40}` | ✓ | ✓ | ✗ | ✗ |
| `DEVELOPMENT` | `petaccess_dev[_…]` / `petaccess_pilot` | ✓ | ✓ | ✗ | ✗ |
| `RESTORE` | `petaccess_restore_*` | ✗ | ✗ | ✗ | — |
| `INFRASTRUCTURE` | `postgres` / `template*` | ✗ | ✗ | ✗ | — |

`ROLE_REGISTRY` 在 import 时做互斥校验（`_assert_registry_is_disjoint`）——
两条模式一旦重叠，模块直接起不来，不会静默地"先匹配到谁算谁"。

随时查看当前分类：

```bash
PYTHONPATH= .venv/Scripts/python.exe -m app.db.safety --describe        # 全量角色表
PYTHONPATH= .venv/Scripts/python.exe -m app.db.safety --probe-db petaccess
```

---

## 2. 常规操作

### 2.1 起一个指向生产库的 API（默认拒绝，需显式授权）

```bash
cd services/api
PYTHONPATH= ../../.venv/Scripts/python.exe ../../scripts/dev_api_server.py \
  --db-name petaccess --role PRODUCTION --production-confirm --port 8012
```

少了 `--production-confirm` 会直接被拒。起完确认它连的是谁：

```bash
curl -s http://127.0.0.1:8012/health/database
# {"database":"petaccess","role":"PRODUCTION","app_env":"..."}
```

**收工必须把它杀掉。** 本轮就发现一个上轮遗留的 `dev_api_server.py --db-name petaccess`
（PID 15024，老代码、没有 `/health/database` 端点）一直连着生产库并返回夹具数据。
凡是指向 `petaccess` 的 dev 服务，收尾前逐个确认关闭：

```bash
netstat -ano | grep LISTENING | grep -E ":(8010|8011|8012)\b"
```

### 2.2 只读体检

```bash
# 23 项完整性扫描，只读，产物不可覆盖
PYTHONPATH= .venv/Scripts/python.exe scripts/check_production_integrity.py \
  --out artifacts/production_isolation/production_integrity_<label>.json

# 语义指纹（逐表行数 + 内容摘要 + 治理区键集）
PYTHONPATH= .venv/Scripts/python.exe scripts/production_fingerprint.py \
  --db-name petaccess --label <X> \
  --out artifacts/production_isolation/PROD_FINGERPRINT_<X>.json

PYTHONPATH= .venv/Scripts/python.exe scripts/production_fingerprint.py --compare A.json B.json
```

### 2.3 只读发布校验（不改任何东西）

```bash
PYTHONPATH= .venv/Scripts/python.exe scripts/verify_publish_r3.py \
  --db-name petaccess --api http://127.0.0.1:<port> \
  --batch-file docs/governance/publish_batches/<BATCH>.json \
  --skip-drills --out artifacts/...json
```

登录与 `effective-rules` 都是纯读（不写 `last_login`、不写审计），
所以这个组合对生产库是安全的。

---

## 3. 破坏性操作（唯一受治理路径）

### 3.1 夹具清理

```bash
# 1) 全量备份
docker exec petaccess-db-1 pg_dump -U petaccess -d petaccess -Fc -f /tmp/before.dump
docker cp petaccess-db-1:/tmp/before.dump artifacts/production_isolation/before.dump

# 2) dry-run（只读、事务回滚）
PYTHONPATH= .venv/Scripts/python.exe scripts/production_fixture_cleanup.py --dry-run \
  --out artifacts/production_isolation/CLEANUP_PLAN_DRY_RUN.json

# 3) 复核产物，再重跑一次确认确定性（除 at 外应 0 diff）

# 4) 执行
PYTHONPATH= .venv/Scripts/python.exe scripts/production_fixture_cleanup.py --execute \
  --confirm-database petaccess \
  --backup artifacts/production_isolation/before.dump \
  --i-reviewed-the-dry-run artifacts/production_isolation/CLEANUP_PLAN_DRY_RUN.json
```

闸门要求**同时**出示备份文件与已审阅 dry-run 文件，缺一即拒绝。
`reconcile_preconditions()` 在 **COMMIT 之前**判定，失败真回滚。

### 3.2 真实发布

```bash
PYTHONPATH= .venv/Scripts/python.exe scripts/publish_reviewed_r1.py \
  --registry docs/reality_audit/review_decisions_r2_final.json \
  --batch-file docs/governance/publish_batches/<BATCH>.json \
  --reviewer huangdi97 --execute --production-confirm
```

校验顺序：**先**验用法（裸 `--execute` 无 `--batch-file` 一律拒），
**再**验角色。这个顺序是有意的——用法错误必须先报用法错误，
否则会被角色拒绝的文案盖住，误导排查方向。

发布前演练（强制）：

```bash
python scripts/rehearsal_db.py --db-name petaccess_publish_rehearsal_r3 --clone --confirm
bash scripts/rehearsal_r3_runbook.sh phase1
python scripts/verify_publish_r3.py --db-name petaccess_publish_rehearsal_r3
```

### 3.3 误建库清理

`scripts/db_cleanup_accidental.py` 的保护集是「角色 ≠ UNKNOWN」——
即**所有已登记库名都受保护**，只有没登记过的名字才在清理范围内。
新增角色后保护范围自动扩大，不需要改脚本。

---

## 4. 隔离规则（谁也不许写生产）

| 负载 | 库 | Redis DB | Celery 队列 | 证明方式 |
| --- | --- | --- | --- | --- |
| pytest | `petaccess_test` | `/1` | `petaccess_test` | `tests/conftest.py` 的 `pytest_sessionstart`，非 TEST 角色 → exit 4 |
| Playwright E2E | `petaccess_e2e` | — | — | `tests/e2e/global-setup.ts` 读 `/health/database` |
| 视觉回归 | `petaccess_visual` | `/2` | `petaccess_visual` | `visual_db_reset.py` 的 `check_role()` |
| 发布演练 | `petaccess_publish_rehearsal_*` | — | — | `rehearsal_db.py` 的 `check_name()` |
| 开发 | `petaccess_dev` / `petaccess_pilot` | — | — | `dev_api_server.py --role` |

Celery 默认队列名 = 库名（`settings.celery_task_queue`），
这样"队列串了"和"库串了"会以同一种方式暴露，而不是各自静默。

供给一个隔离库：

```bash
PYTHONPATH= .venv/Scripts/python.exe scripts/isolated_db.py --role TEST --reset
PYTHONPATH= .venv/Scripts/python.exe scripts/isolated_db.py --role E2E  --reset
```

### 验证隔离没有失效

```bash
PYTHONPATH= DATABASE_URL="postgresql+psycopg://petaccess:***@127.0.0.1:5432/petaccess_test" \
  .venv/Scripts/python.exe -m pytest tests/isolation -q
```

`tests/isolation/test_production_fail_closed.py` 会把集成 / 视觉 / E2E / 演练 / 清理
五种负载**指向 `petaccess`**，断言每一个都失败。它们必须失败，不是通过。

---

## 5. 出事怎么办

| 现象 | 含义 | 处置 |
| --- | --- | --- |
| `UnknownDatabaseRefused` | 库名没登记 | 先确认该库该不该存在；该存在就去 `ROLE_REGISTRY` 登记，否则用 `db_cleanup_accidental.py` |
| `ProductionDatabaseRefused` | 某个非生产负载指到了生产库 | 检查 `DATABASE_URL` / `--db-name` / 连接串来源，不要改闸门 |
| `RoleMismatchRefused` | 库是真的，但不是你要的角色 | 显式传 `--role`，或换库 |
| `ProductionCleanupRefused` | 清理缺备份或缺已审阅 dry-run | 补齐证据再跑，不要绕过 |
| pytest exit 4 | 整个 suite 在开工前被拦下 | 正常保护，切到 `petaccess_test` 再跑 |
| E2E `globalSetup` 失败 | API 不在 `petaccess_e2e` | 检查是不是复用了旧 server（`reuseExistingServer: false`） |

### 回滚

清理有逐批还原点，见 `PRODUCTION_CLEANUP_REPORT.md` §7。
**永远先备份再动，永远按倒序回滚。**

### 已知遗留（不是事故）

- `CONFLICTING_CURRENT_RULES=2` / `DUPLICATE_CURRENT_RULE=2`：
  `青岚公园·演示` zone `645e539f` 上 `decd5051`(2026-05-15) 与 `440e419e`(2026-08-13)
  两条 current 打架。发布前就存在的 demo 语义问题 → `MANUAL_REVIEW_REQUIRED`，
  见 `PRODUCTION_DUPLICATE_CURRENT_AUDIT.md`。
- `AUDIT_TARGET_ID_UNUSABLE=4`：`audit_log` 里有 2,647 行 `target_id` 是字面量 `'None'`
  （`source` / `place` / `zone` / `jurisdiction_rule` 四类）。追加式表，不可修。
- `ORPHAN_SOURCE=2`、`RULES_WITHOUT_PLACE=17`：INFO 级，demoseed 的 zone 级规则。

---

## 9. 遗留项状态更新（PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE_R1）

上一节列的三项遗留状态已变化，操作前请以本节为准。

| 遗留项 | 旧状态 | 当前 |
|---|---|---|
| `CONFLICTING_CURRENT_RULES` / `DUPLICATE_CURRENT_RULE` | 2 / 2（`青岚公园·演示`） | **0 / 0**。取证结论：两条 `current` 均为 `CONFIRMED_DEMO_SEED`（签发方自述虚构、来源域 `demo-gov.example`、无 Evidence / 无 Candidate 血缘、`supersedes` 字段全空——从未存在替代关系）。已随 demo 场所清除。 |
| `AUDIT_TARGET_ID_UNUSABLE` | 2,647 行「不可修」 | **仍 2,647 行，但缺陷已修**。定性更正：这是**活跃缺陷**（`db.add()` 后未 `flush()` → `str(obj.id)` = `"None"`），不是纯历史。已修三层：13 处调用点补 `db.flush()`、`record_audit` 写入时断言、回归锁。历史行不回填（无确定性来源）。最后一条 `"None"` 行产生于 `2026-09-17 07:40`。 |
| `ORPHAN_SOURCE` / `RULES_WITHOUT_PLACE` | 2 / 17（INFO） | **0 / 0** |

**新增操作要点**

- 清理顺序是 `mutate → 不变式校验 → COMMIT`（`scripts/demo_closure_cleanup.py::governed_delete`）。
  不要把 `commit()` 提前：那会产生「日志说已回滚、实际已落库」的假象。
- Source 只在**无人再引用**时才删；仍被引用的会被保留并写入回执的
  `sources_retained_shared`（含引用位置）。
- 审计表只追加。清理本身也要留痕（`governance.cleanup`），历史审计永不物理删除。
- 取证统一用 `scripts/forensics_provenance.py --rule-id/--place-id`，
  不要再手写临时 SQL 去猜来源。
- 收尾检查端口：`netstat -ano | grep LISTENING | grep -E ":(8010|8011|8012) "`。
  本轮曾在 8010 上发现一个上上轮遗留的、直连生产库的无闸门实例。

**还原点**：`artifacts/integrity_final_closure/petaccess_before_integrity_closure.dump`（`pg_dump -Fc`）。
