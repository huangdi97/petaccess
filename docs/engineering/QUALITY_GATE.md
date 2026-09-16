# 质量闸门（QUALITY_GATE）

> 本文件是闸门入口。权威清单在根目录 `ENGINEERING_QUALITY_ACCEPTANCE.md` 与
> `COMPLIANCE_GATE.md`；基线在 `ENGINEERING_QUALITY_BASELINE.md`。
> 本文件规定**命令、失败语义与当前状态**，不复制上面那些文档的内容。

## 1. 命令

```powershell
# Python
$env:PYTHONPATH=""; uv run pytest -q --basetemp=$env:TEMP\petaccess-pytest
uv run ruff check services/api services/worker tests scripts
uv run ruff format --check services/api services/worker tests scripts
cd services/api; uv run mypy .            # canonical 范围：services/api/app

# 前端
pnpm lint:fe; pnpm format:check:fe
$env:VITE_API_BASE="http://127.0.0.1:8010/api/v1"; cd apps/client-h5; pnpm exec vite build
Remove-Item Env:\VITE_API_BASE
cd apps/admin; pnpm exec vite build

# E2E / 视觉 / a11y（Playwright 会自己拉起 API 与 preview）
pnpm exec playwright test
node scripts/ui_capture.mjs
node scripts/a11y_audit.mjs
```

`mypy` 的全称量 repo 有历史错误（集中在旧脚本）；canonical 门禁范围是 `services/api/app`。
新增脚本必须自查为 0 错误，不得把旧债扩大。

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

## 4. 当前状态（POST_SIGNATURE_PUBLISHER_CLOSURE_R1）

见 `docs/governance/POST_SIGNATURE_PUBLISHER_CLOSURE.md` 的测量表。
该表里的数字是**当次执行**的结果，其 `PREPUBLISH_*` 部分与日期相关（freshness）。

`PILOT_REVIEW_PUBLISH_GATE` 仍为 `NOT_RUN`：它还需要真实首批发布、resolver 复核、
Evidence/Source 复核、rollback、supersession、watch、audit。
