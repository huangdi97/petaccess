# CONTRIBUTING — 贡献指南

感谢你愿意为 **PetAccess 宠物共处** 贡献力量。在提交任何改动之前，请先阅读：

1. `docs/MASTER_DESIGN_v0.3_DEV.md`（设计母版，冻结）
2. `GOAL.md` / `DECISIONS.md` / `IMPLEMENTATION_PLAN.md`
3. `ACCEPTANCE_MATRIX.md` / `PROJECT_STATE.md` / `BLOCKERS.md`

项目核心约束（不可妥协）：

- **Access，不是 Friendly**；Place → Zone → AccessRule；自有 Place UUID。
- **Observation ≠ Rule**；**UNKNOWN ≠ 允许/禁止**；AI 不是最终裁判。
- 高影响 Rule 必须有 Source；管理方声明与用户观察并存。
- **不造数据**：禁止 fake 数据、禁止为演示目的向真实数据路径写入虚构记录。
- **不提交 Secrets**：API key、私钥、生产凭据一律不进 Git。

## 1. 环境搭建

前置：Docker、Python 3.12+（含 uv）、Node 20+（含 pnpm）。

```bash
# 一键：基础设施（PostGIS 17 / Redis / MinIO）+ 迁移 + 演示 seed
bash scripts/dev.sh          # Windows PowerShell: scripts/dev.ps1

# 后端
cd services/api && uv run uvicorn app.main:app --reload --port 8000
# 消费者 H5
cd apps/client-h5 && pnpm install && pnpm dev   # http://localhost:5174
# 管理后台
cd apps/admin && pnpm install && pnpm dev       # http://localhost:5173
# 后台 worker（OCR / 异步任务）
cd services/api && uv run celery -A app.worker.celery_app worker --pool=solo
```

> 开发 seed 全部为**虚构演示场所**，仅用于本地开发与测试。

## 2. 提交前必须运行的 Gate

| 门 | 命令 | 要求 |
|---|---|---|
| 后端测试 | `bash scripts/test.sh`（或 `uv run pytest`） | 全量通过 |
| lint | `bash scripts/lint.sh`（ruff check + format check） | PASS |
| 类型检查 | `bash scripts/typecheck.sh`（mypy） | 0 errors |
| 工程门 | `uv run python scripts/check_engineering_quality.py` | 0 FAIL |
| Secret 扫描 | `uv run python scripts/scan_secrets.py` | 0 findings |
| 版本一致性 | `uv run python scripts/check_version_drift.py` | VERSION_DRIFT = 0 |
| E2E | `pnpm exec playwright test` | 全量通过（需 API/H5 实例） |
| 视觉回归 | `pnpm exec playwright test --config playwright.visual.config.ts` | 全量通过 |

本地 E2E / 视觉回归所需服务与端口约定见 `playwright.config.ts` 与
`playwright.visual.config.ts` 的 `webServer` 配置。

## 3. 提交规范

- **单用途提交**：一次提交只解决一个问题。参考类型：
  `feat` / `fix` / `refactor` / `test` / `docs` / `chore` / `security` / `reality` / `governance`。
- **里程碑标注**（M0-M12 风格）：属于某里程碑的改动在主题末尾标注，例如：
  - `feat(android): signed release APK + smoke verified (M8)`
  - `chore(gate): wire engineering quality gate + secret scan + PR CI (M1)`
- **行为变化与结构变化分离**：重构不夹带产品逻辑变更。
- **禁止**：大范围无关注释格式化与功能改动混在同一提交；禁止降级质量门来通过 CI
  （删除测试、弱化断言、加 ignore、改正确测试去迎合错误实现等）。

## 4. 测试要求

- 提交前运行第 2 节全部 Gate；**FAIL 必须修复或如实记录 blocker**。
- 新功能必须覆盖：success / failure / boundary / permission / invalid input / retry / duplicate。
- 关键安全不变量要有回归测试（例如 UNKNOWN ≠ ALLOWED、Observation ≠ Rule）。
- Mock 放在真正系统边界（外部 API / AI / 存储 / 通知），不要 mock 掉自己的核心 Domain 规则。

## 5. Secrets 与数据

- 绝不 commit：API key、private key、production credentials。
- Release keystore 与密码位于 Git 之外（`~/.petaccess-keystore/`），CI 通过 Secrets 注入。
- 提交前自检：`uv run python scripts/scan_secrets.py`（worktree + git history）。
- **禁止向生产/发布路径写入虚构数据**；演示数据只在开发环境隔离。

## 6. 如何报告 Bug

请提供：

- 版本与平台：版本号（如 0.1.0）、OS（Windows / Android）、Android 版本号。
- 复现步骤：从哪进入、点了什么、看到了什么。
- 期望行为与实际行为的对比。
- 截图或日志（**先脱敏**：不要贴 token、密码、完整隐私内容）。
- 是否与「数据为空 / 未收录场所」场景相关。

## 7. 合并与发布

- PR 合并前需通过 PR CI（工程门 → 后端 → 前端 → E2E 子集）。
- 版本发布走 `RELEASE.md` 流程；**发布必须经 `RELEASE_V0_1_0_AUTHORIZATION`（huangdi97）授权**，
  无授权不发布、不伪造。
