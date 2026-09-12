# ENGINEERING_QUALITY_FINAL_REPORT.md

日期：2026-09-13 · PART A（ENGINEERING-QUALITY-FREEZE）终审报告
性质声明：只记录实际执行过的验证；未执行项如实标注。状态词汇遵循 AGENTS.md
（PASS = 实际执行成功 / BLOCKED_EXTERNAL / NOT_RUN / PARTIAL）。

## 1. 范围与基线

- 起点：HEAD `2c9b547`（v0.5 本地 RC 收口后），工作树无 modified/staged，
  保护补丁 `quality_phase_pre_takeover*.patch`（0 字节）。
- 控制文件：`QUALITY_THEN_REAL_DATA_GOAL.md`（要求）、`ENGINEERING_QUALITY_BASELINE.md`
  （起点与 9 项已知缺口 G1–G9）、`ENGINEERING_QUALITY_ACCEPTANCE.md`（Q01–Q28 逐项）。
- 本报告结论：PART A **PASS**，满足进入 PART B 的 Quality Gate。

## 2. Gate 结果总览（真实命令）

| Gate | 结果 | 证据 |
|---|---|---|
| format（ruff format --check） | **PASS** — 147 files already formatted | `uv run ruff format --check .` |
| lint（ruff check） | **PASS** — All checks passed | `uv run ruff check .` |
| typecheck（mypy） | **PASS** — 72 source files, no issues | `uv run mypy services/api/app` |
| backend tests | **PASS** — **207 passed**（基线 184 不回退 + 新增 23） | `uv run pytest -q --cov=app --cov-branch …` |
| property tests | **PASS** — 含于全量（hypothesis：`test_v05_properties` 等） | 同上 |
| frontend lint/format | **PASS** — ESLint 0 error；Prettier all clean（本轮首次引入并实跑） | `pnpm exec eslint .` / `prettier --check .` |
| frontend typecheck+build | **PASS** — Admin ✓ 1.90s / H5 ✓ 1.36s（vue-tsc strict，`strict:true` 三处 tsconfig） | `pnpm --filter … build` ×2 轮 |
| generated client ≡ OpenAPI | **PASS**（修复后） — 实查提交版缺全部 v0.5 端点 → 重新生成 → 双端 build 复验 | `pnpm client:gen` + `git diff` |
| E2E（Playwright） | **PASS** — 7/7（5 v0.3 旅程 + 2 v0.5 边界/可解释匹配） | `playwright test --output=playwright-out` |
| coverage | **PASS** — 总量 82%（branch 开启）；核心五模块 93–100%（resolver 97 / boundary 100 / candidate 100 / evidence 95 / monitor 95）；接口层缺口有解释并登记 TD-03 | `coverage.json` + `TEST_COVERAGE_REPORT.md` |
| migration | **PASS** — down→up→down→up 双循环（populated/fresh/seeded 三态）+ seed 复跑 | `MIGRATION_AUDIT.md` §本日验证 |
| DB integrity | **PASS** — 39 表/66 FK/53 unique/8 check/100 索引；GIST+trgm+队列/审计索引实查；EXPLAIN ANALYZE | `DB_INTEGRITY_REPORT.md` |
| security audit | **PASS** — pip-audit / pnpm audit 0 漏洞；secret scan 0 命中；RBAC/IDOR/限流/CORS/幂等/上传/SSRF 全项核查；**2 项修复**（JWT secret 30→49B、publish 并发 CAS） | `SECURITY_AUDIT.md` |
| privacy inventory | **PASS** — 7 项中 6 项代码/测试实证；redaction 缺口如实登记（TD-05）并定 PART B 约束 | `PRIVACY_DATA_INVENTORY.md` |
| backup/restore | **PASS** — 真实演练：dump 109KB → fresh restore → marker/places/geometry 比对一致；MinIO 122 对象抽检可读 | `BACKUP_RESTORE_EVIDENCE.md` |
| performance baseline | **PASS** — 9 端点 50 次实测，p95 ≤ 28ms；EXPLAIN 佐证索引路径 | `PERFORMANCE_BASELINE.md` |
| critical concurrency | **PASS** — 双 reviewer 并发发布仅一胜（CAS + 测试）；duplicate publish/notification 由状态机终态 + E2E-C 幂等锁定 | `test_concurrent_publish_single_winner` |
| reliability | **PASS** — 有界重试（max_retries=3+backoff）、幂等重放实测、failed-job 可见、monitor 失败路径测试 | `worker/tasks.py` + 新增 monitor 测试 |
| dead code / TODO | **PASS** — 代码 0 TODO/FIXME；4 处 pass/NotImplemented 全合法；6 处前端死代码已删；遗留 8 项登记 | `TECH_DEBT_REGISTER.md` |
| docs reproducible | **PASS** — 16 步全链实跑；README 过时计数已更正 | `REPRODUCIBILITY_REPORT.md` |

## 3. 本轮真实修复（不是纸面工作）

1. **并发布会重复创建规则**（真实缺陷）：`candidate_service.publish()` 先读后写，
   两个 reviewer 同时发布同一 APPROVED 候选会产生两条 AccessRule。改为原子 CAS
   （`UPDATE … WHERE review_status='APPROVED'`，rowcount≠1 → `candidate_already_published`
   整体回滚），并发测试锁定。
2. **verifications HTTP 层零测试**（文档谎报）：`test_api.py` docstring 声称覆盖
   verifications，实际从未有测试。补 5 个集成测试（创建/列表/404/401/幂等/限流），
   模块覆盖 29%→100%。
3. **生成 client 落后 OpenAPI 一个版本**：提交版 schema.d.ts 无任何 v0.5 端点。
   重新生成并复验双端 build。
4. **dev JWT secret 30 字节**（RFC 7518 告警 60 条）：加长至 49 字节，警告归零。
5. **前端工具链缺失**（G1）：引入 ESLint 10 + Prettier 并全量实跑；删除 6 处死代码；
   Shell→AppShell 重命名；`pnpm-workspace.yaml` 占位符修复。
6. **核心模块覆盖缺口**（G2/G9 相关）：SourceMonitor 76→95%、BoundaryMatcher 78→100%、
   candidate_service 86→100%，新增 18 个语义断言测试。
7. 工具新增：`pytest-cov`（coverage 7.16）、`scripts/perf_baseline.py` 可复跑探针。

## 4. A3 E2E 七链路映射（全部有真实测试）

| 链路 | 测试 | 状态 |
|---|---|---|
| 1 pet→place→rule result | Playwright #2/#5 + `test_evaluate_cafe_zones`/`test_unknown_weight_is_unknown` | PASS |
| 2 BoundaryProfile→explainable match | Playwright #6/#7 + boundary API 集成 7 测试 | PASS |
| 3 signage→MinIO→OCR→bundle→candidate→review→rule→client | E2E-A（`test_v05_e2e`）+ `test_media.py` 5 测试 + Playwright #5 | PASS |
| 4 verified operator→template/policy→resolver→client | E2E-B | PASS |
| 5 source changed→monitor→evidence→candidate→supersede→watch | E2E-C（hash change→通知幂等） | PASS |
| 6 external lead→bundle→candidates→review，不得直接 publish | E2E-D（`lead_only_source_not_publishable` 闸门 + 许可补齐对照组） | PASS |
| 7 Entrance/AccessPath/Amenity 显示 | v05 读端点集成（entrances/paths/amenities 分页）+ Admin v0.5 视图 + SpatialExtrasView | PASS |

## 5. Quality Gate 判定（A17 清单逐项）

format ✓ / lint ✓ / typecheck ✓ / backend tests ✓ / frontend tests（typecheck+build+lint 全绿；
无独立前端单测框架——**如实标注**，UI 逻辑经 Playwright 7 旅程真实验证）✓ / E2E ✓ /
property ✓ / coverage 达标且有解释 ✓ / migration ✓ / security ✓ / dependency ✓ /
privacy ✓ / backup/restore ✓ / performance ✓ / concurrency ✓ / 无 unexplained TODO ✓ /
docs reproducible ✓

**PART A = PASS。** 授权进入 PART B（证据优先真实数据先导，先 10 Place）。

## 6. Git 收口

- 本阶段改动将以 `release: engineering-quality-freeze` 本地提交，并打本地 tag
  `v0.5-quality-freeze`。
- 无 remote，不 push（遵守"无授权不伪造 push"）。

## 7. 未真实验证项（诚实清单，均 BLOCKED_EXTERNAL）

- uni-app x 五端编译（B-01）、真实地图 live smoke（B-04）、真实 AI/OCR live smoke（B-05）、
  OAuth/生产部署（B-06/B-07）。以上不阻塞本地 Quality Gate（与 V05_FINAL_REPORT §11 一致）。
