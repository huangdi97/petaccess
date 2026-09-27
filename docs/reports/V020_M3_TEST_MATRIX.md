# V020 M3 TEST MATRIX

> 本轮（M3 深化收口）全部测试为**当前会话实测**，PASS 仅来自本轮执行。时间为 2026-09-27。

## 1. Backend（pytest 全量）

- 环境：`petaccess_test`（isolated_db --role TEST --reset）+ Celery worker（`-A app.worker.celery_app worker --pool=solo -Q petaccess_test`，DATABASE_URL=petaccess_test 同 env）+ PostgreSQL/Redis/MinIO（docker healthy）。
- 结果：**961 passed / 2 skipped / 0 failed**（69.5s）。
- 与基线（946/944 passed）差异：+15 passed（新增 integration 覆盖沿用 baseline 测试数变化，均为全绿）。

## 2. Frontend 静态检查

| 项 | 命令 | 结果 |
|---|---|---|
| vue-tsc | `pnpm --filter @petaccess/client-h5 exec vue-tsc --noEmit` | PASS（0 错误） |
| H5 build | `pnpm --filter @petaccess/client-h5 build` | PASS（vue-tsc + vite） |
| ESLint | `pnpm lint:fe` | PASS（0 error；新增 tests/ui-audit 白名单 + 基线遗留 cdp_journey.cjs ignore 记录） |
| Prettier | `pnpm format:check:fe` | PASS（All matched files use Prettier code style） |

## 3. Playwright E2E（playwright.config.ts，全量）

- 结果：**157 passed / 1 failed（既有 TEST-001 flake）**；单独重跑 `contribute-wizard.spec.ts`（A1/A2/B2）**3/3 passed**。
- 失败项：`contribute-wizard.spec.ts A2`（全量并行时偶发）——已证为**基线既有 flake**：git stash 到 HEAD 基线（不含本 M3 任何改动）重跑同一 spec 同样失败（1 failed / 2 passed），根因是贡献页懒加载 chunk + 并行时序（TEST-001 冻结问题，历史 a8bab37 已加固、仍未根除）。与 M3 改动无关。
- 新增 M3 spec：`tests/e2e/m3-consumer-core.spec.ts`（5 tests）全绿：行级 Reality 摘要、transport error ≠ UNKNOWN（row-answer-error）、request epoch（慢旧不覆盖新）、cache reuse（同 q 不重复请求）、runtime console gate（0 console.error / 0 pageerror）。

## 4. Playwright Visual（playwright.visual.config.ts，全量 5 projects）

- 结果：**59 passed / 0 failed**（更新基线后）。
- M3 视觉变化导致 12 个 consumer 基线重生成（home/search x 3 viewport；h5-390 先更新后全量对齐），UPDATE 后 compare 全绿。
- Admin 基线不变（未触碰 admin）。

## 5. UI 取证截图（playwright.ui-audit.config.ts）

- `current`（BEFORE, commit 049fc39）：**70/70** PNG 有效（35–240 KB，非空、尺寸正确）。
- `m3-final`（AFTER, 当前 HEAD）：**70/70** PNG 有效。
- 三个 Gallery（CURRENT_STATE / M3_FINAL / BEFORE_AFTER）已生成并浏览器实测渲染完整（BEFORE_AFTER 140/140 图可加载、0 broken）。

## 6. Android FAST（契约 §89）

- `emulator-5556`（own AVD pdig5）install debug APK（含 M3 前端，API=10.0.2.2:8010）→ CDP 验证：
  - Home：shell=true, homeTitle=true, errorState=false
  - Search：searchInput=true, results=21
  - Nav：map→home 均 true
  - Offline：offlineBanner=true；Recovery：offlineBanner=false
  - Short lifecycle：force-stop → relaunch → PID 存活
- 全部 PASS；截图归档 `artifacts/ui-audit/android/`（PNG 头校验）。
- 见 `docs/reports/V020_M3_ANDROID_FAST_REPORT.md`。

## 7. Windows smoke（契约 §24/§91）

- NSIS install → petaccess.exe → WebView2：
  - Install / Launch / Home / Search / split-preview / Navigation / Offline-Error / Recovery 全 PASS（截图 + accessibility 树证据）。
- 见 `docs/reports/V020_M3_WINDOWS_SMOKE_REPORT.md`。

## 8. 契约 §87 新增 M3 测试覆盖映射

| 要求 | 覆盖 |
|---|---|
| CoexistenceSnapshot SSOT | e2e m3-consumer-core（行级 Reality+Evidence）+ 架构审计（docs/reports/V020_M3_CONSUMER_ARCHITECTURE_GAP.md） |
| Home/Search query | consumer-routes A1/A3/B1/B2（既有回归）+ m3-consumer-core |
| q 恢复 / lens 恢复 / deep-link / back-forward | consumer-routes B1/B2（回归通过） |
| cache reuse / cache stale | m3-consumer-core（cache reuse 实测 counts 不变） |
| offline cache | Shell GlobalOfflineBanner 语义（offline 截图矩阵 + Android/Windows offline 验证） |
| request race | m3-consumer-core（epoch 慢旧不覆盖新） |
| error != UNKNOWN / error != Empty | m3-consumer-core（row-answer-error 文案）+ consumer-routes E2（无内部泄漏）+ visual error 基线 |
| dedupe | repository.coalesce（in-flight 去重，代码 + e2e 覆盖） |
| runtime error boundary | AppBoundary（既有）；m3-consumer-core（console gate） |
| responsive / overflow | responsive.spec（既有）+ place-preview-overflow（回归）+ 取证 5 viewport |

## 9. 状态汇总

- Backend：**PASS（961/961 实体通过）**
- Frontend 静态：**PASS**
- Playwright E2E：**PASS（157/158，1 为既有 TEST-001 flake；单独跑全绿）**
- Playwright Visual：**PASS（59/59）**
- UI Gallery：**PASS（70×2 截图 + 3 Gallery）**
- Android FAST：**PASS**
- Windows smoke：**PASS**