# F11 TOOLCHAIN DRIFT（本轮实测 vs v0.1.0 Release CI）

## 1. 本机实测（2026-09-26）

| 组件 | 本机 | v0.1.0 CI（release-ci.yml） | 漂移影响 |
|---|---|---|---|
| OS | Windows 11 Pro 10.0.26200 | windows-latest / ubuntu-latest | CI android 在 Ubuntu；本机 Windows host（NDK/clang 由 tauri 注入，b 构建实测可用） |
| Node | 22.15.0 | 22 | 一致 |
| pnpm | 12.4.1 | 12.4.1 | 一致 |
| Python | 3.13.14 | 3.12 | 无 runtime 影响（pytest/ruff 通过） |
| uv | 0.9.18 | setup-uv | 一致 |
| Rust | 1.97.1 | stable（CI 当时） | B/C 构建成功；rustup android targets 4 个齐 |
| JDK | 21.0.12.1 (Eclipse Adoptium) | temurin 17 | **漂移**：gradle 构建 OK（source/target 8 弃用警告），编译产物一致 |
| Gradle | 8.14.3（gen/android） | 依 CLI | 一致 |
| Tauri CLI | ^2.11.5（v0.1.0）/ ^2.11.5（HEAD） | 同 | 一致 |
| Android SDK | platforms 34/35/36 | platforms;android-35 | **漂移**：v0.1.0 CI 用 35；本机生成 compileSdk 36（平台 36 已装）。B/C 对照内自洽 |
| Build Tools | 34/35/36 | 35.0.0 | 本机 35.0.0 可用（同 CI） |
| NDK | 26.1 + 27.1.12297006 | 27.1.12297006 | 一致 |
| emulator | 37.1.11.0 | CI 无（只用模拟器验证） | — |
| adb | PATH 双版本 1.0.32/1.0.41（统一为 SDK 1.0.41 = platform-tools 37.0.1） | CI platform-tools 最新 | **REG-001 根因区**（本机多版本） |

## 2. 结论

- 唯一功能性工具链缺陷 = **本机 PATH 上 1.0.32 旧 adb 与多会话并发**（REG-001/005），非产品代码；已统一处置于 F10/F03。
- CI 与本机差异（JDK 17 vs 21、Ubuntu vs Windows、platform 35 vs 36、rust 版本）均不影响产物等价性（B/C 构建成功且签名一致；后端 945 passed）。

F11 = PASS（漂移已枚举；无影响判定）。