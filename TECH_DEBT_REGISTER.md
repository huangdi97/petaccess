# TECH_DEBT_REGISTER.md

日期：2026-09-13（PART A · A15）。原则：能修的修了（见"本轮已修"）；修不了的如实登记，不藏。

## 本轮已修（从扫描到修复）

| 项 | 处置 |
|---|---|
| 前端 0 lint/format 工具链 | 引入 ESLint 10（vue flat/essential + ts recommended）+ Prettier 3；**实际运行**并通过 |
| 前端 dead code（6 处 unused import/var） | 删除：EvidenceView `platformPreview`、PlacesView `onMounted`、RegulationsView `get`、PlaceView `STATUS_GLYPHS`/`PlaceSummary`、MineView `Shell` 导入、AppShell `mode`/`MODE_LABELS` |
| `Shell.vue` 单词组件名 | 重命名 `AppShell.vue`（7 个视图同步更新） |
| `pnpm-workspace.yaml` 字面占位符 `allowBuilds: esbuild: set this to true or false` | 置为 `esbuild: true`（esbuild postinstall 需要） |
| 生成 API client 与 OpenAPI 不一致 | 实查：提交版缺全部 v0.5 端点（answerability/effective-rules/boundary-match 等 0 命中）。已 `pnpm client:gen` 重新生成，双端 build 复验 PASS |
| dev JWT secret 30 字节（RFC 7518 告警） | 30→49 字节；测试警告 60→1 |
| verifications HTTP 层无测试（docstring 谎报覆盖） | 补 5 个集成测试；test_api.py docstring 修正 |
| `candidate_service.publish()` 并发竞态（双 reviewer 可重复发布规则） | 原子 CAS（`WHERE review_status='APPROVED'`）+ 并发测试锁定 |
| `tests/e2e/__init__.py` 游离文件 | 见 TD-04（随 git mv 检查保留，无运行影响） |

## 登记项（未在本轮修，含理由）

| ID | 项 | 影响 | 建议 | 理由 |
|---|---|---|---|---|
| TD-01 | `services/worker/` 空壳（仅 pyproject.toml，声明 `packages=["worker"]`，实际 Celery 代码在 `services/api/app/worker/`） | 结构混乱：uv workspace 成员指向不存在的包 | 合并 workspace 或移除空壳成员（需 `uv.lock` 重排） | 改动 workspace 定义影响打包/安装链，属结构性重构，独立成 Gates 更安全 |
| TD-02 | `packages/design-tokens/` 空目录；`apps/client/adapters/` 空目录 | 死目录 | 补内容或删除 | design-tokens 属设计系统决策；adapters 属 uni-app x 平台层（B-01 外部阻塞），本轮不越权发明 |
| TD-03 | v0.3 API 路由覆盖偏低（places 48% / disputes 44% / rules 56% / regulations 57% / admin 53%）+ `worker/tasks.py` 46% | 回归防护薄（业务语义已有 integration/E2E 背书） | 按"每修一个 bug 补一层 HTTP 测试"节奏渐进补齐 | 见 TEST_COVERAGE_REPORT 解释；为凑数写无断言测试违背 A5 原则 |
| TD-04 | `tests/e2e/__init__.py`（Playwright 目录里的 Python 包标记） | 轻微困惑 | 删除（pytest testpaths 不含该目录） | 保留于登记：删除属低风险但需一次回归确认，本轮聚焦更高价值项 |
| TD-05 | 无 face / license plate redaction 能力 | 真实数据扩量（PART B 扩量/100+）前的隐私缺口 | 接入 OCR/AI 管线时加脱敏步骤或建立素材准入策略 | 本地 RC 无真实用户素材；PART B 第一轮以"不采集含人脸/车牌素材"为执行约束 |
| TD-06 | 无 resolver batch 批量端点（多场所评估逐次调用） | 规模化时列表页 N×单次成本 | 数据量上来后加 batch 端点（evaluator 本身可批量，GOAL §20） | 当前 4–50 场所规模下 p95≤28ms，无实际瓶颈 |
| TD-07 | client-core 手写 v0.5 DTO（`EffectiveRuleSet` 等接口与后端 schema 重复） | 类型双写漂移风险 | 由生成 `schema.d.ts` 的 operations 类型替代（A1"no duplicated API DTO"） | 涉及 20+ 视图类型迁移，独立重构任务 |
| TD-08 | `observability.py` failed-job 落盘在 Redis 不可用时静默跳过 | Redis 故障期间失败任务不可见（任务本身仍失败/重试可见） | 记录降级计数或落本地文件 | 结构性小改进，非缺陷；可靠性主链（有界重试/幂等/失败可见）已验证 |
| TD-09 | PART B 试点中 7/33 规则候选引用 search_snippet 采集来源（页面未直接抓取核验：解放日报、OTA、CBNData、西岸报道URL待归档） | Evidence Completeness 78.8% < 90%，B15 停止条件已触发（扩量暂停） | 人工核验原文页/定位 URL/补抓 hash，升级 capture_method 后方可 APPROVED；扩量前完成 | 如实登记；见 REAL_DATA_PILOT_10_REPORT.md §7 与 REAL_DATA_FINAL_REPORT.md §9 |

## 扫描方法与结果

- TODO/FIXME/HACK/XXX：tracked 文件全扫 → **代码 0 命中**（仅 GOAL/ZCODE 文档中的纪律性文字）。
- `pass`/`NotImplementedError`：4 处，全部合法（异常类体、抽象接口方法 pragma、
  mock 通知 best-effort、failed-job 降级）。
- mock-only production path：Mock Provider 均有显式开关与 factory（`FEATURE_REAL_*`），无伪装。
- unused env：`.env`/`.env.example` 键与 `core/config.py` 字段一致（抽查 JWT/S3/MAP/AI 组）。
- duplicate schema：唯一发现即 TD-07（已登记）。

结论：无 unexplained TODO；所有遗留项登记在册且有处置建议。
