# TEST_COVERAGE_REPORT.md

日期：2026-09-13（PART A · A5）· 工具：pytest-cov 7.1 / coverage 7.16（branch 模式）
命令：`uv run pytest -q --cov=app --cov-branch --cov-report=term:skip-covered --cov-report=json:coverage.json`

## 总量

| 指标 | 值 |
|---|---|
| 测试总数 | **207 passed**（184 基线 + 17 quality-baseline 单测 + 5 verifications 集成 + 1 并发竞态） |
| 语句覆盖（全 app） | **82%**（4905 stmts / 768 missed） |
| 分支覆盖 | 已开启（`--cov-branch`），明细见 `coverage.json` |
| 完全覆盖文件 | 34 个（skip-covered 跳过显示） |

## 核心模块（A5 目标：尽量 ≥90%）

| 模块 | 覆盖率 | 判定 |
|---|---|---|
| `rulespec/v05_resolver.py`（RuleResolver） | **97%** | 达标 |
| `rulespec/v05_boundary.py`（BoundaryMatcher） | **100%** | 达标（本轮新增 6 个 stance×value 组合测试） |
| `services/candidate_service.py`（Candidate 状态机+发布闸门） | **100%** | 达标（本轮补 publish 4 个守卫分支 + note 路径） |
| `services/evidence_service.py`（Evidence pipeline） | **95%** | 达标 |
| `services/source_monitor.py`（SourceMonitor） | **95%**（原 76%） | 达标（本轮补 dns/redirect/http_error/oversize/network/check_monitor 全分支） |
| `services/answerability.py` | 93% | 达标 |
| `providers/ai_guard.py` | 98% | 达标 |
| `rulespec/evaluator.py`（v0.3 evaluator） | 86% | 合理解释：GOAL #7 十条矩阵 + 40 类对抗 fixtures 已锁定全部语义分支；未覆盖行为错误兜底与罕见组合 |
| `tools/reality_audit.py` | 86% | 合理解释：12 专项测试覆盖引擎主链与报告输出；尾部为 CLI 打印路径 |

## 领域/服务层 vs 接口层

- **domain / services / providers**（业务核心）：全部 ≥86%，核心五个模块 93–100% → 满足
  "domain/services line ≥85%"。
- **v0.3 时代 API 路由**（places 48% / disputes 44% / verifications 29%→本轮补齐 / admin 53% /
  rules 56% / regulations 57%）：接口层偏低。解释：这些流程的**业务语义**由
  integration（test_api / test_operator_contribution）与 Playwright E2E 在 HTTP 层真实验证；
  未覆盖的多为错误分支与分页边角。本轮发现并修复了一个真实缺口：verifications.py 的
  HTTP 流程**完全无测试**（test_api.py docstring 声称覆盖但从未写过），已补 5 个集成测试
  （创建/列表/404/401/幂等重放/限流 429），覆盖率 29%→100%。
- `db/seed.py` 0%：seed 是演示脚本，正确性以实际运行验证（每轮迁移后 `--demo` 复跑 PASS），
  不纳入单测覆盖目标。
- `worker/tasks.py` 46%：Celery 任务经 E2E-C 真跑（通知幂等）+ TTL 任务集成测试覆盖主链；
  未覆盖为分支边角。

## 本轮新增测试

| 文件 | 数量 | 内容 |
|---|---|---|
| `tests/unit/test_quality_baseline.py` | 18 | BoundaryMatcher 全 stance×value 矩阵；SourceMonitor 7 类守卫与 check_monitor 三态；publish 4 守卫+成功路径；**双 reviewer 并发发布仅一胜**（A12） |
| `tests/integration/test_verifications.py` | 5 | 核验 HTTP 全流程：创建+列表、404、401、幂等重放、限流 429 |

## 不变量（A4 十条）测试映射（全部 PASS）

| 不变量 | 测试 |
|---|---|
| UNKNOWN 不自动变 MATCH | `test_v05_adversarial`（边界 UNKNOWN）+ `test_quality_baseline`（boundary unknown/未知 stance） |
| 未发布 RuleCandidate 不进 EffectiveRuleSet | `test_v05_track_b` 状态机 + resolver 只认 current 规则（`test_v05_resolver`） |
| 未发布 ObservationCandidate 不成正式 Claim | `test_v05_evidence` + API 层逐字节不变测试 |
| Observation 不改 normative resolver | evaluator/resolver 签名无观察参数（属性测试锁定） |
| expired temporary rule 不 current | `test_v05_adversarial` 时间窗类 |
| superseded rule 不 current | `test_evaluator` GOAL#7 矩阵 |
| service_dog 与 ordinary_pet 隔离 | `test_v05_adversarial` 三向隔离 |
| external provider id ≠ Place 主键 | 模型 FK 结构 + `test_v05_track_b`（ExternalPlaceRef 仅引用） |
| stale ≠ invalid | freshness H39 对抗 fixture |
| mandatory legal constraint 不被低层覆盖 | `test_v05_resolver` 法定地板 |

## 结论

- 覆盖目标：核心五模块全部 ≥93%（目标 ≥90%）——**达标**。
- 全域 domain/services ≥85% —— **达标**。
- 接口层与 worker 覆盖偏低有明确解释与登记（见 `TECH_DEBT_REGISTER.md` TD-03）。
- 无任何为覆盖率而写、不断言行为的测试；新增测试均断言语义（verdict/reason/code/状态）。
