# V020 RC ARTIFACT REPORT

> 实现基准：`IMPLEMENTATION_BASE` = 本轮启动时 fetch 后的 v5 实现 commit（`70d670c…`，分支历史内可查；
> 本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准）。完整结构化记录：`artifacts/rc-v020/RC_ARTIFACT_MANIFEST.json`。

## 1. 结论

```text
RELEASE_LIKE_H5 = PASS
RELEASE_LIKE_WINDOWS = PASS（签名受限：NotSigned，如实记录）
RELEASE_LIKE_ANDROID = PASS（签名受限：RELEASE_SIGNING = BLOCKED_SECRET）
RC_ARTIFACT_MANIFEST = PASS
```

本轮构建 release-like 产物并完成 artifact manifest；**不发布、不假签**。若发布需正式签名：

- Android：`~/.petaccess-keystore/petaccess-release.keystore` 缺失 → `BLOCKED_SECRET`（keystore 属 secrets，不 commit）。
- Windows：无 Authenticode 证书 → `NotSigned`。

## 2. 产物清单

| artifact | kind | path | size | sha256 | sign | smoke |
| --- | --- | --- | --- | --- | --- | --- |
| client-h5 production build | web | `apps/client-h5/dist` | 51 files / 426,186 B | index `E41DF9DF…` / js `8A94674D…` / css `5530106E…` | — | PASS（index 200、asset 200、hash routes 5/5、无 sourcemap、无 dev-port/dev-endpoint 泄漏） |
| Android debug APK | android | `…/apk/universal/debug/app-universal-debug.apk` | 137,488,646 B | `E6E79695…` | debug | PASS（FAST：install Success、launch、12 截图、runtime 断言全过） |
| Android release-like APK (unsigned) | android | `…/apk/universal/release/app-universal-release-unsigned.apk` | 11,586,738 B | `156285CD…` | BLOCKED_SECRET | PASS（aapt badging 核验 manifest/version/permissions；unsigned 不可安装为预期） |
| Android release-like AAB (unsigned) | android | `…/bundle/universalRelease/app-universal-release.aab` | 6,185,942 B | `9A52FC5B…` | BLOCKED_SECRET | PASS（exists / non-zero / hash） |
| petaccess.exe (debug, real Tauri) | windows | `D:\pa-fix-target-win\debug\petaccess.exe` | 8,732,160 B | — | — | PASS（Windows Smoke 全场景） |
| Windows NSIS installer (release-like) | windows | `D:\pa-fix-target-win-rel\release\bundle\nsis\PetAccess_0.1.0_x64-setup.exe` | 1,994,016 B | `5CC7C84E…` | NotSigned | PASS（makensis 产出；exists / non-zero / hash） |

构建命令（全部在复用 ASCII worktree `D:\pa-fix`，CARGO_TARGET_DIR 指向 D: 避免占用 E:）：

```text
H5:     pnpm --filter @petaccess/client-h5 build
Android: VITE_TAURI_ANDROID_API_BASE=http://10.0.2.2:8016/api/v1 \
         pnpm --filter @petaccess/client-h5 exec tauri android build --target x86_64 [--debug]
Windows: VITE_TAURI_API_BASE=http://127.0.0.1:8016/api/v1 \
         pnpm --filter @petaccess/client-h5 exec tauri build [--debug --no-bundle]
```

## 3. Android 清单核验（G10）

- `aapt2 dump badging`：package `com.petaccess.map` · versionName `0.1.0` · versionCode `1000` ·
  launchable-activity `MainActivity`。
- 权限：`android.permission.INTERNET` only（debug 构建额外注入标准
  `DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`，非产品权限；release 亦仅 INTERNET）——
  **无新增权限、无 permission drift**。

## 4. Windows 清单核验（G9）

- NSIS installer 由 `makensis` 产出，x64，productName PetAccess。
- 未执行静默安装/卸载矩阵（重 forensic，超出 FAST/RC 范围；真实 WebView2 运行验证见
  `docs/reports/V020_RC_WINDOWS_SMOKE.md`）。

## 5. 签名状态（诚实记录，不假签）

- Android：`RELEASE_SIGNING = BLOCKED_SECRET`（keystore 缺失；发布前需用户提供/生成并安全注入）。
- Windows：`NotSigned`（无 Authenticode 证书；如发布需购买/配置签名）。

## 6. Manifest

- `artifacts/rc-v020/RC_ARTIFACT_MANIFEST.json`：逐 artifact kind/path/size/sha256/build command/signing/smoke。