# PRODUCTION_STATE.md

> 最后结构性重核：2026-10-14（GMT+8）
>
> **GitHub 仓库事实优先。不要从本文件复制旧 SHA 当“当前 HEAD”。**
> 当前候选工作线为 draft PR #1 / `feat/ui-direct-craft-v8`；每次使用本文件时，
> 先读取远端 branch tip 与同一 HEAD 的 Actions 结果。

## 1. Current Phase

当前阶段不是 2026-09-14 的 `P0_PUBLISH_CLOSURE + UI_CORE_CLOSURE`。

当前真实主线是：

```text
v0.10-R1 product truth
+ Consumer Discovery v9 UI/UX candidate
+ one canonical Vue Consumer
+ Tauri 2 Windows / Android shells
+ Android Preview packaged-runtime acceptance
+ Human Visual Acceptance pending
```

PR #1 仍为 **Draft**。机器测试通过不自动等于 Human Visual Acceptance，也不授权 merge /
tag / Release。

## 2. Canonical implementation boundary

当前唯一 Consumer：

- `apps/client-h5` — Vue 3 + Vite Consumer；
- `apps/client-h5/src-tauri` — Windows / Android Tauri 2 runtime；
- `.github/workflows/android-preview.yml` — Android branch Preview；
- `.github/workflows/release-ci.yml` — signed Release 构建链。

`apps/client`（uni-app x）为 **`LEGACY_REFERENCE_ONLY`**：

- 不构建当前 Android；
- 不做 Human Visual Acceptance；
- 不做 Release；
- 不接受新产品功能；
- 不得把 synthetic marker / legacy Observation 等旧行为重新带回当前 Consumer。

## 3. Current Consumer / UI state

当前候选已经完成从“规则数据库 / 后台面板”向
**城市生活探索 × 真实空间 × 可信事实** 的重构。

核心页面：

- Home：Consumer Discovery hero、任务式入口、附近场所与可信事实；
- Search：地点发现列表 + Rule / Reality / Evidence 决策详情；
- Map：地图为主画布，结果面与 preview 降为上下文层；
- Place：场所 identity → Rule / Reality → 空间 / 设施 / 证据 dossier；
- Reality：现场事实时间线；
- Evidence：来源 / provenance / review 记录；
- Contribution：五类事实贡献入口与人工审核边界；
- Mine / Settings / Privacy / About 等二级页面已统一 Consumer shell 与 runtime page identity。

当前 UI 结论必须写成：

```text
UI_MACHINE_GATES = use latest same-HEAD Actions result
UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW
```

禁止把历史 screenshot、旧 oracle PASS 或**运行时输入已经变化**的旧 CI 结果拼成当前视觉验收。
如果 branch tip 只比 Android artifact commit 多文档/治理说明改动，可以复用该 runtime evidence，
但必须用 commit compare 明确证明 Android Preview 的触发范围内没有任何文件变化。

## 4. Android current state

### 4.1 Preview identities

普通 Android Preview：

- package：`com.petaccess.map.preview`
- label：`PetAccess Preview`
- build：debug
- release keystore：**NO**
- store artifact：**NO**
- 可与 `com.petaccess.map` 正式包并存。

自动生成：

1. `x86_64 emulator` — API 指向 `10.0.2.2:8000/api/v1`；
2. `ARM64 USB device` — API 指向 `127.0.0.1:8000/api/v1`，需要
   `adb reverse tcp:8000 tcp:8000`。

### 4.2 Standalone Phone Preview

脱离电脑直接装手机需要一个**手机可达的真实 HTTPS PetAccess API**。

状态由 `Android Phone Preview APK` workflow 的 readiness 给出：

- 有 `PETACCESS_PHONE_PREVIEW_API_BASE` 或手动 `api_base` → `READY`；
- 没有 → `BLOCKED_BY_API_BASE`；
- blocked 只阻塞 standalone Phone Preview，不阻塞 emulator / USB Preview。

不得把 localhost、`10.0.2.2` 或临时假地址包装成 standalone phone build。

### 4.3 Packaged Android acceptance

Android runtime evidence 已升级为**真实打包 WebView**门禁，而不是“能安装 + 有截图”：

- 所有 Router 页面 identity；
- Place overview / rules / space；
- 真实 CI 登录后的贡献 / Mine / Privacy / Pets / Notifications / Boundary / Pet New；
- governed scene media 解码；
- Search / Pet New 真实 adb 输入 + IME；
- phone-m / ~360dp / ~430dp / tablet 宽度矩阵；
- horizontal overflow；
- safe-area overlap；
- Evidence → Android system Back → Reality；
- fresh Home → Android system Back → Activity 离开前台；
- offline banner → online recovery；
- Activity Home / resume；
- API 35 + API 36 runtime；
- offline HTML Android Runtime Review Board。

最终 Android acceptance 以最新 `Android Preview APK` Actions run 的 artifact / coverage JSON 为准，
不能引用历史截图替代。


### 4.4 Latest verified Android Preview snapshot

截至 2026-10-14（GMT+8），已对候选 commit
`9719576d37c0ac6ec80deaba68e57f21ee30e7f7` 完成同一 runtime-input scope 的验证：

- Android Preview workflow run：`38484246593` → **SUCCESS**；
- ARM64 USB Preview APK → **SUCCESS**；
- x86_64 Emulator Preview APK → **SUCCESS**；
- API 35 packaged runtime smoke → **SUCCESS**；
- API 36 packaged runtime smoke → **SUCCESS**；
- Android workflow 的后台 API / `uv` 生命周期误红已修复，workflow overall 现在真实为 SUCCESS。

同 run 产物：

- `petaccess-android-preview-usb-device-9719576d37c0ac6ec80deaba68e57f21ee30e7f7`；
- `petaccess-android-preview-emulator-9719576d37c0ac6ec80deaba68e57f21ee30e7f7`；
- `petaccess-android-preview-runtime-api35-9719576d37c0ac6ec80deaba68e57f21ee30e7f7`；
- `petaccess-android-preview-runtime-api36-9719576d37c0ac6ec80deaba68e57f21ee30e7f7`。

同一候选的 PR CI、UI Direct Validation、UI Direct Visual、Public Preview Stack Validation
与 Windows Preview Runtime 也均为 **SUCCESS**。

这只授权写成“当前候选的机器与 packaged-runtime gate 已通过”；**不等于**
`UI_HUMAN_VISUAL_ACCEPTANCE = PASS`、signed Release 已授权或 Public Beta 已授权。

## 5. Product truth invariants

以下边界仍为产品不变量，不得为了视觉或 demo 改写：

- Rule ≠ Reality；
- Observation ≠ Rule；
- StaffResponse ≠ OperatorPolicy；
- Facility ≠ EntryPolicy；
- No Observation ≠ No Animal Presence；
- UNKNOWN ≠ ALLOWED；
- 只使用真实场所坐标；
- 无经审核真实场景媒体时，不伪造“场所照片”；
- 用户贡献先进入 review，不自动改变规则；
- AI 不代替具名人类做最终规则裁决。

## 6. Current external gates

真正仍需外部输入的主要事项：

| Gate | Current state | What is missing |
|---|---|---|
| GOV-01 | BLOCKED_HUMAN | R2 规则候选的具名人类逐条最终签署 |
| Tencent real map | BLOCKED_EXTERNAL | client/server Key + provider configuration |
| Real Vision/OCR | BLOCKED_EXTERNAL | provider 选型 +真实 API key |
| Legal review | BLOCKED_EXTERNAL | 执业律师审阅法律/隐私草案 |
| Platform submission | BLOCKED_EXTERNAL | 应用商店/小程序等主体与审核 |
| Production domain/compliance | BLOCKED_EXTERNAL | 域名、备案、正式主体信息 |
| Signed Release public API | BLOCKED_EXTERNAL | `PETACCESS_PUBLIC_API_BASE=https://.../api/v1` |
| Standalone Phone Preview | BLOCKED_BY_API_BASE until configured | `PETACCESS_PHONE_PREVIEW_API_BASE` |

`B-01` HBuilderX / uni-app x 已 RETIRED；`B-03` Android 工程签名链已 RESOLVED。
它们不是当前 Android blocker。

## 7. Historical evidence is not current state

旧文档中的以下内容只能作为历史证据，不能直接复用为当前 PASS：

- 2026-09-14 的固定 HEAD `53c4c03...`；
- 当时的 Docker Desktop / PostgreSQL / Redis / MinIO 本机状态；
- 当时的 pytest / Playwright 数量；
- 旧 UI_CORE_CLOSURE；
- 旧 Android/HBuilderX 路径；
- 旧 screenshot / runtime evidence。

特别是“Docker 当前运行中”属于当时机器的观测。当前本地 Agent需要数据库时，应重新探测；
GitHub CI 的 container PASS 也不能反推用户当前 Windows Docker Desktop 一定在线。

## 8. Current release interpretation

当前候选不能写成 `READY_FOR_PUBLIC_BETA = YES`。

准确表述：

```text
CANONICAL_CONSUMER_ARCHITECTURE = CLOSED
ANDROID_PREVIEW_BUILD_CHAIN = VERIFIED
ANDROID_RUNTIME_ACCEPTANCE = PASS_AT_LATEST_VERIFIED_SNAPSHOT
SIGNED_RELEASE_RUNTIME = BLOCKED_BY_PUBLIC_API
RULE_DATA_PUBLISH = BLOCKED_HUMAN
UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW
PUBLIC_BETA = NOT_AUTHORIZED
```

## 9. Next actions

按优先级：

1. 对最新 Android Runtime Review Board 与 UI HUMAN_REVIEW 包做**具名人工视觉验收**；
   机器 PASS 不能替代该步骤；
2. 若要脱离电脑直接在安卓手机体验，部署可达 HTTPS Preview API、配置
   `PETACCESS_PHONE_PREVIEW_API_BASE`，解除 `BLOCKED_BY_API_BASE` 后生成 standalone Phone Preview；
3. 获取腾讯地图 client/server Key 后执行 `require_real_map=true` packaged validation；
4. 导入/签署允许发布的真实 pilot 数据与场景媒体；不得用 E2E fixture 丰富公网 Preview；
5. 由具名人类完成 GOV-01 规则数据签署；
6. 完成生产域名、法务与平台外部 gate 后，才评估 signed Release / Public Beta。

## Truth Rule

**Never mark PASS without same-scope, runtime-equivalent evidence.**

证据优先使用同 HEAD。若证据 commit 早于当前 tip，只有在 commit compare 明确证明
Android/Consumer/API/design-token/acceptance 等对应 workflow 输入范围内 **0 runtime-relevant
delta** 时，才允许复用；一旦运行时输入发生变化必须重跑。正式 tag / signed Release 则始终以
最终发布 HEAD 重新验证。

机器门禁、真实 Android runtime、Human Visual Acceptance、规则治理签署、Production Release
是不同层级；任何一层 PASS 都不能自动替代另一层。
