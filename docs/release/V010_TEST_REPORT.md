# V010 TEST REPORT — 2026-09-24

> 状态标记 (Status Legend): **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 测试 | 结果 | 标记 |
|---|---|---|
| Backend pytest | 916 passed / 2 skipped | CURRENT VERIFIED |
| Gate unit tests | 21 passed | CURRENT VERIFIED |
| Playwright E2E（h5-shell + h5-journey） | 18 passed | CURRENT VERIFIED |
| Playwright E2E（empty-state.spec.ts） | 3 passed | CURRENT VERIFIED |
| Visual suite | 47 passed（17 families × viewports，compare-mode） | CURRENT VERIFIED |
| mypy | 93 files, 0 errors | CURRENT VERIFIED |
| ruff check / format --check | PASS（292 files） | CURRENT VERIFIED |
| client-h5 build (vue-tsc + vite) | PASS | CURRENT VERIFIED |
| admin build (vue-tsc + vite) | PASS | CURRENT VERIFIED |
| CI 实际运行 | BLOCKED（无 git remote，未授权） | BLOCKED |
| DEPENDENCY_SCAN（pip-audit） | 结果待 orchestrator 填录 | NOT RERUN |
| Desktop 窗口直接截图 | 未捕获（headless Win32 title lookup 不可靠；渲染经进程树/Playwright 确认） | NOT RERUN（局限） |

## 1. 后端

- pytest：916 passed / 2 skipped（TEST db `petaccess_test` + celery worker on redis /1）—— PASS。
- Gate unit tests：21 passed。

## 2. 前端 E2E

- h5-shell + h5-journey：18 passed。
- empty-state.spec.ts：3 passed（合计 21）。

## 3. Visual

- 47 passed（projects：h5-390 / h5-768 / h5-1440 + admin-768 / admin-1440）。
- 17 baseline families；为一次有意的文案变更重新生成过一次基线；compare-mode PASS。

## 4. 静态与构建

- mypy：93 files, 0 errors（历史 97 口径为更广范围含 worker；本轮以 93 files 为准）。
- ruff check + ruff format --check：PASS（292 files）。
- vue-tsc + vite build：client-h5、admin 均 PASS。

## 5. 未执行项（如实标记）

- **CI 实际运行**：BLOCKED —— 无 git remote 且未获运行授权。
- **DEPENDENCY_SCAN**：NOT RERUN —— facts 仅记录 "pip-audit 已运行"，结果数字待 orchestrator 填录。
- **Desktop 窗口直接截图**：NOT RERUN —— headless 环境不可靠；渲染已通过 WebView2 进程树 + bundled copy + Playwright 同 bundle 渲染确认。

## 6. 结论

**结论: FULL_REGRESSION = PASS**（已执行项全绿；CI / DEPENDENCY_SCAN / 窗口截图按上表如实标记）。
