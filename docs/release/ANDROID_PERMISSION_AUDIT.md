# ANDROID_PERMISSION_AUDIT.md — v0.1.0

> 生成日期: 2026-09-24 (Phase U, 实测 `src-tauri/gen/android/app/src/main/AndroidManifest.xml`)
> 原则: 只申请真正需要的权限; v0.1.0 不请求定位; 现场贡献需要时再 just-in-time。

## 1. 最终 Manifest 权限(实测)

| 权限 | 是否声明 | 用途 | 判定 |
|---|---|---|---|
| `android.permission.INTERNET` | 是 | WebView 加载 H5 与 API 请求 | 必需 — KEEP |
| `android.permission.ACCESS_FINE_LOCATION` | 否 | 附近场所查询用 mock 相机坐标 | 不声明 — 正确 |
| `android.permission.ACCESS_COARSE_LOCATION` | 否 | 同上 | 不声明 — 正确 |
| `android.permission.CAMERA` | 否 | 现场照片走系统相册 picker | 不声明 — 正确 |
| `android.permission.READ_EXTERNAL_STORAGE` | 否 | Android 13+ 由 photo picker 代理 | 不声明 — 正确 |
| `android.permission.WRITE_EXTERNAL_STORAGE` | 否 | 不写外部存储 | 不声明 — 正确 |
| 其他 runtime 权限 | 否 | 无 | — |

## 2. 结论

- **运行时权限请求数 = 0**。v0.1.0 无任何需要用户授权的 runtime permission。
- 后端 `GET /places/nearby` 使用服务端合成相机坐标(演示), 不依赖设备定位。
- 未来"现场贡献"若需要真实定位: 在触发动作时 just-in-time 请求
  `ACCESS_FINE_LOCATION`(单次), 不得在启动时请求。
- 相机: 若需要拍照, 使用系统 photo picker(ACTION_PICK_IMAGES), 不直接调 CAMERA。

## 3. 验证命令

```powershell
# 从 APK 提取并核对权限
& "$env:USERPROFILE\Android\Sdk\build-tools\35.0.0\aapt2.exe" dump permissions PetAccess_0.1.0-android-universal.apk
# 期望仅输出: package: com.petaccess.map
#   uses-permission: name='android.permission.INTERNET'
```
