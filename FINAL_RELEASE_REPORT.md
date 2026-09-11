# FINAL_RELEASE_REPORT.md
# 宠物准入信息平台 / Place Animal Access Map — 本地 RC 发布报告

日期：2026-09-12　|　代码基线：`fac294c`（Phase 0-13 全部本地可实现工作）
性质声明：本报告只记录**实际执行过**的验证；未真实验证的项单独列出，绝不写成通过。

---

## 1. 完成情况（相对 GOAL.md 的 13 个 Phase）

| Phase | 内容 | 状态 |
|---|---|---|
| 0 | git/monorepo/docker/lockfile/lint/typecheck/test/根脚本 | 完成 |
| 1 | 17 表 + Alembic up/down + PostGIS/trgm 索引 + 可重复 seed | 完成 |
| 2 | rule-spec JSON Schema + 确定性 evaluator + 单测矩阵 | 完成 |
| 3 | FastAPI 全量 API + RBAC/audit/rate-limit/idempotency + TS client | 完成 |
| 4 | Admin Vue3 真连 API（14 个视图） | 完成 |
| 5 | client-core + H5 闭环真跑 + uni-app x 源码工程 | 完成（全端构建=B-01） |
| 6 | AI Provider 抽象 + Mock（vision/OCR/NL parse） | 完成 |
| 7 | 贡献/核验/幂等/限流/撤回/反滥用 | 完成 |
| 8 | Operator claim→批准→问卷→规则版本化 | 完成 |
| 9 | Jurisdiction 四态 + 审核流 | 完成 |
| 10 | Dispute 全流程 + 审计 | 完成 |
| 11 | Watch 订阅 + Celery worker + mock 通知（幂等） | 完成 |
| 12 | 跨端配置/说明（docs/PLATFORMS.md） | 完成（构建=B-01..03） |
| 13 | 全量测试/安全扫描/文档/本报告 | 完成 |

非谈判原则逐条落实于代码与测试：自有 UUID（external_place_ref 仅引用）、
Observation 永不变 Rule（evaluator 输入无观察）、服务犬 scope 独立、
UNKNOWN≠允许/禁止（单测锁定）、无遇宠率/排行榜/评论区、小区无住户数据、
无连续轨迹（仅分桶）、高影响规则强制 source_id FK、demo 全虚构。

## 2. 测试证据（实际命令 → 实际输出摘要）

| 命令 | 结果 |
|---|---|
| `uv run pytest -q` | **30 passed**（15 evaluator 单测含 GOAL #7 十条矩阵；2 JSON-Schema 契约；13 集成打真实 PostGIS+Redis） |
| `pnpm exec playwright test` | **5 passed**（H5 核心旅程：首页→详情答案→模式切换→搜索→注册→宠物→快速核验） |
| `bash scripts/lint.sh` | ruff check + format check 全过 |
| `uv run mypy services/api/app` | 54 files, no issues |
| `alembic upgrade head` / `downgrade base` / `upgrade head` | 19 表 → 2 表 → 19 表 |
| PostGIS 真查 | ST_DWithin nearby（4 场所带距离）、ST_Contains 命中"A 草坪"、trgm 命中"星河咖啡" |
| `uv run celery ... worker --pool=solo` + `notify_rule_changes.delay().get()` | `{'notified_watches': 1}`；Redis 出现通知；**二次执行 0（幂等）** |
| 浏览器手工 E2E（IAB） | 首页 4 场所→星河咖啡：室内"限制"/户外"有条件·需牵引"/服务犬"可以进入"→切换模式重算→注册→建"豆豆·柴犬·9.5kg"→答案带宠物上下文→快速核验"已记录"→关注成功 |
| `pnpm --filter @petaccess/admin build`、`client-h5 build` | vue-tsc strict + vite build 通过 |
| `uv tool run pip-audit` / `pnpm audit` | No known vulnerabilities（两者） |
| 密钥扫描 | .env 未入库；源码无 key 模式 |

## 3. 架构与交付物

- `services/api`：FastAPI + SQLAlchemy 2 + Alembic + psycopg3 + PostGIS；13 组路由；
  OpenAPI 50 路径（SSOT）；统一错误/RBAC 五级/审计/Redis 限流/幂等。
- `app/rulespec/`：纯函数 evaluator（无 DB/LLM），zone 遮蔽 place、服务犬隔离、
  冲突检测、阈值/义务/时段条件；`packages/rule-spec` 5 个 draft-2020-12 Schema。
- `packages/api-client`：openapi-typescript 生成 + 类型化 fetch 封装（ADR-011）。
- `apps/admin`：Vue3+Vite+TS 后台，全部真连 API。
- `apps/client-h5` + `packages/client-core`：平台无关业务核心 + H5 验证应用。
- `apps/client`：uni-app x 源码（manifest/pages.json/7 页面 .uvue/platform adapter）。
- `app/worker`：Celery（watch 通知、图片 TTL），mock 通知写 Redis 可验证。
- 演示数据：星河咖啡/青岚公园/云栖中心/松风社区 + service dog 差异、冲突、废止、
  已认领、异议、观察与规则并存。

## 4. 未真实验证（诚实清单）

1. **uni-app x 五端编译产物**（H5/微信/Android/iOS/HarmonyOS）——无 HBuilderX，
   源码按官方规范写就但未经编译器检查（B-01）。H5 行为由 client-h5 真跑覆盖，
   两者共享同一业务核心。
2. **真实腾讯地图渲染**——Key 未配置（B-04）；Mock provider 已真跑同接口。
3. **真实 AI 识别/OCR**——Key 未配置（B-05）；Mock 已真跑同接口与确认契约。
4. **OAuth/短信登录**——MVP 用账密 JWT；扩展登录未实现（B-06）。
5. **生产部署链路**（域名/备案/HTTPS/备份恢复演练）——超出本地 RC 范围（B-07）。
6. **MinIO 上传**——S3 抽象与配置就绪，但上传端到端（真实图片→对象存储→审核）
   未串通，属 Stage C。

## 5. Blockers（全部为真实外部项，详见 BLOCKERS.md）

B-01 HBuilderX（uni-app x 编译）· B-02 微信 AppID/类目 · B-03 移动端签名与账号 ·
B-04 腾讯地图 Key · B-05 AI Key · B-06 OAuth/短信 · B-07 域名/备案/法务。

## 6. 用户仅剩的人工步骤

1. 安装 HBuilderX → 打开 `apps/client` → 运行 H5/微信（B-01 步骤）。
2. 各平台账号/证书申请后按 docs/PLATFORMS.md 打包。
3. 申请腾讯地图 Key → `.env` 填入 → `FEATURE_REAL_MAP=true` → 重启 API。
4. 选型 AI provider → 实现 factory 中对应 adapter（接口已冻结）→ `FEATURE_REAL_AI=true`。

## 7. 凭证到位后的命令

```bash
# 腾讯地图 Key
$env:TENCENT_MAP_KEY_CLIENT="<key>"; $env:FEATURE_REAL_MAP="true"; cd services/api; uv run uvicorn app.main:app --port 8000
# 验证：curl /api/v1/ai/map/config → provider 不再是 mock（需先落地 tencent adapter）
```

## 8. 启动（全新机器）

```bash
cp .env.example .env            # Windows: Copy-Item
bash scripts/dev.sh             # infra + migrate + seed
cd services/api && uv run uvicorn app.main:app --port 8000   # API(:8000)
cd apps/client-h5 && pnpm i && pnpm dev                      # H5(:5174)
cd apps/admin && pnpm i && pnpm dev                          # Admin(:5173)
```

## 9. 结论

Stage A（本地垂直切片）**真实完成**：DB/API/evaluator/Admin/H5/synthetic seed 全链路
真跑并有两层测试（API 集成 + 浏览器 E2E）背书。Stage B 数据面能力（贡献/认领/异议/
关注）在同一真机栈上闭环。Stage C 需要的外部凭证已全部精确定位并隔离（Mock 不阻塞
业务逻辑）。可以进入：真实小范围场所采集试点（Stage D 前置）与 HBuilderX 全端验证。
