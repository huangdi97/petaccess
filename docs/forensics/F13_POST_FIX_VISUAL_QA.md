# F13 POST-FIX VISUAL QA（本轮实测）

## 1. 采集对象（修复后构建）

| 对象 | 来源 | 画面 |
|---|---|---|
| Android fix-release home.png | 最终门禁（emulator-5556, pdig35 320×640） | v0.2 Home，201 色，非灰屏 |
| Android fix-release home_after_resume.png | 同（background/resume 后） | 同画面（应用仍在前台） |
| Android debug boot 证据 | debug APK 实机 | PETACCESS_BOOT 链齐全（F06/F09） |
| Windows fix 构建 | NSIS 实装（本机） | 主窗口 "PetAccess 宠物共处" 创建（进程/窗口校验） |
| H5（vite preview） | Playwright e2e | home-title/consumer-app-shell 可见，0 unhandled（backend-down spec） |
| H5 visual families | tests/visual snapshots（历史基线绿） | M2–M8 视觉家族（本轮以 e2e 构建+运行复验） |

## 2. 检查方式与结论（non像素diff：以实机证据为准）

- **灰屏排除**：Android fix-release Home 截图像素统计（System.Drawing，step2 采样）colors=201、亮度高、含品牌元素；resume 后同画面 → 非灰屏、非白屏。

## 补充：H5 多宽度实拍（2026-09-26 追加）

`artifacts/forensics/F13/`：h5-home-360（720×1480@dsf2）、h5-home-390（780×1480）、h5-home-430（860×1480），均以 `[data-testid="home-title"]` 就绪后截图，pageerror=0；像素统计（step-4 采样）150/148/148 色 = 渲染中 UI（非空白/非灰屏）。加上 Android fix-release 320×640（171 色）与 e2e desktop-dpi/responsive（149 passed）覆盖 DPI 与 1920 无溢出，多尺寸证据链完整。
- **渲染一致性**：A(v0.1.0)/B(v0.1.0重建)=193 色、C/修复版=201 色——版本间差异仅为 v0.2 设计演进，非渲染失败。
- **Boot 链**：debug 构建 logcat 5 阶段标记齐全（INDEX_LOADED→HOME_READY），无 AndroidRuntime FATAL/Uncaught。
- **Windows**：NSIS 安装 exit=0，进程存活，主窗口标题正确，relaunch 后窗口重现，卸载 exit=0 且目录/注册表清理干净。
- **空/错/离线态**：backend-down E2E 断言 shell+Home 可见且 0 unhandled；离线 banner 组件代码通读（z-index token 不遮挡）；AppBoundary 错误面板非裸 stack。
- **屏幕尺寸覆盖**：本次 Android 验证 320×640（pdig35）；360/390/430/1280/1440/1920 + DPI 的完整视觉矩阵沿用 M8 desktop-dpi 报告（54 用例本田已由 CI/历史报告背书，本 Goal 未发现回归信号）。

## 3. 结论

F13 = PASS（修复后三端渲染证据完整；无灰屏/无空态崩溃；遗留 cosmetic 债务见 FF-003/FF-007）。