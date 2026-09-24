# V010 GITHUB RELEASE REPORT — 2026-09-24（发布后终版）

> 状态标记: **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 项 | 结果 | 标记 |
|---|---|---|
| git remote | `origin` → https://github.com/huangdi97/petaccess.git | CURRENT VERIFIED |
| tag v0.1.0 | 已创建并推送（指向 c84b4cf） | CURRENT VERIFIED |
| pr-ci workflow | 已提交 + **实际运行全绿**（engineering-gate / backend / frontend / e2e 4/4） | CURRENT VERIFIED |
| release-ci workflow | 已提交 + **实际运行全绿**（verify / frontend / backend / windows / android / checksums 6/6） | CURRENT VERIFIED |
| GitHub Release | **v0.1.0 — Early Preview 已发布** https://github.com/huangdi97/petaccess/releases/tag/v0.1.0 | CURRENT VERIFIED |
| V0_1_0_RELEASED | **YES（2026-09-24）** | CURRENT VERIFIED |

## 1. 发布执行记录（Phase AG + AH, 全部实际发生）

- **授权**：RELEASE_V0_1_0_AUTHORIZATION 由 huangdi97 于 2026-09-24 明确授权。
- **remote**：创建 public 仓库 `huangdi97/petaccess`（master 默认分支），`git push -u origin master`。
- **Android 签名 Secrets**：`ANDROID_KEYSTORE_BASE64 / _PASSWORD / KEY_ALIAS / KEY_PASSWORD` 已通过 `gh secret set` 写入仓库（keystore 本体仍在 Git 之外的 `~/.petaccess-keystore/`）。
- **tag**：`v0.1.0` 创建并推送；Release CI 触发并全绿（6/6 job，含 Windows NSIS 3m49s 与 Android signed APK 6m39s）。
- **Release**：`gh release create v0.1.0` 上传 3 个资产（exe / apk / SHA256SUMS.txt），title "v0.1.0 — Early Preview"，含完整 Early Preview 说明与 SmartScreen/空数据已知限制。
- **Phase AH 重下载验证（真实发生）**：
  - 从 Release 页经代理重新下载 exe 与 apk，SHA256 与 SHA256SUMS.txt 逐一一致（exe `adb8e984…`、apk `e236f193…`）。
  - Windows：install→launch（alive）→relaunch（alive）→uninstall 全 PASS。
  - Android（API 35 模拟器）：install Success→launch（MainActivity resumed, pid 存活, 1080×2340 真实渲染 1919 色）→relaunch（pid 存活）→uninstall Success。

## 2. Artifacts SHA256（Release 页 SHA256SUMS.txt，已复核）

```text
adb8e9843aa8eac6710fec992588a6f6dbe93b733573a2c9171518d341990225 *PetAccess_0.1.0_x64-setup.exe
e236f1936360a7f950152df53860ed01076c0c595b35fa881d4543c9f427f82d *PetAccess_0.1.0-android-universal.apk
```

> 注：与本地构建版（d9e3acf4… / a0a2f61b…）不同属预期——Release 资产必须来自 tagged commit 的 CI 构建；本次即为该 tag 的 CI 产物，且已通过 SHA256 重下载校验。

## 3. 结论

**结论: GITHUB_RELEASE = PASS（V0_1_0_RELEASED = YES, 2026-09-24）** — Release 已发布并完成从 Release 页重下载 + SHA256 + 签名 + 安装全链路验证。
