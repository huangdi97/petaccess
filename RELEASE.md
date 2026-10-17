# RELEASE.md — PetAccess 发布状态与下一次发布门禁

> 最后重核：2026-10-14（GMT+8）
>
> GitHub Release / tag 事实优先于旧发布计划。本文件不授权创建新 tag 或 Release。

## 1. 已发布事实

GitHub 当前已有公开 Release：

- tag：`v0.1.0`
- title：`v0.1.0 — Early Preview`
- published：2026-09-24
- draft：false
- prerelease：false

Release 资产：

- `PetAccess_0.1.0-android-universal.apk`
- `PetAccess_0.1.0_x64-setup.exe`
- `SHA256SUMS.txt`

因此旧文档中的“`RELEASE_V0_1_0_AUTHORIZATION` 未授予前不创建 v0.1.0 Release”
只能作为**发布前历史流程说明**，不能再解释成“v0.1.0 当前未发布”。

不要重新创建、移动或覆盖 `v0.1.0` tag / Release。

## 2. 当前开发候选不是 v0.1.0 Release

当前 Consumer/UI 候选位于：

```text
draft PR #1
feat/ui-direct-craft-v8
```

它已经明显晚于 v0.1.0 发布内容，包含 Consumer Discovery UI、Tauri Android Preview、
packaged runtime acceptance、Reality / Evidence / Contribution 等后续工作。

当前 PR 的机器 PASS **不自动授权**：

- 修改现有 `v0.1.0` Release；
- 新建 `v0.1.1` / `v0.2.0` 或其他 tag；
- 上传新的 signed/store artifact；
- 宣称 Public Beta；
- 合并 master。

下一版本号与发布授权必须由人类明确决定。

## 3. Canonical release architecture

当前正式 Consumer / runtime 边界：

- Consumer：`apps/client-h5`
- Windows：`apps/client-h5/src-tauri`
- Android：`apps/client-h5/src-tauri`
- signed workflow：`.github/workflows/release-ci.yml`
- Android branch Preview：`.github/workflows/android-preview.yml`
- standalone Phone Preview：`.github/workflows/android-phone-preview.yml`

`apps/client`（uni-app x）为 `LEGACY_REFERENCE_ONLY`，不得重新进入 Release。

Preview package：

```text
com.petaccess.map.preview
PetAccess Preview
debug
releaseArtifact=false
storeArtifact=false
```

正式 package：

```text
com.petaccess.map
```

Preview APK 永远不能直接提升为 signed Release。

## 4. 下一次 signed Release 的硬门

### 4.1 Same-HEAD engineering gates

最终候选同一 HEAD 至少需要：

- PR CI PASS；
- UI Direct Validation PASS；
- UI Direct Visual PASS；
- secret scan PASS；
- engineering quality gate PASS；
- frontend / backend / migration required checks PASS；
- 对应 Android Preview packaged-runtime evidence PASS。

历史 HEAD 的 PASS 不得拼接到新 HEAD。

### 4.2 Human visual gate

当前仍要求：

```text
UI_HUMAN_VISUAL_ACCEPTANCE = PASS
```

Android/Web/Windows 机器截图不能自动提升成人工视觉通过。

### 4.3 Signed runtime API — fail closed

Signed Windows / Android 不能继续使用开发端点。

必须配置：

```text
PETACCESS_PUBLIC_API_BASE=https://<真实域名>/api/v1
```

并满足：

- 绝对 HTTPS；
- 无用户名/密码；
- 无 query / fragment；
- 路径以 `/api/v1` 结尾；
- `/health` 为真实 PetAccess health；
- `/api/v1/ping` 为真实 PetAccess API；
- `Origin: http://tauri.localhost` 的 CORS 响应正确；
- signed Tauri CSP 不含 `localhost`、`127.0.0.1`、`10.0.2.2` 开发 origin。

由：

- `scripts/release/verify_public_api.cjs`
- `scripts/release/generate_tauri_release_config.cjs`

执行 fail-closed 检查。

缺少该真实 HTTPS API 时：

```text
SIGNED_RELEASE_RUNTIME = BLOCKED_BY_PUBLIC_API
```

不得用 Preview API、USB reverse 或假域名让 release job 变绿。

### 4.4 Android signed artifact

正式 Android job 必须：

- 使用 `com.petaccess.map`；
- 使用正式 release keystore Secrets；
- 构建目标 ABI 与 release policy 一致；
- `apksigner verify` PASS；
- 保存 signer certificate evidence；
- AAPT badging 与 version/package 事实一致；
- 生成 SHA256。

Debug Preview signer 不可作为 release signer。

### 4.5 Product / governance external gates

下一次 Public Beta / production release 仍需分别满足其对应范围：

- GOV-01：具名人类规则审查与签署；
- 法律文本执业律师审阅；
- 正式运营主体、域名、备案与隐私信息；
- 目标应用商店 / 平台审核；
- 若宣称腾讯真实地图：真实 Tencent client/server key + packaged validation；
- 若宣称真实 Vision/OCR：真实 provider + key + runtime evidence。

不要把这些外部 gate 混成一个笼统的“工程没做完”。

## 5. Android Preview 与 Phone Preview

### Android Preview APK

自动分支 Preview 提供：

- x86_64 emulator build；
- ARM64 USB-device build；
- API35 / API36 packaged runtime acceptance；
- Android Runtime Review Board。

USB ARM64 build 依赖：

```bash
adb reverse tcp:8000 tcp:8000
```

它适合真机开发验收，但不是脱离电脑的 standalone build。

### Android Phone Preview

Phone Preview 需要手机可达的真实 HTTPS API：

```text
PETACCESS_PHONE_PREVIEW_API_BASE=https://.../api/v1
```

readiness：

- `READY` → 构建 ARM64 standalone Debug Preview；
- `BLOCKED_BY_API_BASE` → 不构建 standalone 包；
- blocked 不影响普通 emulator / USB Preview。

Phone Preview 仍然不是 signed/store Release。

## 6. 下一次发布操作纪律

在下一版本号和发布授权明确前：

- 不创建 tag；
- 不创建新 GitHub Release；
- 不覆盖 v0.1.0 assets；
- 不修改 v0.1.0 tag 指向；
- 不把 draft PR artifact 当 release asset。

真正进入下一次发布时，应先冻结：

1. version；
2. final commit SHA；
3. Human Visual Acceptance；
4. public API；
5. external governance/legal/platform gates；
6. release notes；
7. artifact names / checksums。

然后才执行 tag-triggered `release-ci.yml`。

## 7. 发布后验证

任何未来 signed Release 都必须重新：

1. 从 GitHub Release 下载，而不是使用工作目录缓存；
2. 核验 SHA256；
3. 核验 Android signer / package / version；
4. 核验 Windows installer identity；
5. 真机/目标 Windows 安装启动；
6. 验证生产 API；
7. 验证产品对外定位没有超出实际数据覆盖、地图 Provider、AI Provider 与治理状态。

## 8. Truth Rule

```text
Existing GitHub Release != current branch release authorization.
Preview PASS != signed Release PASS.
Machine PASS != Human Visual Acceptance.
Engineering readiness != legal/platform/governance authorization.
```

永远以 GitHub Release 对象、当前 branch tip、同 HEAD CI artifact 和具名人类授权为事实源。
