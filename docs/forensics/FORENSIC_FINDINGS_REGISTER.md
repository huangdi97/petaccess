# FORENSIC FINDINGS REGISTER（2026-09-26）

> 来源：F02 工程门禁重跑（0 FAIL / 60 REVIEW / 34 WARN）+ 本轮代码审计。severity：CRITICAL/HIGH/MEDIUM/LOW。
> 全部登记项带 tracking ID（FF-xxx）；修复后复审计逐项复核。

## CRITICAL
- 无。

## HIGH
- **FF-001（REG-003）packaged runtime API base 依赖 Vite proxy**：`apps/client-h5/src/main.ts` 默认 `VITE_API_BASE ?? "/api/v1"`；Tauri packaged（Windows/Android）无 Vite server → packaged 数据面不可达。证据：代码 + vite.config 注释 + 矩阵实机（logcat/console 见 F03/F09）。修复：ApiEndpointProvider（WEB/TAURI_DESKTOP/TAURI_ANDROID 运行时解析），`10.0.2.2` 仅限 Android dev。状态：待修复（回归测试随修复提交）。

## MEDIUM
- **FF-002 HOME/Search 数据流在 packaged 下退化为 full-offline**（REG-003 的 UI 侧表现）：Empty-First 未灰屏（A/B 实测渲染正常），但数据面依赖 proxy 会在 packaged 下整体失败。与 FF-001 同源。
- **FF-003 检测到旧/新两代 Cosmetic 组件并存**：`apps/client-h5/src/views/HomeView.vue` 引用 v0.1.0 代组件（`components/AppShell.vue` 26L、`SkeletonList.vue`、`StateMessage.vue`、`StatusBadge.vue`、`answer.ts`），而 App.vue 已切到 M2 代 `ConsumerAppShell`；HomeView 未被 M2+ 产品化（Search/Map/Place/Contribute 已产品化）。影响：维护性/一致性，不阻断 boot（A/B 渲染实测正常）。跟踪：F08 页面矩阵标记 PASS_WITH_DEBT。
- **FF-004 `scripts/check_engineering_quality.py` 60 项 review**：函数 >60 行 / cyclo>15 集中在 `services/api/app/api/v1/`（admin.py quality_dashboard 182L/cyclo25、media.py upload_media 99L/21、reality.py 多函数 >60L 等）。属既有技术债（M1 已登记），不影响 runtime/security；保持跟踪。
- **FF-005 CI 与本地工具链漂移**：CI Android 用 JDK 17 + Ubuntu + NDK 27.1.12297006；本机 JDK 21 + Windows；编译产物等价（B/C 构建成功且签名一致）。见 F11。

## LOW（warn 34 项，代表性抽查）
- **FF-006** 文件 >250 行系列：`services/api/app/api/v1/rules.py`(275)、`models/rule.py`(292)、`rulespec/animal_scope.py`(292)、`rulespec/source_scope_semantics.py`(291) 等（M1 既有）。
- **FF-007** Vue 组件 >150 行系列：`ContributeRealityForm.vue`(200)、`ContributeSignageForm.vue`(195)、`PlacePreview.vue`(200)、`DesktopRail.vue`(198)、`BoundaryView.vue`(200)、`ContributeView.vue`(171) 等（M1 既有，scanner 为 warn 非 fail）。
- **FF-008** 依赖/工具标记：`vswhom-sys` 需 MSVC cl.exe（Windows host 构建）；PowerShell `>` 二进制重定向陷阱（REG-002）——均为工具链/自动化层，已在本 Goal 规避并留档。

## 已排除项（记录而非盲改）
- 后端 full regression：945 passed/2 skipped（0 fail）→ 无后端失败路径残留。
- `apps/client-h5/src-tauri/gen/android`（generated）：compileSdk/targetSdk=36（HEAD 版生成）、minSdk=24，本机 platforms 34/35/36 齐备；v0.1.0 生成版为 compileSdk 35 → 平台依赖差异记录于 F07/F11，不改生成代码。

## 处置状态
- 待修复：FF-001/FF-002（+ 随附回归测试，fail-before/pass-after 演示）。
- 保持跟踪（PASS_WITH_TRACKED_DEBT）：FF-003..FF-008 全部有 ID 与理由。