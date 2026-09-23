# PetAccess 宠物共处 — 宠物准入与公共空间共处规则平台

> 产品名：**PetAccess / Place Animal Access Map**
> 一句话：让你在到达一个地方之前，知道这里关于动物的规则。

> ⚠️ 当前版本：**v0.1.0 — Early Preview（技术预览）**。
> 这不是 Public Beta，也不包含完整数据。当前**真实数据可能为空**——这是设计使然，
> 不是故障：宁可显示「暂无记录」，也不展示未经核验或虚构的规则。

---

## 1. 产品是什么

PetAccess 是一个「宠物准入与公共空间共处规则」平台：用户在到达一个场所之前，
可以查看该场所对宠物（包括服务犬）的准入规则、已经人工核验的现场事实，
也可以贡献自己观察到的线索。

**设计母版**：`docs/MASTER_DESIGN_v0.3_DEV.md`（冻结）。

### Rule + Reality 双事实层

平台把「规则」和「现实」作为两个独立的事实层，永不混为一谈：

| 层 | 内容 | 来源 |
|---|---|---|
| **Rule（规则层）** | 管理方/来源声明的准入规则 | 管理员录入，高影响规则必须有 Source（来源） |
| **Reality（现实层）** | 经人工核验的现场事实 | 用户观察线索 → 人工核验 → 现场事实 |

核心不变量：

- **UNKNOWN ≠ ALLOWED**：未收录 ≠ 没有规则，暂无记录 ≠ 没有动物。
- **Observation ≠ Rule**：用户观察永远不等于规则，也不会自动变成规则。
- **AI 不是最终裁判**：AI 辅助整理，最终判定由人工完成。
- **管理方声明与用户观察并存**：两者都可见，而不是互相覆盖。

### 当前真实数据可能为空（重要）

v0.1.0 的**真实数据可能为空**：

- `Places` / `Rules` / `RealityClaims` / `StaffResponses` / `AnimalFacilities` 均可能为 0。
- release 构建**不含** demo seed，**没有任何虚构/演示数据**。
- 空态是产品特性：首页显示「当前还没有已发布的场所数据」，
  搜索显示「没有找到已收录场所」，未收录场所显示「未收录 ≠ 没有规则」。

## 2. 功能列表

- **Empty-First 空态**：无数据时页面完整可用，首页 / 搜索 / 场所 404 都有明确的空态或错误文案，不假装有内容。
- **搜索**：按场所名 / 品牌 / 别名检索场所。
- **地图**：场所地图视图；v0.1.0 不请求设备定位（附近场所查询使用服务端合成坐标，仅演示）。
- **场所详情**：规则层与现实层分开展示；含服务犬与普通宠物的准入差异、规则冲突与废止规则的可见性。
- **贡献线索**：提交现场观察线索（含防滥用限制：限频 / 去重 / 旧视频拒绝 / 场所不匹配拒绝）；观察不等于规则。
- **宠物档案**：记录宠物信息，便于查看相关准入与共处信息。
- **共处边界**：服务犬 ≠ 普通宠物；规则冲突、废止规则、管理方声明与用户观察并存展示。

## 3. 平台与安装

| 平台 | 安装包 | 说明 |
|---|---|---|
| **Windows x64** | `PetAccess_0.1.0_x64-setup.exe`（NSIS） | **未签名**，SmartScreen 可能弹出警告；项目政策：**不伪造签名**。请先校验 SHA256。 |
| **Android 7.0+** | `PetAccess_0.1.0-android-universal.apk` | **正式签名**（release keystore，v2/v3 scheme）；`com.petaccess.map`；versionName `0.1.0` / versionCode `1000`；minSdk 24；仅 `INTERNET` 权限。未上架应用商店，直接安装需允许「未知来源」。 |

安装前请校验哈希：

```
SHA256SUMS.txt 位于 artifacts/v0.1.0/ 与 docs/release/
Windows: certutil -hashfile PetAccess_0.1.0_x64-setup.exe SHA256
Android: certutil -hashfile PetAccess_0.1.0-android-universal.apk SHA256
```

## 4. 快速开始（开发环境）

前置：Docker、Python 3.12+（含 uv）、Node 20+（含 pnpm）。

```bash
# 1. 基础设施（PostGIS 17 / Redis / MinIO）+ 迁移 + 演示 seed（仅开发，release 不含）
bash scripts/dev.sh          # Windows PowerShell 见 scripts/dev.ps1

# 2. 后端 API（文档 http://127.0.0.1:8000/docs）
cd services/api && uv run uvicorn app.main:app --reload --port 8000

# 3. 消费者 H5（http://localhost:5174）
cd apps/client-h5 && pnpm install && pnpm dev

# 4. 管理后台（http://localhost:5173）
cd apps/admin && pnpm install && pnpm dev

# 5. 后台 worker（OCR / 异步任务需要）
cd services/api && uv run celery -A app.worker.celery_app worker --pool=solo
```

> 开发 seed 全部为**虚构演示场所**，仅用于开发与测试，绝不进入 release。

## 5. 测试

| 目标 | 命令 | 本会话实测 |
|---|---|---|
| 后端全量测试 | `bash scripts/test.sh` 或 `uv run pytest` | **916 passed / 2 skipped** |
| E2E | `pnpm exec playwright test` | **21 passed**（18 常规 + 3 空态） |
| 视觉回归 | `pnpm exec playwright test --config playwright.visual.config.ts` | **47 passed** |
| lint | `bash scripts/lint.sh`（ruff check + format check） | **PASS** |
| 类型检查 | `bash scripts/typecheck.sh`（mypy） | **93 files / 0 errors** |
| 工程门 | `uv run python scripts/check_engineering_quality.py` | **0 FAIL** |
| Secret 扫描 | `uv run python scripts/scan_secrets.py` | **0 findings** |
| 版本 SSOT | `uv run python scripts/check_version_drift.py` | **VERSION_DRIFT = 0** |

## 6. 架构

分层：**UI → App → Domain → Ports**；外部能力（地图 / AI / 存储 / 通知 / 认证）一律通过
interface + adapter 接入，核心 Domain 不依赖具体 SDK。

```
apps/client-h5       消费者 H5（Vue 3 + Vite）+ Tauri 2 壳（Windows / Android）
apps/admin           管理后台（Vue 3 + design-tokens）
services/api         FastAPI + SQLAlchemy 2 + PostGIS 17（PostGIS 索引、FK、audit 时间戳）
services/worker      Celery worker（Redis 队列）
packages/design-tokens   设计令牌（Design System）
packages/rule-spec       规则语义
packages/api-client      生成的 API 客户端
packages/client-core     消费者共享逻辑
infra/docker         docker-compose（postgis/postgis:17 / redis / minio）
schemas              契约 schema
scripts              工程脚本（dev / test / lint / gate / secret scan / 版本 SSOT）
tests                后端 + E2E + 视觉回归
docs                 设计母版 / ADR / 治理 / 发布文档
```

## 7. 安全

- **Secrets 政策**：绝不 commit API key、私钥、生产凭据；release keystore 与密码存放于
  Git 之外的用户目录（`~/.petaccess-keystore/`）；PR CI 强制 secret 扫描（worktree + git history）。
- **无 fake 数据**：release 不含 demo seed；演示数据全虚构并在开发环境隔离。
- **权限最小化**：Android 仅 `INTERNET` 权限，运行时权限请求数 = 0；Tauri capabilities 仅 `core:default`；CSP strict。

## 8. 贡献

参见 [CONTRIBUTING.md](CONTRIBUTING.md)：环境搭建、gate 运行、提交规范、测试要求。

## 9. License

MIT — 见 `apps/client-h5/src-tauri/Cargo.toml`（`license = "MIT"`）。

## 10. 当前版本状态

- **v0.1.0 — Early Preview（技术预览）**，不是 Public Beta，不承诺数据覆盖。
- **未上架应用商店**（Android 需侧载，Windows 走安装包）。
- **GitHub Release 待授权**：`RELEASE_V0_1_0_AUTHORIZATION`（huangdi97）未授予，
  `V0_1_0_RELEASED = NO`。
- **CI 目前 BLOCKED**：仓库尚无 git remote，远程 CI 未实跑；PR/Release CI 工作流已就绪。

## 相关文档

`PROJECT_STATE.md` / `DECISIONS.md` / `ACCEPTANCE_MATRIX.md` / `BLOCKERS.md` /
`docs/MASTER_DESIGN_v0.3_DEV.md` / `docs/release/`（v0.1.0 发布评审报告）。
