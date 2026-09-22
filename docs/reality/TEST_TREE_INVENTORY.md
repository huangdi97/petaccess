# TEST TREE INVENTORY & REGRESSION BASELINE — v0.9-R1 Reality Layer

> 文件：`docs/reality/TEST_TREE_INVENTORY.md`
> 生成：2026-09-22（UTC+8 会话，v0.9-R1 六阶段推进）
> 用途：AC6 —— 盘点完整测试树，明确区分 CURRENT SESSION FULL REGRESSION 与
> HISTORICAL BASELINE；每个数字标注来源与是否本会话实测。

## 0. 一句话结论

- **HISTORICAL BASELINE**：V09 审计记录 **825 passed / 2 skipped / 0 failed**
  （出处：`docs/status/V09_CURRENT_REALITY_AUDIT.md` §5.8，2026-09-21 实测，
  隔离 TEST 库 + Celery worker 下运行）—— 该基线发生在 Reality migration
  `2c7ea6ca8e30` 落地之前的 Wave02 收口轮次。
- **CURRENT SESSION（本会话实测）**：
  - 非 DB 可执行子集（`services/api/tests/`）：**75 passed / 0 failed**
    （`uv run pytest tests/ -q`，cwd=`services/api`，1.45s）
  - ruff check `.`：**All checks passed!**
  - ruff format `--check`（lint.sh scope）：**277 files already formatted**
  - mypy `services/api`（`--python-version 3.12`，与运行时一致）：
    **Success: no issues found in 96 source files**
  - 全量 root `tests/`（unit+integration+contract+isolation+e2e+visual）：
    **NOT_RUN this session** —— root `tests/conftest.py` 是 fail-closed
    （`pytest_sessionstart` 强制 TEST-role DB，DB 不可达即 exit 4），
    本会话 Docker 不可用（BLOCKED_EXTERNAL）→ 无法在隔离 TEST 库上运行。

## 1. 测试树全貌（静态盘点，2026-09-22）

pytest 配置（`pyproject.toml`）：`testpaths = ["tests", "services/api/tests"]`，
`asyncio_mode = "auto"`，注册 markers：`integration`（需要 TEST DB）、`e2e`
（需要运行中的 API server）。

### 1.1 `services/api/tests/`（非 DB 纯逻辑，本会话可跑）

| 文件 | 用例数 | 内容 |
|---|---|---|
| `test_evaluator.py` | 15 | 确定性 evaluator 单测 |
| `test_reality_summary.py` | 13 | RealitySummary 六状态 + freshness + 红线 |
| `test_rule_reality_divergence.py` | 37 | AC8 六 Divergence 状态 + 红线（新增，本会话） |
| `test_coexistence_snapshot.py` | 10 | AC9 统一快照聚合（新增，本会话） |
| **合计** | **75** | 本会话实测全过 |

### 1.2 `tests/unit/`（root，无需 DB 语义但受 conftest 门禁管辖）

| 文件 | 用例数 |
|---|---|
| test_access_answer.py | 12 |
| test_adr030_holder_scope.py | 17 |
| test_animal_scope.py | 30 |
| test_audit_event_contract.py | 10 |
| test_broad_term_split.py | 21 |
| test_config_validation.py | 4 |
| test_design_tokens.py | 10 |
| test_dev_api_psycopg_url.py | 5 |
| test_domain_invariants.py | 24 |
| test_governance_baseline.py | 11 |
| test_human_review_packet_final.py | 35 |
| test_idempotency_keys.py | 6 |
| test_jurisdiction_proviso.py | 21 |
| test_mandatory_level.py | 22 |
| test_place_geo_backfill.py | 8 |
| test_property_invariants.py | 6 |
| test_publish_batch_selection.py | 23 |
| test_publish_layer_integrity.py | 5 |
| test_publish_plan.py | 34 |
| test_publish_preflight_crosscheck.py | 11 |
| test_publish_register_resolution.py | 6 |
| test_publish_scope_fidelity.py | 10 |
| test_quality_baseline.py | 18 |
| test_quality_metrics.py | 17 |
| test_reality_audit.py | 12 |
| test_real_world_regression.py | 4 |
| test_rule_exceptions.py | 14 |
| test_rule_exception_binding.py | 15 |
| test_scope_remodel_r2_candidates.py | 4 |
| test_superseded_semantics_and_evidence_acceptance.py | 23 |
| test_temporal_invariants.py | 13 |
| test_ui_states.py | 8 |
| test_v05_adversarial.py | 41 |
| test_v05_evidence.py | 22 |
| test_v05_properties.py | 8 |
| test_v05_resolver.py | 13 |
| test_v05_track_b.py | 12 |
| test_wave01_monitor_matrix.py | 13 |
| test_wave01_semantic_bridge.py | 28 |
| **小计** | **~596** |

### 1.3 `tests/integration/`（需要真实 TEST DB，本会话 NOT_RUN）

21 个文件：test_access_answer_api(7)、test_api(11)、test_boundary_api(7)、
test_evidence_api(11)、test_mandatory_level(4)、test_media(5)、
test_operator_contribution(3)、test_place_extras(5)、test_place_search_aliases(9)、
test_production_integrity_closure(5)、test_publish_atomicity(4)、
test_publish_exception(15)、test_reality_audit_api(3)、
test_regulations_contract(6)、test_rollback_l1(5)、test_rule_exceptions(6)、
test_v05_e2e(4)、test_verifications(5)、test_versioning_supersession(5)、
test_watch_notify_idempotency(2)、test_wave01_freshness_watch(11) → **~133 用例**，
全部 `pytest.mark.integration`。

### 1.4 其他 root 测试

- `tests/contract/`：test_ai_guard(7)、test_rule_spec_contract(2)、
  test_tencent_map_provider(13) → **22 用例**
- `tests/isolation/`：test_production_fail_closed(11) → **11 用例**
- `tests/e2e/`、`tests/visual/`、`tests/fixtures/`：目录存在；e2e/visual 由
  Playwright / visual 脚本驱动（不在 pytest testpaths 默认收集，或为辅助）。

### 1.5 Playwright

- `playwright.config.ts` + `playwright.visual.config.ts` 存在；V09 基线：
  **16 passed / 2 failed**（2 个为 AccessAnswer 迁移后的既有 E2E 期望不一致，
  `ENGINEERING OPEN`，出处 V09 §5.9）。
- 本会话：**NOT_RUN**（需要 API server + E2E 库 + Playwright 浏览器，属 DB/
  容器相关链路）。

## 2. CURRENT SESSION FULL REGRESSION（本会话真实执行）

| 门禁 | 命令 | 结果 | 备注 |
|---|---|---|---|
| 非 DB pytest | `cd services/api && uv run pytest tests/ -q` | **75 passed / 0 failed**（1.45s） | 28 存量 + 47 新增（Divergence 37 + Snapshot 10） |
| ruff check | `uv run ruff check .` | **All checks passed!** | 修复 6 处既有 lint（wave02 脚本 3 + migration 1 + 新文件 2） |
| ruff format | `uv run ruff format --check services/api services/worker tests scripts` | **277 files already formatted** | 9 个既有文件被 reformat（6 in-scope + migration） |
| mypy | `uv run mypy --python-version 3.12 services/api` | **Success: no issues found in 96 source files** | 运行时 Python 3.12.9 |
| root pytest 全量 | `uv run pytest -q`（root） | **REFUSED (exit 4)** | conftest fail-closed：DB 不可达，如实 NOT_RUN |

### 2.1 全量 root pytest 为什么 NOT_RUN（而非 FAIL）

`tests/conftest.py` 的 `pytest_sessionstart` 在**任何测试执行前**强制：
`SELECT current_database()` 必须是 TEST-role（`petaccess_test*`）；DB 不可达
即 `pytest.exit(returncode=4)`。这是项目刻意设计（拒绝触碰生产库），不是缺陷。
本会话 Docker daemon 不可达 → 无 PostgreSQL → 无法 provision TEST 库 →
全量 suite 无法运行。这不属于"测试失败"，标记为 `NOT_RUN`（DB 依赖未满足）。

## 3. HISTORICAL BASELINE（出处与数字）

| 条目 | 值 | 出处 |
|---|---|---|
| pytest 全量 | **825 passed / 2 skipped / 0 failed**（70.66s） | `docs/status/V09_CURRENT_REALITY_AUDIT.md` §5.8（2026-09-21 实测，隔离 TEST 库 + Celery worker） |
| ruff | All checks passed | 同上 |
| mypy | Success: no issues found in 87 source files | 同上（当时 87 files） |
| Playwright E2E | 16 passed / 2 failed | 同上 §5.9 |
| 更早基线（ENV-01 解除时） | 319 passed / 0 failed（2026-09-14）；Wave01 收口基线与之相符 | `BLOCKERS.md` ENV-01 段落 |

> 差异说明：HISTORICAL 825 与 CURRENT 非 DB 75 不可直接比较 —— 825 是含 DB
> integration 的全量；75 是本次无 DB 环境下真实可执行的子集。两者都是真实
> 数字，用途不同。Reality migration `2c7ea6ca8e30` 之后的全量回归必须等
> Docker 恢复后在隔离 TEST 库上重跑（AC2–AC5 解除后立即执行）。

## 4. 新增测试（本会话，AC7/AC8/AC9）

| 文件 | 数量 | 钉死的语义 |
|---|---|---|
| `services/api/tests/test_rule_reality_divergence.py` | 37 | 六 Divergence 状态全可达；笛卡尔积完备且确定性；NO_RECENT_RECORD ≠ 没有动物；unknown 规则永不变允许；DISPUTED 降级 INSUFFICIENT_DATA；Divergence 只描述不改写 |
| `services/api/tests/test_coexistence_snapshot.py` | 10 | 六合一快照；divergence 从两半推导；to_plain JSON 安全；不可变；evidence_summary 双面证据 |

## 5. 下一步（Docker 恢复后）

1. `docker compose up -d` → 确认 postgres/redis healthy；
2. `uv run python scripts/isolated_db.py --role TEST --reset`；
3. `DATABASE_URL=…petaccess_test uv run pytest -q`（root 全量，预期向 825+
   回归并叠加 Reality 相关新用例）；
4. `alembic upgrade head` 真实验证（见 `REALITY_DB_MIGRATION_VERIFICATION.md`）；
5. Playwright 全量重跑并记录。