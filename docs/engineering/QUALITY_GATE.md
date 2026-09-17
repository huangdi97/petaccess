# 质量闸门（QUALITY_GATE）

> 本文件是闸门入口。权威清单在根目录 `ENGINEERING_QUALITY_ACCEPTANCE.md` 与
> `COMPLIANCE_GATE.md`；基线在 `ENGINEERING_QUALITY_BASELINE.md`。
> 本文件规定**命令、失败语义与当前状态**，不复制上面那些文档的内容。

## 1. 命令

在本机 Git Bash 上，`PATH` 首行需要先修掉（否则 `find`/`sort` 会命中 Windows 版本）：

```bash
export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"
cd "E:/AI/宠物管理"

# Python：必须指向 petaccess_test，否则 pytest 在开工前就 exit 4
export PYTHONPATH=
export DATABASE_URL="postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess_test"
export CELERY_TASK_QUEUE=petaccess_test REDIS_URL="redis://127.0.0.1:6379/1" DB_ROLE=TEST
export HYPOTHESIS_STORAGE_DIRECTORY="$TEMP/hyp_storage"
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m ruff check services/api services/worker tests scripts
.venv/Scripts/python.exe -m ruff format --check services/api services/worker tests scripts
cd services/api && ../../.venv/Scripts/python.exe -m mypy .   # canonical 范围

# 前端
pnpm lint:fe && pnpm format:check:fe
pnpm admin:build
cd apps/client-h5 && env -u VITE_API_BASE pnpm exec vite build   # 走代理，E2E/视觉共用一份

# E2E / 视觉（Playwright 会自己拉起隔离库与 API）
pnpm exec playwright test
pnpm exec playwright test --config playwright.visual.config.ts
```

`mypy` 的全称量 repo 有历史错误（集中在旧脚本）；canonical 门禁范围是 `services/api`。
新增脚本必须自查为 0 错误，不得把旧债扩大。

## 1.1 a11y / UI 采集需要手工拉起三件套

它们不像 Playwright 那样会自己建库，需要先起 VISUAL 角色的 API：

```bash
cd services/api && PYTHONUNBUFFERED=1 PYTHONPATH= ../../.venv/Scripts/python.exe \
  ../../scripts/dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8011 &
cd apps/client-h5 && VITE_API_PROXY="http://127.0.0.1:8011" pnpm exec vite preview --host 127.0.0.1 --port 5175 &
cd apps/admin    && VITE_API_PROXY="http://127.0.0.1:8011" pnpm exec vite --host 127.0.0.1 --port 5173 &

node scripts/a11y_audit.mjs --json artifacts/a11y_audit.json
node scripts/ui_capture.mjs
```

跑完**逐个端口确认关掉**（`8011` / `5173` / `5175`）。
遗留的 dev 服务是本轮发现的真实泄漏源之一。

## 2. 失败语义

| 状态 | 含义 |
|---|---|
| `PASS` | 实际执行且成功 |
| `FAIL` | 实际执行且失败——必须修复或如实记录 blocker |
| `BLOCKED_EXTERNAL` | 外部条件缺失（Docker 未起、无网络、无 token） |
| `NOT_RUN` | 没跑，不得按 PASS 计 |

**不得**用「上次跑过」代替本轮结果；不得引用历史数字（例如 `517 passed`）作为本轮证据。

## 3. 发布相关闸门（本轮新增/加固）

| 闸门 | 判定 |
|---|---|
| 人类签署完整 | 37 行三字段齐备、reviewer 唯一、时间戳带时区 |
| 授权来源 | 计划只读 `final_decision`；`proposed_decision` 不授权 |
| 发布闸门真实执行 | `PREPUBLISH_GATE_RAN = True`；`NOT_RUN` 不算 PASS |
| 例外一等公民 | carve-out 计划为 `CREATE_RULE_EXCEPTION`，非第二条 `AccessRule` |
| base 先于 exception | 依赖闭包成立 |
| 层内绑定 | `CROSS_LAYER_EXCEPTION = 0`，且写入边界拒绝跨层 |
| HOLD / REJECTED 排他 | `HOLD_PUBLISHABLE = 0`、`REJECTED_PUBLISHABLE = 0` |
| 计划自检 | `SELF_SUPERSEDE = 0`、`DUPLICATE_PLAN = 0`、`SUPERSESSION_CYCLE = 0` |
| dry-run 只读 | 子进程级前后行数一致，`DRY_RUN_ZERO_DB_MUTATION = True` |
| 签署不可变 | 生成器/formatter 不得改动签署；非签署字段对签署前基线 diff = 0 |

## 3.1 数据隔离闸门（PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1）

| 闸门 | 判定 | 证明 |
| --- | --- | --- |
| 角色唯一权威 | 服务端 `current_database()` 探针，非 URL 解析 | `app/db/safety.py` |
| 未知库名拒绝 | `UnknownDatabaseRefused`，不静默放行 | `tests/isolation` |
| 六种负载 fail-closed | 指向 `petaccess` 必须全部失败 | `tests/isolation/test_production_fail_closed.py`（18 passed） |
| pytest 开工前拒绝 | 非 TEST 角色 → exit 4 | `tests/conftest.py::pytest_sessionstart` |
| 全量 QA 零改动 | `PRODUCTION_DB_ROW_DIFF = 0` 且 `SEMANTIC_DIFF = 0` | `PROD_FINGERPRINT_C` vs `_D` |
| 夹具零残留 | `TEST_FIXTURE_{PLACE,SOURCE}_IN_PRODUCTION = 0`、`TEST_ACCOUNT_IN_PRODUCTION = 0` | `production_integrity_after_batch02.json` |
| UNKNOWN 不自动删除 | 3 个 UNKNOWN 场所仍在库内 | `PRODUCTION_CLEANUP_REPORT.md` §6 |

## 4. 当前状态（POST_SIGNATURE_PUBLISHER_CLOSURE_R1）

见 `docs/governance/POST_SIGNATURE_PUBLISHER_CLOSURE.md` 的测量表。
该表里的数字是**当次执行**的结果，其 `PREPUBLISH_*` 部分与日期相关（freshness）。

`PILOT_REVIEW_PUBLISH_GATE` 仍为 `NOT_RUN`：它还需要真实首批发布、resolver 复核、
Evidence/Source 复核、rollback、supersession、watch、audit。

---

## 5. 当前状态（PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE_R1）

测量表与全部证据见 `docs/governance/PRODUCTION_INTEGRITY_LIMITATION_FINAL_CLOSURE.md` §8–§10。
下列数字是**本轮当次执行**的结果，不得引用更早轮次的值。

| 项 | 结果 |
|---|---|
| pytest | 643 passed / 2 skipped |
| ruff check / ruff format --check | PASS / PASS（195 files） |
| mypy（canonical 范围） | PASS（79 files） |
| ESLint / Prettier | PASS / PASS |
| H5 build / Admin build | PASS / PASS |
| E2E | 18 passed |
| Visual | 47 passed |
| a11y | 0 issues |
| Publisher critical ×3 | PASS（`AUDIT_LINKAGE = PASS`） |
| DB isolation proof | 18 passed |
| 生产库 QA 前后差异 | `ROW_DIFF = 0`、`SEMANTIC_DIFF = 0` |

```
PRODUCTION_DATA_ISOLATION_GATE = PASS
PRODUCTION_INTEGRITY_GATE      = PASS
PRODUCTION_INTEGRITY_CRITICAL  = 0
PRODUCTION_INTEGRITY_HIGH      = 0
PRODUCTION_INTEGRITY_MEDIUM    = 1   (AUDIT_TARGET_ID_UNUSABLE，历史行，已解释)
30_50_PLACE_EXPANSION          = READY_TO_START   # 未启动
SEMANTIC_REMODEL_ISSUE         = OPEN
```

**新增的闸门命令**

```bash
# 审计事件契约与回填标签
PYTHONPATH= .venv/Scripts/python.exe -m pytest tests/unit/test_audit_event_contract.py -q

# §19/§20/§24 生产完整性锁（需要 TEST 角色库）
PYTHONPATH= DATABASE_URL="postgresql+psycopg://petaccess:petaccess_dev_only@127.0.0.1:5432/petaccess_test" \
  DB_ROLE=TEST .venv/Scripts/python.exe -m pytest tests/integration/test_production_integrity_closure.py -q

# a11y（失败语义已收紧：页面没渲染出来标 NA 并以失败退出，不算绿）
node scripts/a11y_audit.mjs --json artifacts/a11y_audit.json
```

**a11y 的失败语义变更**：`TOTAL issues: 0` 只有在页面确实渲染出来时才算通过。
交互元素少于 3 个的页面会被标 `NA` 并让进程退出码非 0——
在空文档上统计出 0 issues 是最不能接受的一种「绿」。
