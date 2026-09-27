# UI Reconstruction — Test Matrix（真实执行记录）

> 分支：`feat/ui-reconstruction-spatial-dossier`（HEAD 移动中）
> 环境：Windows 11 / PostgreSQL 42h healthy / Redis / MinIO
> 原则：只有真实执行的命令才记录 PASS；并行 contribute-wizard flake 按 TEST-001 语义标注。

## 1. 后端

| 门禁 | 命令 | 结果 | 证据 |
|---|---|---|---|
| 全量 pytest | `DATABASE_URL=…petaccess_test .venv/Scripts/python.exe -m pytest -q`（root testpaths: tests + services/api/tests；celery worker `--pool=solo -Q petaccess_test` 在线） | **961 passed / 2 skipped**（49.2s） | 见下“本次执行输出” |
| DB 隔离 | `scripts/isolated_db.py --role TEST --reset` | PASS（recreated, seed=demo） | 输出 DATABASE_URL/CELERY_TASK_QUEUE/REDIS_URL |
| media/OCR | 依赖 celery worker（`celery@Kaiser: OK pong`） | PASS | 3 条 media/ocr 不再超时 |

### 本次执行输出（截断尾部）
```
961 passed, 2 skipped, 1 warning in 49.22s
```

> 备注：早期会话存在 3 条 isolation 失败（Windows GBK reader-thread crash），
> `scripts/isolated_db.py` / `scripts/visual_db_reset.py` 已加入
> `subprocess.run(text=True, encoding="utf-8", errors="replace")` 修复；本次全量
> 运行不再复现，故按真实结果记录 961 passed。

## 2. 前端工程门禁

| 门禁 | 命令 | 结果 |
|---|---|---|
| vue-tsc | `pnpm exec vue-tsc --noEmit`（apps/client-h5） | PASS |
| client-h5 build | `pnpm exec vite build` | PASS（2.3–3.3s） |
| admin build | `pnpm admin:build` | PASS（2.7s） |
| eslint | `pnpm lint:fe`（`eslint .`） | PASS（修复：ui-reconstruction 测试加入 default project、cdp_probe.cjs 忽略） |
| prettier check | `pnpm format:check:fe`（`prettier --check .`） | PASS（3 个旧脚本已 format） |
| 单元 UI 状态守卫 | `pytest tests/unit/test_ui_states.py` | 8/8 PASS（组合组件 import 解析后） |

## 3. Playwright

### 3.1 主套件（playwright.config.ts，petaccess_e2e，自建 webServer）

| 组 | 文件 | 结果 |
|---|---|---|
| 导航/壳 | navigation.spec.ts、h5-shell.spec.ts | PASS |
| 核心旅程 | h5-journey.spec.ts（含查询上下文切换、双场所切换、共处边界） | PASS |
| 地图护照 | map-passport.spec.ts（B1/B2/B5） | PASS |
| 溢出 | place-preview-overflow.spec.ts、desktop-dpi.spec.ts | PASS |
| 响应式溢出 | responsive.spec.ts（**8 页 × 9 viewport**，含 place/reality/evidence） | **72/72 PASS** |
| 消费者契约 | consumer-contract-closure.spec.ts、m3-consumer-core.spec.ts | PASS |
| 其余 | empty-state、consumer-routes、endpoint-resolution、pa-icon-size、reality-trace、backend-down-home、contribute-wizard | PASS* |

**全量：189 passed（1.2m）**。\* contribute-wizard 并行偶发（TEST-001 家族）：单跑/重跑均 PASS，已在 PROJECT_STATE 标注为已知 flake 语义。

### 3.2 UI 重构矩阵（playwright.ui-reconstruction.config.ts，petaccess_visual :8011）

| 组 | 结果 |
|---|---|
| capture（final stage） | **90/90 PASS**（8 页 ready + 10 状态 × 5 viewport） |
| phase1-gate | PASS（5 断言 × 5 viewport） |
| phase3-gate | PASS（4 断言 × 5 viewport，API_PORT=8011） |
| a11y-gate（AC-R2） | **30/30 PASS**（6 断言 × 5 viewport） |

截图产物：`artifacts/ui-reconstruction/final/{ui-360,ui-430,ui-800,ui-1280,ui-1440}/*.png` 共 90 张，PNG 魔数/尺寸/非纯色抽样核验。

## 4. 关键状态覆盖（360/430/800/1280/1440）

| 页面 | ready | loading | empty | error | offline | unknown | stale |
|---|---|---|---|---|---|---|---|
| Home | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓（freshness 行） |
| Search | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ |
| Map | ✓ | — | ✓（map-empty） | ✓（桌面窗格 + 移动画布） | ✓（横幅） | — | — |
| Place | ✓ | ✓ | — | ✓（StateMessage） | — | ✓（place-unknown） | ✓ |
| Reality | ✓ | ✓ | — | ✓ | — | — | — |
| Evidence | ✓ | ✓ | — | ✓ | — | — | — |
| Contribute | ✓ | — | ✓（contribute-needs-place） | ✓ | — | — | — |

## 5. 性能（AC-R3 记录）

- Search/Map/Place 数据全部经 consumer repository 单缓存（CoexistenceSnapshot SSOT）；`enrichRows` 有界并发（bounded concurrency），无 N×request 爆炸（map-passport/consumer-contract 断言）。
- Map marker 状态与预览共用同一 snapshot 缓存：选中场所只发一次 `POST /places/{id}/coexistence`。
- 无 uncontrolled 图片加载；Evidence 无装饰性图片。
