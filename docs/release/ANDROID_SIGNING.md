# ANDROID_SIGNING.md — v0.1.0 Release Signing Strategy

> 生成日期: 2026-09-24 (v0.1.0 Phase V, 实测)
> 目的: 正式 release 签名策略 + 本地实践记录。禁止发布 debug-signed APK。

## 1. 策略

| 项 | 值 |
|---|---|
| 签名工具 | `apksigner` (Android SDK build-tools 35.0.0) |
| Key | RSA 2048, alias `petaccess`, validity 10000 天 |
| Keystore | `~/.petaccess-keystore/petaccess-release.keystore` — **不进 Git** |
| 密码 | `~/.petaccess-keystore/keystore-password.txt` — **本地仅存, 不进 Git** |
| Git | 已确认: `git status` 无 keystore/密码引用; `.gitignore` 不含该目录 |
| CI 策略 | GitHub Actions Secrets (`ANDROID_KEYSTORE_BASE64` / `ANDROID_KEYSTORE_PASSWORD` / `ANDROID_KEY_ALIAS` / `ANDROID_KEY_PASSWORD`), 由 Release CI 在构建时注入 |

## 2. 本地签名步骤(实测)

```powershell
$sdk = "$env:USERPROFILE\Android\Sdk"
$ks  = "$env:USERPROFILE\.petaccess-keystore\petaccess-release.keystore"
$pw  = (Get-Content "$env:USERPROFILE\.petaccess-keystore\keystore-password.txt" -Raw).Trim()

# 1) 构建 unsigned APK (ASCII 路径 worktree, 因仓库路径含 CJK 触发 AGP 拒绝)
#    C:\petaccess-worktree\apps\client-h5\src-tauri\gen\android\app\build\outputs\apk\universal\release\app-universal-release-unsigned.apk

# 2) 签名
& "$sdk\build-tools\35.0.0\apksigner.bat" sign `
  --ks $ks --ks-key-alias petaccess `
  --ks-pass pass:$pw --key-pass pass:$pw `
  --out PetAccess_0.1.0-android-universal.apk app-universal-release-unsigned.apk

# 3) 验证
& "$sdk\build-tools\35.0.0\apksigner.bat" verify --verbose PetAccess_0.1.0-android-universal.apk
# 实测: Verified using v2 scheme: true; v3 scheme: true; Number of signers: 1
```

## 3. 版本元数据(实测)

| 项 | 值 |
|---|---|
| applicationId | `com.petaccess.map` (固定) |
| versionName | `0.1.0` |
| versionCode | `1000` (gen/android/app/tauri.properties: `tauri.android.versionCode=1000`) |
| minSdk | 24 (Tauri 官方最低; 本项目无需更高 — 无原生定位/相机强依赖) |
| targetSdk | 36 |
| 权限 | 仅 `android.permission.INTERNET` (见 ANDROID_PERMISSION_AUDIT.md) |

## 4. 平台要求

- Android 7.0 (API 24) 及以上。
- v0.1.0 为 Early Preview, 未上架 Google Play; APK 直接安装需允许"未知来源"。
- GitHub 发布物为 signed APK; 若未来上架 Play 需额外 `.aab`(Release CI 可加)。

## 5. 轮换 / 恢复

- Keystore 丢失 = 无法更新已发布 APK(签名失效)。keystore 与密码须离线备份
  至受控位置(本仓库不存)。CI Secrets 与本地文件必须一致。
