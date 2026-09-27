# V020 M3 WINDOWS SMOKE REPORT

> M3 深化收口后的 Windows（Tauri 桌面）快速冒烟（契约 §24/§91）。
> 本轮为真实 packaged runtime 验证（NSIS 安装 → petaccess.exe → WebView2 渲染），非浏览器预览。

## 环境（本轮实测）

- 构建：`D:\pa-m3` ASCII worktree（git worktree @ M3 HEAD 173bdcb）→ `tauri build --debug`，含 M3 前端与 Consumer 层；`VITE_TAURI_API_BASE=http://127.0.0.1:8010/api/v1`（独立 PetAccess API 实例）。
- 产物：`D:\pa-m3-target\debug\bundle\nsis\PetAccess_0.1.0_x64-setup.exe`（2.6 MB installer）→ 静默安装到 `%LOCALAPPDATA%\PetAccess\petaccess.exe`（13.2 MB）。
- 后端：`dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8010`。
- 验证手段：真实窗口 + WebView2 渲染截图（PNG 校验头）+ 窗口标题 + **WebView2 accessibility 树（DOM 级）**（UI Automation），弥补截图无法逐字判断的局限。

## 执行结果

| 项 | 结果 | 证据 |
|---|---|---|
| Install | PASS | `setup.exe /S` → exit 0；`%LOCALAPPDATA%\PetAccess\petaccess.exe` 存在 |
| Launch | PASS | 主进程存活，`MainWindowTitle = PetAccess 宠物共处`（多个进程实例均确认） |
| WebView2 渲染 | PASS | accessibility 树：`首页 · PetAccess - Web 内容` 子树完整（rail/主要内容/语义文案） |
| Home | PASS | 截图 `windows/home-m3-final.png`（293,196 B，PNG 头 89504E47）；accessibility 树含「去之前，先看看这里的规则和现场。」+ 查询视角 + 类别 + 「拍规则牌/现场核验」 |
| Search | PASS | 点击 rail「搜索」→ 树含「搜索场所」、筛选 chips（明确允许/明确限制/来源不一致/信息不足）、结果行（青岚公园·演示、松风社区·演示，含生效规则数与 Reality 摘要「现场记录不足或未完成人工核验」）、桌面 split preview（PlacePreview 空态→数据） |
| 桌面 split preview | PASS | 树含 PlacePreview：规则 / 近期现场 / 差异 / 「查看完整场所」/ 依据行（规则依据 1 条 · 现场依据 0 条） |
| Navigation | PASS | rail 首页/搜索/地图/贡献/我的/设置/关于（Hyperlink）齐全；点击搜索成功切换 |
| Offline / Error | PASS | API 未启动时 Home 显示统一错误（「未能取得附近场所」+ 重试）；Accessibility 树含错误态，无原始堆栈 |
| Recovery | PASS | 启动 API 后点击「重试」→ 数据完整恢复（结果行/Reality 摘要出现） |
| 语义不变量（树上确认） | PASS | 「尚未核验」+「规则待核实 ≠ 允许或禁止」文案在树中；「现场记录不足或未完成人工核验」= Reality 空态，非「没有动物」 |

## 截图

- `artifacts/ui-audit/windows/home-m3-final.png`（293 KB，Home + 数据）
- `artifacts/ui-audit/windows/search-m3-final.png`（287 KB，Search + split preview）

## 已知说明

- 首次登录态：Windows 冒烟为匿名访问（未配置 token），与 Android/Web 同策略。
- debug build：与上一轮 acceptance 的 debug 冒烟一致；release 包已在历史基线验证过安装链，本轮为 M3 前端改动后的 runtime 复验。

## 结论

`WINDOWS_RUNTIME = PASS`（本轮实测：install / launch / Home / Search / split preview / navigation / offline-error / recovery 全通过，截图与 accessibility 树证据归档）。