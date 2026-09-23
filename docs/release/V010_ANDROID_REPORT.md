# V010 ANDROID REPORT — 2026-09-24

> 状态标记 (Status Legend): **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 项 | 结果 | 标记 |
|---|---|---|
| Build（SDK 35 / NDK 27.1.12297006 / API 35 emulator） | PASS | CURRENT VERIFIED |
| 4 ABIs | aarch64 / armv7 / i686 / x86_64 | CURRENT VERIFIED |
| 签名（release keystore） | apksigner v2+v3 校验通过 | CURRENT VERIFIED |
| aapt2 元数据 | applicationId/versionName/versionCode/minSdk/targetSdk | CURRENT VERIFIED |
| 权限审计 | 仅 INTERNET，0 runtime permissions | CURRENT VERIFIED |
| 模拟器 smoke | install/launch/screenshot/force-stop/relaunch/uninstall PASS | CURRENT VERIFIED |

## 1. 构建环境与真实环境发现

- SDK 35、NDK 27.1.12297006、API 35 x86_64 模拟器（WHPX）。
- **真实环境发现**：AGP 拒绝 CJK 路径（repo 名 `宠物管理`）；构建改在 ASCII 路径 git worktree `C:\petaccess-worktree` 完成（tauri android init/build）。
- 4 ABIs 全部构建：aarch64 / armv7 / i686 / x86_64。

## 2. Artifact 与元数据

- unsigned 34.7 MB -> 签名后 `PetAccess_0.1.0-android-universal.apk` 34.8 MB。
- SHA256：`d9e3acf4cb1241c7c068942f98d6bbd59511b9fd3697e5097ea8aa1ec0e592bb`（Get-FileHash 复核）。
- aapt2 badging：applicationId `com.petaccess.map`，versionName `0.1.0`，versionCode `1000`，minSdk `24`，targetSdk `36`。

## 3. 签名

- release keystore：`~/.petaccess-keystore/petaccess-release.keystore`（不在 Git 内）；apksigner v2+v3 校验通过。
- 签名流程文档：`docs/release/ANDROID_SIGNING.md`。

## 4. 权限

- 仅 `android.permission.INTERNET`（aapt2 dump permissions 核验）；manifest runtime permissions 请求 0。

## 5. 模拟器 smoke（Android 15, Pixel 5）

- install Success -> launch MainActivity resumed、pid alive -> screenshot 1080x2340 真实渲染（品牌蓝 + 白 + 文本，1887 unique colors）-> force-stop -> relaunch pid alive -> uninstall Success、package removed。

## 6. 结论

**结论: ANDROID_BUILD = PASS; ANDROID_INSTALL = PASS**
