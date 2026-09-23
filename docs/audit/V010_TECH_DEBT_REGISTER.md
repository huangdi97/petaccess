# V010_TECH_DEBT_REGISTER.md

# v0.1.0 Phase A — 技术债登记册

> 来源:docs/audit/V010_REPOSITORY_BASELINE.md(2026-09-23 只读盘点)
> 状态:OPEN(待修)/ IN_PROGRESS / DONE / WONTFIX(记录原因)
> 每项含 ID / severity / file / problem / risk / fix / verification / status

Severity:CRITICAL(发布阻塞) / HIGH(发布前必修) / MEDIUM(应修) / LOW(可缓)

---

## 后端(services/api)

| ID | Sev | File | Problem | Risk | Fix | Verification | Status |
|---|---|---|---|---|---|---|---|
| TD-001 | HIGH | app/api/v1/v05.py(3103 行) | God module,远超 300 行硬上限;HTTP/domain/规则加载混杂 | 回归面大、无法单元化测试;gate 必 FAIL | 按职责拆分:路由薄层 + service/domain 拆出;_load_layered_rules 等大函数拆分 | 文件 <300 行;ruff/mypy/pytest 全绿;gate FAIL→PASS | OPEN |
| TD-002 | HIGH | app/rulespec/v05_resolver.py:resolve(467 行,McCabe 109) | 单函数复杂度过高,核心 AI 判定链路 | 判定逻辑无法审查/测试;任何改动高风险 | 拆分为策略链/小函数,保持行为不变(behavior-preserving) | resolve 拆分后单函数 ≤60 行;golden fixtures 回归 | OPEN |
| TD-003 | HIGH | app/db/seed.py(1494 行,run_demo_seed 1378 行) | 种子数据 God function;含 demo 场所 | v0.1.0 release 禁止 demo seed 进 release path;seed 与 release 数据路径需隔离 | 拆 seed 数据为 fixture/JSON;release 路径不加载 seed;标记 dev/test-only | release 构建不含 seed 数据;文档隔离声明 | OPEN |
| TD-004 | HIGH | app/services/evidence_service.py(649 行,7 处 type:ignore) | 证据域核心业务类型逃逸 + 文件超标 | 证据判定无类型校验;编译期错误变运行时错误 | 补类型模型消除 ignore;拆分服务职责 | type:ignore→0;mypy 全绿 | OPEN |
| TD-005 | MEDIUM | app/core/idempotency.py(2 处 silent catch) | 幂等键清理失败被静默吸收 | 幂等边界失效且无观测,违反规范 §16 | 显式 domain error + 结构化日志;失败可重试 | silent catch→0;幂等回归测试 | OPEN |
| TD-006 | MEDIUM | app/core/security.py(1 处 silent catch) | 安全边界错误被静默 | 安全失败不可观测 | 显式日志 + fail 语义;安全回归测试 | 测试覆盖安全失败路径 | OPEN |
| TD-007 | MEDIUM | app/worker/tasks.py(5 处宽捕获) | 队列任务宽捕获,重试语义脆弱 | 任务失败状态不可信 | 精确异常 + Celery 重试策略显式化 | 任务失败测试覆盖 | OPEN |
| TD-008 | MEDIUM | app/db/safety.py(651 行,7 处 print) | 安全敏感模块用 print 而非结构化日志;文件超标 | 日志不可检索、无级别;gate 超标 | 换 logging;拆分模块;保留安全不变量注释 | logging 替换;文件 <300 | OPEN |
| TD-009 | MEDIUM | app 全域 49 处 Any 使用(非 import) | 类型纪律违反;coexistence_snapshot 13、access_answer 11 最集中 | 判定链路无类型保护 | 逐文件补 typed model;unjustified Any → 0 | mypy strict 扫描 Any 归零 | OPEN |
| TD-010 | MEDIUM | app 24 个文件 >300 行(含 enums.py 848、models/v05.py 499) | 批量规模超标 | 维护成本高、难测试 | 按职责拆分(先处理 gate 必需的最小集) | gate FAIL→PASS | OPEN |
| TD-011 | MEDIUM | services/api/tests 4 文件与根 tests/ 疑似重复职责 | 测试双目录,职责不清 | 测试漂移、维护混乱 | 合并到根 tests/ 或明确边界;删除重复 | 测试全量 PASS;无重复测试名 | OPEN |
| TD-012 | LOW | app/config.py 内嵌 dev JWT/DB/S3 默认值 | 生产环境缺显式 fail-fast | 生产误用 dev 凭据 | 生产模式(AAPP_ENV=production)对敏感配置强制显式提供,缺失即启动失败 | 生产模式启动测试 | OPEN |
| TD-013 | LOW | migrations/versions/e9f2c1d4a5b6_*.py 带 UTF-8 BOM | 裸 utf-8 解析报 SyntaxError,工具链需 utf-8-sig | 部分 ast/工具扫描失败 | 去除 BOM(保留内容不变) | ast 可解析;alembic 无 drift | OPEN |
| TD-014 | LOW | scripts/(89 个一次性/运维脚本) | 大量高复杂度一次性脚本滞留仓库 | 审计噪音、维护负担 | 归档至 scripts/archive 或明确标记一次性;不参与 production gate | gate 排除脚本目录;文档说明 | OPEN |

---

## 前端(apps/, packages/)

| ID | Sev | File | Problem | Risk | Fix | Verification | Status |
|---|---|---|---|---|---|---|---|
| TD-015 | HIGH | client-h5 PlaceView.vue(723)/ContributeView.vue(700)/HomeView.vue(427) | God Component,远超 200 行红线 | 不可维护;Empty-First(Phase H)改动高风险 | 按区块拆组件 + composable 抽离业务逻辑 | 组件 ≤200;vue-tsc/build PASS;视觉基线回归 | OPEN |
| TD-016 | MEDIUM | admin 6 个视图 250–400 行(SpatialExtrasView 397、OrganizationsView 389 等) | 组件规模超标 | 维护成本高 | 抽 composable/子组件 | 组件 ≤200(admin 非 release 主产品,可延后但需收口) | OPEN |
| TD-017 | MEDIUM | packages/client-core/src/api/client.ts(728 行手写) | 手写 API client 与生成 schema.d.ts 并存 | API contract 漂移(Phase G) | 统一到生成 client 或明确 adapter;核对 OpenAPI SSOT | contract 测试;漂移检测 | OPEN |
| TD-018 | MEDIUM | apps/client(uni-app)28 处硬编码 hex 色 | 唯一游离于 design-tokens 的客户端 | 视觉不一致;Phase J 要求 0 硬编码色 | 引入 tokens 等价映射;替换为 CSS 变量 | uni-app 硬编码色→0 | OPEN |
| TD-019 | MEDIUM | 全前端无 errorCaptured/errorHandler;admin 无离线/网络错误 UI | 无统一错误边界 | 异常时白屏/裸错误;Phase L 要求每页 error/offline 状态 | 建全局 error boundary + 网络错误组件;接入 admin | 注入错误 → 显示友好页非白屏 | OPEN |
| TD-020 | MEDIUM | 无独立 EmptyState 组件;"暂无"文案散落 ≥12 文件 | Empty 语义不统一;Phase K P0 | 空状态误导用户 | 建 EmptyState 组件(design-tokens PAGE_STATES 已定义语义),统一文案 | Empty 矩阵(0 place/rule/reality)全 PASS | OPEN |
| TD-021 | LOW | import.meta.env 2 处重复默认值 `/api/v1`;无 env 封装模块 | 配置散落 | 平台适配(Desktop/Android)时 base URL 混乱 | 建集中 env 模块(platform adapter) | 单点配置;Tauri/Capacitor 适配测试 | OPEN |

---

## 配置 / CI / 发布

| ID | Sev | File | Problem | Risk | Fix | Verification | Status |
|---|---|---|---|---|---|---|---|
| TD-022 | CRITICAL | 全仓无 .github/workflows | 无 CI;质量门禁全部靠人工本地执行 | **发布管线缺失**,v0.1.0 不可发布;回归无保障 | Phase AC 建立 PR CI(quality gate/ruff/mypy/pytest/前端 build/E2E/secret scan)+ Release CI | PR 与 tag 触发真实跑绿 | OPEN |
| TD-023 | HIGH | docs/governance/FIRST_REAL_PUBLISH_BATCH_01A_CLOSURE.md | 疑似 secret 模式命中(值未读取) | 若含真实凭据则泄露 | 人工核实内容;若含 secret 立即轮换并重写该文件;清理 git history 若已提交 | gitleaks/detect-secrets 全仓 0 命中 | OPEN |
| TD-024 | HIGH | 全仓无 secret 扫描配置 | 无自动防线 | secret 泄漏无感知 | 引入 gitleaks/detect-secrets 配置 + CI 接入 | 扫描器全仓 0 命中 | OPEN |
| TD-025 | LOW | packages/design-tokens/package.json version 0.6.0-beta.1 | Version SSOT 漂移 1 处 | VERSION_DRIFT > 0,Phase AE gate FAIL | 统一为 0.1.0 | VERSION_DRIFT = 0 | OPEN |
| TD-026 | LOW | README.md(73 行,pytest 209 过期) | 文档过期;未提及 v0.9/Reality/新架构 | 误导读者 | Phase AB 重写 README(含 0.1.0 Early Preview 定位) | README 内容与现状一致 | OPEN |
| TD-027 | LOW | docs/adr 仅 ADR-030/031 独立文件;ADR-001~029 内嵌 DECISIONS.md | ADR 编号连续性靠文档维护 | 决策难追溯 | 可批量导出独立 ADR 文件(非发布 blocker) | docs/adr 编号连续 | OPEN |

---

## 汇总

| Severity | 数量 | 说明 |
|---|---|---|
| CRITICAL | 1 | TD-022 无 CI(发布阻塞) |
| HIGH | 8 | TD-001/002/003/004/015/023/024 + 基线中规模超标项 |
| MEDIUM | 13 | TD-005~011、016~020 等 |
| LOW | 5 | TD-012/013/014/021/025/026/027 |

处置顺序(对齐 master goal Phase 顺序):
1. Phase B 建 gate → TD-001/002/003/008/010/015/016 进入自动 FAIL 列表(先让现状显性化)
2. Phase C/D 后端重构 → TD-001/002/004/005/006/007/008/009/011/012
3. Phase I/J/K/L 前端 → TD-015/016/018/019/020/021
4. Phase AC CI → TD-022;Phase F/Z 安全 → TD-023/024
5. Phase AE → TD-025;Phase AB → TD-026/027

> 注:每项修复都必须有验证(verification 列),不允许"改完即 PASS"。
