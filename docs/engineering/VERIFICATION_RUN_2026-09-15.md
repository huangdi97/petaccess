# 验证跑 · 2026-09-15（GMT+8）

> 目的：在**未提交的工作区**上把所有门禁重新跑一遍，确认"报告里写的 PASS"在 HEAD 上仍然成立。
> 原则：跑不动的写 `NOT_RUN`，失败的写 `FAIL` 并给根因；不把"上次通过"当成本次通过。

## 1. 门禁结果（全部实测）

| 门禁 | 命令 | 结果 |
|---|---|---|
| 后端全量测试 | `pytest -q` | **PASS — 501 passed / 0 failed（54.80s）** |
| Ruff lint | `ruff check services/api services/worker tests scripts` | **PASS** |
| Ruff format | `ruff format --check …` | **PASS — 162 files**（修了 1 个格式化偏差） |
| Mypy | `mypy services/api` | **PASS — 77 source files** |
| ESLint | `pnpm lint:fe` | **PASS — 0 problems** |
| Prettier | `pnpm format:check:fe` | **PASS** |
| H5 typecheck | `vue-tsc --noEmit` | **PASS** |
| Admin typecheck | `vue-tsc --noEmit` | **PASS** |
| H5 build | `vite build` | **PASS** |
| Admin build | `vite build` | **PASS** |
| E2E | `playwright test` | **PASS — 16 passed / 0 failed（19.7s）** |
| 变异测试 | `scripts/mutation_probe.py` | 见 `TEST_MATRIX.md` §29（4/4 捕获） |
| `bandit` | `bandit -r …` | **NOT_RUN** — 已安装（1.9.4），执行被安全审批拦截 |
| `pip-audit` | — | **NOT_RUN** — 未安装 |

依赖栈：Postgres/PostGIS healthy、Redis healthy、MinIO up、API `:8010` `status: ok`、
**Celery worker 已启动**（全量 pytest 的前置条件）。

## 2. 本轮发现并修复的缺陷

### D-1（P1，真实缺陷）相对 API base 会让整个 H5 退化成错误态

- **位置**：`packages/api-client/src/index.ts::createClient`
- **症状**：首页/搜索/场所详情全部显示"加载失败：Failed to construct 'URL': Invalid URL"，
  E2E 7 例失败。
- **根因**：`main.ts` 的默认配置是相对路径 `"/api/v1"`（同域反代部署的正确写法），
  但请求构造是 `new URL(resolveBase() + path)` —— `new URL()` 不接受相对 URL，直接抛异常。
  也就是说**默认配置从来就跑不通**，只是此前本地构建一直传了绝对 `VITE_API_BASE` 把问题遮住了。
- **修复**：`resolveBase()` 在浏览器环境下把相对 base 锚定到 `globalThis.location.origin`
  （绝对 base 行为不变；非浏览器环境保持原样返回）。
- **验证**：不带 `VITE_API_BASE` 重新构建后，首页取到附近场所；E2E 16/16 通过。

### D-2（P2，卫生）测试提交方式污染开发库

- **位置**：`tests/integration/test_versioning_supersession.py`、`test_publish_atomicity.py`
- **症状**：跑一次就在开发库留下 45 place + 45 source。
- **修复**：夹具里的 `commit()` 改为 `flush()`（随用例事务回滚）；
  原子性用例改用 savepoint 演示"半发布"，不写库。
- **验证**：两文件仍全绿；并按外键顺序清掉了本轮已产生的残留行。

### D-3（P2，可观测性）全量 pytest 疑似卡死

- **症状**：跑到 43% 后长时间无输出，容易被误判为死锁。
- **根因**：Hypothesis 首次写 example DB（13.3s）+ 缺 Celery worker 时 4 个用例挂到超时。
- **修复**：`pyproject.toml` 增加 `timeout = 120` / `timeout_method = "thread"`，
  `pytest-timeout` 加入 dev 依赖；worker 启动命令写入 `LOCAL_DEV_WINDOWS.md`。
- **验证**：加超时后全量 54.80s 通过；最慢健康用例 13.33s，留 9 倍余量。

### D-4（P3）Ruff format 偏差

- `tests/integration/test_publish_atomicity.py` 一处断言换行不符合 `line-length = 100`；已格式化。

## 3. 未处理（已知，不在本轮）

| 项 | 状态 |
|---|---|
| `bandit` / `pip-audit` 结果 | NOT_RUN（审批/未安装），`SECURITY_AUDIT.md` 已如实标注 |
| 并发测试（§26）、视觉回归基线 | 仍未实现，见 `TEST_MATRIX.md` §4 |
| 30–50 Place 扩量 | **NOT_ALLOWED** —— `PILOT_REVIEW_PUBLISH_GATE = BLOCKED_HUMAN` |
