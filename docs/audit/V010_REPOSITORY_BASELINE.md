# V010_REPOSITORY_BASELINE.md

# v0.1.0 Phase A — 全仓只读审计 · 仓库基线

> 生成日期:2026-09-23(基于仓库实际只读盘点,非历史报告复制)
> 状态标记:CURRENT VERIFIED(本次实测) / HISTORICAL(历史记录,未重跑) / NOT RERUN(本轮未重跑) / BLOCKED(外部条件缺失)

---

## 1. 基线核验结果

| 项目 | 声称值 | 实测值 | 状态 |
|---|---|---|---|
| Git HEAD | `6079847` | `6079847` (master) | CURRENT VERIFIED |
| Worktree | — | clean (0 changed) | CURRENT VERIFIED |
| MIGRATION_HEAD | `e9f2c1d4a5b6` | alembic head `e9f2c1d4a5b6`(单 head,链完整,初始 revision `864ffcfc7ccb`) | CURRENT VERIFIED |
| pytest | 889 passed / 2 skipped | 未重跑(Phase B/X 重跑) | NOT RERUN |
| ruff / format | PASS | 未重跑(Phase B 重跑) | NOT RERUN |
| mypy | 97 files / 0 errors | 未重跑(Phase B 重跑) | NOT RERUN |
| H5 / Admin vue-tsc + build | PASS | 未重跑(Phase B 重跑) | NOT RERUN |
| Playwright | 18 passed | 未重跑 | NOT RERUN |
| Visual | 17 baselines PASS | 未重跑 | NOT RERUN |
| Reality DB migration/persistence | PASS | alembic head 已实测;drill 未重跑 | PARTIAL |
| Security Critical/High = 0 | PASS | 未重跑(Phase Z 重跑) | NOT RERUN |
| Backup/Restore | PASS | 未重跑 | NOT RERUN |
| Observability | basic endpoints PASS | 未重跑 | NOT RERUN |

关键差异记录:
- `e9f2c1d4a5b6` 是 **alembic revision**,不是 git commit;git 中不存在同名 commit(初查误判,已澄清)。
- 历史质量数字全部按 NOT RERUN 对待,Phase B(工程 gate)起逐项重验。

---

## 2. 仓库结构

```
E:\AI\宠物管理
├─ apps/
│  ├─ client/        uni-app x 客户端(.uvue,7 页 + tabBar,14 文件)
│  ├─ client-h5/     Vue 3 H5 消费者端(86 文件;src: 25 .vue + 6 .ts)
│  └─ admin/         Vue 3 管理端(102 文件;src: 29 .vue + 6 .ts)
├─ services/
│  ├─ api/           FastAPI 后端(290 文件;app 93 .py + migrations 24 versions + 独立 tests 4)
│  └─ worker/        Celery worker(仅 pyproject.toml,无 .py)
├─ packages/
│  ├─ api-client/    OpenAPI 生成 TS client(schema.d.ts 7042 行生成代码 + index.ts)
│  ├─ client-core/   手写 API client(728 行)+ platform adapter
│  ├─ design-tokens/ 语义 tokens(index.ts 291 行 + tokens.css)
│  └─ rule-spec/     JSON schema + fixtures(无 src)
├─ tests/            unit(43) / integration(23) / contract(4) / isolation(2) / e2e(1) / fixtures / visual
├─ scripts/          89 个 .py 运维/一次性脚本
├─ docs/             16 个子目录(adr 2, engineering 16, governance 47, reality_audit 26, ...) + audit(新建)
├─ infra/            docker/initdb/01-extensions.sql
├─ schemas/          petaccessjson-0.1.example.json 等
├─ .github/          不存在(全仓 0 CI 配置)
└─ 根: pyproject.toml, package.json(pnpm workspace), docker-compose.yml(db/redis/minio),
      AGENTS.md, DECISIONS.md, GOAL.md, 产品母版 md
```

后端分层(app/):`api/v1`(17) / `core`(10) / `db`(5) / `models`(11) / `providers`(7) / `rulespec`(13) / `schemas`(8) / `services`(13) / `worker`(3) / `tools`(2)。分层边界清晰,符合 UI→App→Domain→Ports 方向。

---

## 3. 文件数量统计

| 类别 | 数量 |
|---|---|
| backend app .py | 93 |
| tests .py(根 tests/) | 75(另 services/api/tests 4 个疑似重复职责) |
| alembic migration versions | 24 |
| scripts .py | 89 |
| client-h5 .vue / .ts | 25 / 6 |
| admin .vue / .ts | 29 / 6 |
| uni-app .uvue / .ts | 9 / 1 |
| 手写 TS 大文件 | client.ts 728 行(>300) |
| 生成 TS | schema.d.ts 7042 行(豁免) |

---

## 4. 行数 / 复杂度超标(工程规范门禁现状)

### 4.1 Python app(>250 / >300 行)
- >300 行:**24 个**;>250 行:**27 个**
- 最严重:`api/v1/v05.py` **3103**、`db/seed.py` **1494**、`models/enums.py` **848**、`rulespec/v05_resolver.py` **747**、`api/v1/reality.py` **718**、`tools/reality_audit.py` **705**、`db/safety.py` **651**、`services/evidence_service.py` **649**
- migrations >250:4 个(豁免项,但 864ffcfc7ccb 达 832 行)

### 4.2 tests(>300 行)
- **21 个**;最大 `unit/test_animal_scope.py` 752

### 4.3 前端 .vue/.uvue
- >150:**20 个**;>200:**16 个**
- 最严重:`client-h5/views/PlaceView.vue` 723、`ContributeView.vue` 700、`HomeView.vue` 427、admin `SpatialExtrasView.vue` 397、`OrganizationsView.vue` 389
- uni-app .uvue 全部 ≤137,合规

### 4.4 函数与复杂度
- 函数体 >60 行:**168 个**(top: `db/seed.py:run_demo_seed` 1378、`v05_resolver.py:resolve` 467)
- McCabe 复杂度 >10:**160 个**(top: `v05_resolver.py:resolve` **109**、`access_answer.py:build_access_answer` 36)
- 集中在核心判定链路(v05 系列 / access_answer / publish_gate)

---

## 5. 类型纪律

| 项 | 数量 | 分布 |
|---|---|---|
| `# noqa` | 194(scripts/tests 为主;app 内 7) | worker/tasks.py 4, celery_app 2, seed 1 |
| `cast(` | 3 | core/idempotency、observability、ratelimit 各 1 |
| `# type: ignore` | 13(app 内 11) | **evidence_service.py 7**、answerability 2、disputes 2 |
| `Any`(app 非 import) | 49 次使用 / 65 含 import | coexistence_snapshot 13、access_answer 11、safety 8、storage 7、tencent_map 6 |
| 前端 `any` | 4 | admin/RealityClaimsView.vue ×3 + 生成代码 1 |
| 前端 ts-ignore 家族 | 0 | — |

结论:前端纪律好;后端核心域存在集中类型逃逸(证据/答案判定),违反强类型规则。

---

## 6. TODO / 死代码 / 日志

| 项 | 结果 |
|---|---|
| 裸 TODO/FIXME/HACK/XXX(Python) | **0** |
| 裸 TODO/FIXME/HACK/XXX(前端 src) | **0** |
| `console.log(` 前端 src | **0** |
| `print(` backend app | **10**(`db/safety.py` 7 —— 安全敏感模块用 print 而非结构化日志) |
| 死路由/死组件 | 未发现明显死路由;uni-app 与 client-h5 存在功能重复实现(StatusBadge/ModeBar 两套) |
| i18n | 无(v0.1.0 不要求) |

---

## 7. 配置 / Env / Secret

| 项 | 结果 |
|---|---|
| 集中 Settings | 有:`app/core/config.py` `class Settings(BaseSettings)`(pydantic-settings v2,env_file 根 .env) |
| 散落 env 读取 | `os.getenv` 9 处(app 1 + tests 1 + scripts 7);`import.meta.env` 2 处重复默认值 `/api/v1` |
| .env.example | 37 行,全 dev 占位值,**无真实 secret**;.env 29 键与 example 完全一致 |
| 可疑默认值 | config.py 内嵌 dev JWT_SECRET / DB / S3 明文默认(生产需 fail-fast 覆盖) |
| Secret 扫描 | **无任何扫描配置**(gitleaks/detect-secrets 均无);全仓 1 个疑似 secret 命中文件:`docs/governance/FIRST_REAL_PUBLISH_BATCH_01A_CLOSURE.md`(**需人工核实**) |
| docker-compose | db(postgis)/redis/minio,全部 `${VAR:-default}` 插值,无硬编码凭据 |
| .gitignore | 完整(含 .env、密钥后缀 *.p12/*.jks/*.pem/*.key、agent 输出目录) |

---

## 8. CI / 发布基建

| 项 | 现状 |
|---|---|
| GitHub workflows | **不存在**(无 .github) |
| 任何 CI 载体 | **0**(仅本地 scripts/dev.sh test.sh lint.sh typecheck.sh + qa_all.ps1) |
| Secret 扫描 CI | 无 |
| Tauri / Android 工程 | **不存在**(无 src-tauri / Cargo.toml / tauri.conf.json / AndroidManifest)——Phase Q–U 待建 |
| GitHub remote / release | 无 remote、无 tag(v0.5-quality-freeze 为历史本地 tag) |
| docs/release | 6 个文档,最新 V09_FINAL_REPORT;`docs/audit` 原为空(本次 Phase A 填充) |

---

## 9. Version SSOT(Phase AE 预检)

| 位置 | version |
|---|---|
| package.json(根) + apps/admin + client-h5 + client + packages/client-core + api-client | 0.1.0(6 处一致) |
| pyproject.toml(根) + services/api + services/worker | 0.1.0(3 处一致) |
| **packages/design-tokens/package.json** | **0.6.0-beta.1(唯一漂移)** |
| 发布轮次文档 | 已到 v0.9-R1(代码版本号未随轮次推进) |

现状:漂移点 1 处(design-tokens);v0.1.0 目标要求 VERSION_DRIFT = 0,Phase AE 收口。

---

## 10. Phase A 全清单核对(目标项 → 发现)

| 检查项 | 结果 |
|---|---|
| 文件总数 / production source / tests / generated | ✓ 见 §3 |
| >250 / >300 行人工源码 | ✓ 24 个 >300(app),21 个 tests >300 |
| UI component >200 行 | ✓ 16 个 |
| function >60 行 | ✓ 168 个 |
| complexity >10 / >15 | ✓ 160 个 >10(app 内 63 个 >15 级候选) |
| deep nesting | 未单列扫描(随复杂度项覆盖),Phase B gate 补 |
| high parameter count | 未单列扫描(需 Phase D 抽查) |
| circular dependency | 未发现(app 依赖方向单向);Phase C 用工具验证 |
| duplicate domain model | services/api/tests 4 文件与根 tests 疑似重复职责(未确认重复逻辑) |
| any / cast / ignore / noqa | ✓ §5 |
| TODO/FIXME/HACK/TEMP | ✓ 0(前端与后端) |
| dead route / dead component | 未发现死路由;uni-app 与 H5 双实现是最大重复面 |
| dead env / dead dependency | 未发现明显死 env;依赖死项未单列扫描(Phase B 补) |
| duplicated config | 前端 env 默认值 2 处重复(§7);后端 config 集中良好 |
| scattered process.env / os.getenv | ✓ 少量(9 + 2),可控 |
| hardcoded colors | ✓ 28 处全在 uni-app(.uvue);client-h5/admin 的 .vue 为 0(全走 tokens) |
| hardcoded spacing | 未发现(设计 tokens 已覆盖 client-h5/admin) |
| raw magic status | 未系统扫描(需 Phase D 抽点);tokens 已提供 STATUS_SEMANTICS |
| silent catch / broad exception | ✓ 17 宽捕获 + 18 可疑 silent catch(app 10) |
| logging privacy issues | 未发现敏感正文日志;db/safety.py 用 print 是结构性问题 |
| N+1 / unbounded query | 未系统扫描(Phase D 需逐查询审计) |
| synchronous heavy media | 未发现(媒体走 storage provider,无同步重媒体) |
| missing idempotency | 已有 core/idempotency.py;其内部 2 处 silent catch 需修 |
| unsafe transaction | 未发现明显越界 commit;Phase D 审计 |
| API/client drift | schema.d.ts 为生成代码(SSOT=OpenAPI);手写 client.ts 728 行与生成 client 并存,需 Phase G 核对漂移 |

---

## 11. 结论

- **健康面**:结构分层清晰、配置集中、零裸 TODO、零前端类型逃逸、tokens 覆盖到位、alembic 单 head、.env 无真实 secret。
- **主要风险面**(按影响排序):
  1. **无 CI / 无 secret 扫描 / 无 GitHub remote** —— 发布管线完全缺失(Phase AC 前不可发布)。
  2. **规模失控集中在核心判定链路** —— v05.py 3103 行、resolve() McCabe 109、seed.py 1494 行,直接违反 300 行/60 行/复杂度门禁(Phase B/C/D 收口)。
  3. **错误吞噬位于幂等/安全边界** —— idempotency / security / worker 的 silent catch(Phase D 必修)。
  4. **类型逃逸集中在证据/答案判定域** —— evidence_service 7 处 type:ignore、49 处 Any 使用(Phase C/D 收口)。
  5. **uni-app 客户端游离于设计体系** —— 28 处硬编码色、无 env/离线/错误处理(Phase I/J 收口)。
- 下一步:Phase B(工程规范自动 gate 落地) → Phase C(架构审计) → Phase D(后端 review),逐项从 NOT RERUN 转 CURRENT VERIFIED。
