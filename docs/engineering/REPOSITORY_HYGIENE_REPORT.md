# Repository Hygiene Report

> §3 的实测结果。原则：只清理**垃圾**，绝不删 Evidence / Source / Audit / Migration / 有效 fixture。

## 1. 扫描范围

`git status --porcelain --untracked-files=all`、缓存与构建目录、
临时/补丁文件、截图产物、本地环境文件、ignore 配置。

## 2. 发现与处置

| # | 发现 | 类型 | 处置 |
|---|---|---|---|
| 1 | `workbuddy_pre_takeover.patch`（**已跟踪**，2.1 KB，Sep 12 的 agent 交接补丁） | 补丁垃圾 | `git rm --cached` 取消跟踪，**文件保留在磁盘**；新增 `*.patch` 忽略规则 |
| 2 | `quality_phase_pre_takeover.patch` / `*_staged.patch` / `zcode_resume_*.patch`（4 个未跟踪，其中 2 个为 0 字节） | 补丁垃圾 | 同上，由 `*.patch` 忽略；未删除（不是我的产物，保留可追溯） |
| 3 | `.workbuddy/`（agent 工作区，含 `_gitstatus.tmp`） | 工具目录 | 加入 `.gitignore` |
| 4 | `.mypy_cache/` 23 MB、`.pytest_cache/`、`.ruff_cache/`、`test-results/`、`playwright-out/` | 缓存/构建产物 | 已在 `.gitignore`；本轮补 `htmlcov/` `.coverage` `coverage.xml` `blob-report/` `.playwright/` `.hypothesis/` `*.tsbuildinfo` |
| 5 | 生成物被 Prettier 改写 | 工具冲突 | `.prettierignore` 增加 `HUMAN_REVIEW_PACKET_R2_FINAL.md` 等签署包生成物 |

## 3. `.gitignore` 本轮新增

```
.workbuddy/            .opencode/             *.patch  *.rej  *.orig  *.tmp  *.bak  *.swp
htmlcov/  .coverage  .coverage.*  coverage.xml
blob-report/  .playwright/  *.tsbuildinfo  .hypothesis/
ehthumbs.db  desktop.ini
```

**同时显式保留**（不得忽略）：`docs/reality_audit/**`（Evidence/Audit 记录）、
`infra/*.sql`、`services/api/migrations/**`、`tests/fixtures/**`。

## 4. 未发现的问题

- 无 `*.orig` / `*.rej` / `*.bak` 残留
- 无截图/视频产物（`test-results/`、`playwright-out/` 均为空）
- 无本地 DB 文件、无 `.env` 被跟踪（`.env` 与 `.env.*` 自始被忽略）
- 无 `node_modules` / `.venv` / `dist` 被跟踪

## 5. 清理后状态

`git status --porcelain` 只剩：

- 本轮**修改**：`.gitignore` `.prettierignore` `pyproject.toml`、签署包三件套、
  两个已存在的治理脚本、Design token、Admin view、API config/main
- 本轮**新增**：`scripts/governance_snapshot.py`、`scripts/mutation_probe.py`、
  `scripts/qa_all.ps1`、7 个测试文件、`docs/engineering/**`、`docs/frontend/**`、
  `docs/reality_audit/snapshots/baseline.json`
- 无 patch 垃圾、无 agent 临时文件、无缓存目录

## 6. 结论

`REPOSITORY_HYGIENE = PASS`（清理后工作区干净；Evidence / Source / Audit / Migration 一条未删）。
