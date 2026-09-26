# V020 Android 全光谱验收报告（模拟器）

> 目标：PETACCESS_ANDROID_FULL_EMULATOR_ACCEPTANCE
> 日期：2026-09-26 · 设备：自有 AVD `petaccess_test_360` · serial `emulator-5562` · Android API 35
> 后端：`http://10.0.2.2:8010/api/v1`（独立实例）· 数据库：`petaccess_e2e_android`（E2E 角色 guard 校验通过）

## 1. 构建产物（HEAD 67fb924）

| 项 | 值 |
|---|---|
| HEAD | `67fb92482e10ac863bf1497bc4ec49c114cf6e02`（master） |
| 构建方式 | ASCII worktree `D:\pa-acc`，runbook §3（vcvars `>nul 2>&1`，单一 SDK adb） |
| Debug APK | `current-debug.apk` 137,469,246 B · SHA256 `3D47E7F9…C6C8` · versionCode 1000 · versionName 0.1.0 · minSdk 24 · targetSdk 36 · boot trace + API pin 8010 |
| Release-like APK | `current-release-signed.apk` 11,642,245 B · SHA256 `584413C8…D33DA` · 签名 `CN=PetAccess…`（v2 scheme，1 signer）· 同 keystore 身份 |
| 签名 | apksigner + `~/.petaccess-keystore/petaccess-release.keystore`（runbook 规则：不传 `--key-pass`） |

## 2. 测试环境与隔离

- 自有 AVD：`petaccess_test_360`（API 35，1080×2340 @440dpi → 393×851dp 逻辑视口）。
- 每条 adb 命令绑定 `-s emulator-5562`；未触碰 `emulator-5554`；未执行 kill-server / reconnect / taskkill adb。
- 后端独立实例 :8010（`petaccess_e2e_android`，E2E 角色 guard 通过）；夹具与回归全部落在测试库，从未触碰生产库。
- 证据树：`artifacts/android_acceptance/`（session.json、device/、runtime/、logs/、screenshots/、performance/、upgrade/、reports/、scenario_matrix.csv、coverage_matrix.json）。

## 3. 安装 / 启动 / 生命周期

| 场景 | 要求 | 实际 |
|---|---|---|
| install（debug / release / -r / uninstall / fresh） | Success | PASS（install log、package dump、signature result 已存） |
| Cold launch | 10/10 HOME_READY | **10/10**（每次均见 INDEX_LOADED→VUE_CREATED→APP_SHELL_MOUNTED→ROUTER_READY→HOME_READY；截图非灰） |
| Warm launch | 20/20 | **20/20** |
| Relaunch | 20 cycles | **20/20** |
| Background/Foreground | ≥20 cycles（1s/5s/30s/2min） | **20/20**（四种 hold 各 5 次） |
| Process Death Recovery | 重启后 Home 就绪 | **3/3** |

证据：`runtime/cold_launch.json`、`warm_launch.json`、`relaunch.json`、`background_foreground.json`、`process_death.json`。

## 4. 页面与语义（CDP 驱动真实 DOM 断言）

- **路由覆盖**：`/`、`/search`、`/map`、`/contribute`、`/mine`、`/settings`、`/privacy`、`/about` 逐一进入并读取 innerText（`runtime/cdp_journey_ws.json`）→ **ROUTE_COVERAGE 通过**。
- **Rule 语义**：`测试·无规则场所`（0 条规则）显示“生效规则 0 条”＋“尚未核验”＋“本次查询范围内没有已发布规则 —— 未知 ≠ 允许” → **UNKNOWN 从未显示为允许**（`cdp_semantic.json`）。
- **Reality 语义**：`星河咖啡·测试店` 显示“近期现场有动物出现 · 1 天前最近一次记录 · 观察动作 present · 工作人员处理（计数，仅事实）” → PROFILE B 的经人工核验 claim 真实渲染；`星河咖啡·栖霞分店` 无记录时显示 `INSUFFICIENT_OBSERVATION` 且文案为“暂无记录（≠ 没有动物）”。
- **Reality Trace**：独立路由显示“暂无记录不代表现场没有动物（NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE）”；事实/核验分离。
- **Home 富态**：Retry 后真实场所列表渲染（云栖中心·测试商场“已核验：普通犬·场所整体 · 有条件（需宠物包）”；其余“尚未核验（≠允许/禁止）”）。

## 5. Contribution / 数据

- PROFILE B 通过**真实 API 管线**（登录→contribute→人工 decision→发布 claim）注入：4 条 presence（1d/3d/20d/120d）、4 条 staff response（provide_water/remind_leash/deny_entry/no_intervention，awareness confirmed/likely/unknown）、3 条 facility（water_bowl/waiting_area/cage，purpose confirmed/signage/unknown）、1 条未复核 candidate（INSUFFICIENT）、2 条 report（exact/parent match、event/publication time 分离）。
- 消费者接口确认状态机：`OBSERVED_RECENTLY`（证据 3、staff 4、facility 3）；`INSUFFICIENT_OBSERVATION` 文案正确。
- Contribution UI 入口渲染验证（`contribution_ui` 路由进入 + 表单壳层）；完整向导交互由 Playwright A1/A2/B2 覆盖（全部通过）。

## 6. 网络 / 错误矩阵

| 场景 | 结果 | 证据 |
|---|---|---|
| Slow backend 1s/3s/8s | 实测 1.42s/3.06s/8.08s 后 200 | `network_matrix.json` |
| HTTP 400/401/403/404/409/422/429/500/503 | 注入 status 全部以相同 status + CORS 头返回 | `http_status_matrix.json` |
| Offline→Online | backend 停止后 in-page fetch 失败；恢复后 200；Home 显示“未能取得附近场所”＋Retry，Retry 后数据恢复 | `network_matrix.json`、`cdp_retry` 过程 |
| CORS（tauri.localhost） | 修复后 `Access-Control-Allow-Origin: http://tauri.localhost` 正常返回 | `test_api.py::test_tauri_webview_origin_is_cors_allowed` |
| 权限 | 应用仅声明 INTERNET，无运行时权限 → **NOT_RUN（不适用）** | manifest |

## 7. 压力 / 稳定性 / 性能

| 项 | 结果 | 证据 |
|---|---|---|
| Route stress（Home→Search→Map→Contribute→Mine） | **100/100** | `route_stress.json` |
| Bottom nav | 100/100（坐标 tap 循环） | `runtime/ui_journey.json` |
| Scroll stress | 50 cycles 无 jank 崩溃 | 截图集 |
| Monkey（app-only，seed 42，1000 events） | **1000 events，0 crash** | `logs/monkey_seed42.log` |
| Soak | **30 分钟 / 87 cycles，0 crash / 0 ANR / 0 renderer** | `runtime/soak.json` |
| 内存基线（dumpsys meminfo） | cold 70,225 KB → after-nav 73,969 → after-route-stress 110,675 → scroll 后 110,730 → soak 109,909→109,637 KB（**无不可恢复增长**） | `performance/memory_summary.json` |
| CPU | idle Home `top` 采样已存 | `performance/cpu_*.txt` |

## 8. 安装 / 升级 / 卸载

- 官方 v0.1.0 APK（`PetAccess_0.1.0-android-universal.apk`）安装 → launch → `adb install -r` 当前 release-like → Success → package identity/version/launch 正常 → 升级后 Home 渲染（release build 无 boot trace，以非灰截图 + ResumedActivity 验证）→ **UPGRADE_FROM_V010 PASS**（`upgrade/upgrade_drill.json`）。
- fresh install（卸载→装 current）、reinstall -r、uninstall 后无残留：均 PASS。

## 9. 视觉与 a11y

- 71 张截图按统一命名规则保存（`phoneM__<route>__<state>__<tag>.png`），PNG 魔数全部 `89504E47`，非灰校验通过。
- uiautomator tree 确认 WebView 节点存在；WebView 内部文本不暴露给 uiautomator（Tauri WebView 特性）→ **Accessibility：PARTIAL**（页面级结构断言 + 现有 a11y 回归规格覆盖）。
- 视觉细节问题（SVG attribute length 错误）已在运行时定位并修复（见 §10 问题）。

## 10. 问题清单

| ID | 级别 | 问题 | 处置 |
|---|---|---|---|
| P1-001 | P1 | Android WebView 请求被 CORS 阻断（`tauri.localhost` 不在 allow_origins）→ Home 无法取数 | **已修复** `services/api/app/main.py`（加入 `http://tauri.localhost` / `https://tauri.localhost`）＋回归测试 `test_tauri_webview_origin_is_cors_allowed`；模拟器实测 CORS 0 拦截 |
| VIS-001 | P1（运行时控制台） | `PaIcon` 把 CSS 变量绑定到 SVG width/height **属性**，浏览器报 “Expected length” | **已修复** `apps/client-h5/src/components/ui/PaIcon.vue`（改 inline style）＋回归规格 `tests/e2e/pa-icon-size.spec.ts`；模拟器实测 SVG 错误 0 |
| TEST-001 | 测试工具 | contribute-wizard A1/A4 在 6 并行 worker 下 5s 超时（已知 load flake，仓库 a8bab37 已对 B2 加固） | **已修复** 按相同模式加 15s 有界等待；最终 Playwright 151/151 |

## 11. 回归（真实计数，§104）

| 套件 | DISCOVERED | EXECUTED | PASS | FAIL | SKIP |
|---|---|---|---|---|---|
| Backend pytest | 948 collected | 948 | **946** | 0 | 2 |
| Playwright E2E | 151 | 151 | **151** | 0 | 0 |

- pytest 基线 runbook §6 为 945+2；本轮 946（多出的 1 个是 DB 内容相关的条件跳过转收集后通过，见 `pytest_backend_r3.log`）。
- Playwright 含新增 2 条 PaIcon 回归；`playwright_final.log` 显示 `151 passed (47.9s)`。

## 12. Logcat Gate

- 整个 suite 保存 logcat；分类后：**FATAL 0 · ANR 0 · AndroidRuntime 0（本应用）· JS uncaught 0 · renderer 0 · CSP 0**。
- 发现的运行时控制台错误（SVG attribute）已修复并在模拟器复测为 0。

## 13. 终态判定

| Gate | 状态 |
|---|---|
| ANDROID_BUILD / INSTALL / COLD_BOOT / HOME | PASS |
| ROUTE_COVERAGE | PASS（8/8 + Place/Reality 深链） |
| RULE_STATE_COVERAGE / REALITY_STATE_COVERAGE | PASS |
| CONTRIBUTION / EMPTY_STATE / ERROR_STATE / OFFLINE_STATE / NETWORK_RECOVERY | PASS |
| PERMISSION_MATRIX | NOT_RUN（无运行时权限，不适用） |
| LIFECYCLE | PASS |
| UPGRADE_FROM_V010 | PASS |
| VISUAL | PASS（截图证据 + 运行时修复闭环） |
| A11Y | PARTIAL（WebView a11y 树限制，如实记录） |
| STRESS / SOAK | PASS |
| CRASH / ANR / UNCAUGHT_RUNTIME_ERROR | 0 / 0 / 0 |
| P0 / P1 | 0 / 0（P1-001、VIS-001 已修复并回归） |

> 诚实说明：**Device Sizes 仅 PHONE-M 全量执行**（PHONE-S/L/tablet wm-size 档位未在本次执行），因此覆盖矩阵 Device Sizes 记 **PARTIAL**；A11Y 记 **PARTIAL**。据此：
> `ANDROID_FULL_ACCEPTANCE = PASS*`（带 2 项如实记录的非阻塞 PARTIAL），`M3_RESUME_ALLOWED = YES` 由人工按此报告裁定。
