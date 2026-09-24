# V020_GLOBAL_CODE_AUDIT.md

# v0.2.0 M1 — Master Goal §40 全量机器门禁审计

> 交付物：`docs/audit/V020_GLOBAL_CODE_AUDIT.md`（v0.2.0 M1 §65）
> 执行日期：2026-09-24 · 机器报告：`uv run python scripts/check_engineering_quality.py --json`

## 结论

工程门禁 `scripts/check_engineering_quality.py` 现覆盖 Master Goal §40 要求的
全部机器检查项。本次运行 **RESULT: PASS（0 FAIL）**，无未豁免 FAIL；REVIEW
与 WARN 均为既有、已登记（gate_exemptions.json）或需后续阶段处理的非阻塞项。

四个此前缺失的 Gate 已补齐并接入 `collect()`：

| 规则 | 实现模块 | 级别 | 状态 |
|---|---|---|---|
| silent-catch | scripts/engineering_quality_scan2.py | FAIL | PASS |
| magic-status | scripts/engineering_quality_scan2.py | FAIL | PASS |
| dead-code | scripts/engineering_quality_scan3.py | FAIL | PASS |
| duplicate-config | scripts/engineering_quality_scan3.py | FAIL | PASS |

---

## §40 检查矩阵（17 项）

| # | 规则名 | 级别 | 实现 | 状态 |
|---|---|---|---|---|
| 1 | file>300 | FAIL | engineering_quality_checks.check_size | PASS（豁免见 TD-010/TD-028 注册） |
| 2 | file>250 | WARN | engineering_quality_checks.check_size | PASS（WARN 非阻塞） |
| 3 | vue>200 | FAIL | engineering_quality_checks.check_size | PASS |
| 4 | vue>150 | WARN | engineering_quality_checks.check_size | PASS（WARN 非阻塞） |
| 5 | ts>300 | FAIL | engineering_quality_checks.check_size | PASS |
| 6 | fn>60 | REVIEW | engineering_quality_checks.py_metrics | PASS（REVIEW 非阻塞） |
| 7 | cyclo>15 / cyclo>10 | REVIEW/WARN | engineering_quality_checks.py_metrics | PASS |
| 8 | cycle | FAIL | engineering_quality_checks.dependency_cycles | PASS |
| 9 | type-escape | FAIL | engineering_quality_scan.check_type_escapes | PASS |
| 10 | todo | FAIL | engineering_quality_scan.check_todos | PASS |
| 11 | hardcoded-color | FAIL | engineering_quality_scan.check_ts_colors | PASS |
| 12 | silent-catch | FAIL | engineering_quality_scan2.check_silent_catches | PASS（8 处根因修复，见下） |
| 13 | magic-status | FAIL | engineering_quality_scan2.check_magic_status | PASS（28 处根因修复，见下） |
| 14 | dead-code | FAIL | engineering_quality_scan3.check_dead_code | PASS（7 处删除 + 130 条符号注册） |
| 15 | duplicate-config | FAIL | engineering_quality_scan3.check_duplicate_config | PASS（基线 0 命中） |
| 16 | version-drift | FAIL | scripts/check_version_drift.py（独立 gate） | 不变，非本次范围 |
| 17 | secrets-scan | FAIL | scripts/scan_secrets.py（独立 gate） | 不变，非本次范围 |

（项目同时维护独立的 `check_version_drift.py` 与 `scan_secrets.py`，未在本模块重复实现。）

---

## 本次修复清单（根因，非豁免凑 PASS）

### silent-catch（8 处，均补 debug 日志，对外行为不变）

| 文件 | 位置 | 说明 |
|---|---|---|
| core/observability.py | list_failed_jobs | `except Exception: return []` → 捕获 exc + debug 日志（计划点名项） |
| core/idempotency.py | get_cached / check_inflight | Redis 不可用时 fail-open，现记录日志 |
| core/ratelimit.py | check_rate_limit | Redis 不可用时 fail-open，现记录日志 |
| core/security.py | get_optional_user | 可选认证解析为「无用户」，现记录 debug 日志 |
| providers/storage.py | stat_object | S3Error 折叠为 None，现记录日志 |
| services/source_monitor.py | retry-after 解析 | 非法头部按无处理，现记录日志 |
| tools/reality_audit.py | _parse_dt | 非法时间戳按无处理，现记录日志 |

（providers/mock.py、observability.py record_failed_job 原本即含 debug 日志与 WHY 注释，合规。）

### magic-status（28 处，StrEnum 成员替换，行为等价）

- `RuleEffect.*`：rulespec/access_answer.py（4）、rulespec/v05_resolver.py（10）、
  rulespec/guide_dog_safety.py（5）、rulespec/v05_boundary.py（5）
- `LifecycleStatus.ACTIVE`：api/v1/places.py（2）
- `UserStatus.ACTIVE`：api/v1/auth.py（1）、core/security.py（1）
- `ObservationDisputeStatus.OPEN`：api/v1/observations.py（1）

### dead-code（7 处真实死代码删除 + 130 条按符号注册）

删除（全库无引用，删除后全量测试 938 passed）：

| 文件 | 符号 |
|---|---|
| rulespec/v05_resolver.py | `_unused`（占位 hack，仅保持 import 可引用的假函数） |
| api/v1/places.py | `current_user_dep` |
| db/base.py | `utcnow`、`SoftDeleteMixin`（无模型使用，media.py 自行内联 deleted_at） |
| rulespec/source_scope_semantics.py | `declared_scope_subjects` |
| schemas/civic.py | `RuleStatusChange` |
| schemas/reality_reports.py | `ObservationEffortOut`、`ExternalContentReferenceOut` |

注册（动态分发 / 规划词汇，逐符号，非整路径豁免）：

- **TD-028**（127 条）：FastAPI/Celery/中间件装饰器注册入口（api/v1/*、main.py、
  worker/*）——文本语料扫描看不到 `@router.get` / `@app.get` / `@celery_app.task`
  装饰器上的注册引用；
- **TD-029**（3 条）：文档化领域枚举 `StaffAwarenessState` / `FacilityPurposeState`
  与规划中的 Map adapter 工厂 `get_map_provider`，接线随对应 phase 落地。

### duplicate-config

基线 0 命中：根目录 `.env` / `.env.example` 各自单文件无重复 KEY；各
package.json / tauri.conf.json 顶层 key 唯一；root 及 services/* pyproject.toml
无重复表头 / 同表重复 key。（跨文件重复（如 .env 与 .env.example 同键）按设计
不算 duplicate：不同文件互不覆盖。）

---

## TS 死代码覆盖方式（如实标注）

本工具 **不重复实现** TS 死代码扫描：PR CI 已跑 eslint（`no-unused-vars`）与
`vue-tsc` 构建（`noUnusedLocals`），即 TS 侧机器死代码门禁。Python 侧死代码为
文本语料+符号注册（见上）。

---

## 机器报告摘录（--json，节选）

```json
{
  "fail": 0,
  "review": 60,
  "warn": 26
}
```

规则分布（violations 86 项 = 0 FAIL / 60 REVIEW / 26 WARN）：
REVIEW 全部来自既有 fn>60 / cyclo>10..15（api/v1/*、rulespec、services 中已登记
TD-001/002/003/010 的大函数）；WARN 来自 file>250、vue>150、cyclo>10，均非阻塞，
且 file>300 全部命中豁免（TD-010 计划拆分）。

## 评审后加固（code-reviewer 复核 → 已修复）

| 发现 | 严重级 | 修复 |
|---|---|---|
| dead-code 违规 dict 缺 `severity` 键，首次真实命中会 KeyError 而非 FAIL | MAJOR | `_dead_code_violations` 补 `"severity": "FAIL"` |
| `_top_level_json_keys` 字符串状态机失效（`in_str` 从未置真、`str.index` 可越界崩溃） | MAJOR | 重写为 escape 感知的小型状态机 |
| `collect()` 重复调用 check_type_escapes / check_todos | MINOR | 删除重复行 |
| TS silent-catch 只扫首个 catch、漏 `.uvue` | MINOR | 逐 catch 扫描 + 新增 `_ts_catch_body` brace 匹配 + 收 `.uvue` |
| `core/idempotency.py store()` 用 `contextlib.suppress` 静默吞错 | MINOR | 改为 try/except + debug 日志（fail-open 语义不变） |
| `ROOT =` 重复赋值 | NIT | 删除重复行 |

复核确认正确：v05_resolver 的 StrEnum 替换行为等价（StrEnum == str）、豁免条目
shape/路径匹配、新版门禁文件均 ≤300 行。修复后全量回归 938 passed。

已知边界（如实标注，非缺陷）：
- magic-status 按计划规则只覆盖 `==`/`!=`；`in ("allowed","available",…)` 这类
  属性值元组（v05_boundary.py、guide_dog_safety.py 各 1 处）不属于纯状态比较，
  且含非 RuleEffect 词（available/unknown），不替换、不豁免注册。
- TS silent-catch 为行级启发式：catch 与其 body 拆行且 body 内含注释被当作出站
  内容处理时可能漏报；当前 TS 源码树无真命中（仅 dist 命中，已被迭代器排除）。

---

## 测试

- `tests/unit/test_engineering_quality_gate.py`：25 passed（含新增 14 条：
  silent-catch ×3、magic-status ×3、dead-code ×3、duplicate-config ×3，
  沿用 make_py_tree fixture 风格）。
- 后端全量回归：`uv run pytest -q` → 938 passed, 2 skipped
  （Celery worker 就绪环境下执行；无 worker 时 3 条集成用例为环境性 Timeout）。
- `uv run ruff check scripts services/api/app tests/unit` → All checks passed。
- `uv run ruff format --check scripts services/api/app tests/unit` → 全部已格式化。

## 状态口径

PASS=实际执行成功；FAIL=必须修复（当前 0）；REVIEW/WARN=非阻塞，既有登记项。