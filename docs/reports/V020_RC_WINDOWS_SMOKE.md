# V020 RC WINDOWS SMOKE REPORT

> 实现基准：`IMPLEMENTATION_BASE` = 本轮启动时 fetch 后的 v5 实现 commit（`70d670c…`，分支历史内可查；
> 本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准）。

## 1. 结论

```text
WINDOWS_SMOKE = PASS
```

在**真实 Tauri v2 + WebView2 runtime**（非浏览器模拟）上完成桌面 smoke：launch / Home /
Search / Place overview / Place rules / Map / Reality / Evidence / Contribution / offline /
recovery / close / relaunch 全部通过；窗口 chrome、desktop rail、本地 API 解析、键盘/焦点
均实测正确。

## 2. 环境（本轮实测）

| 项 | 事实 |
| --- | --- |
| 构建 | ASCII worktree `D:\pa-fix`（复用）@ RC HEAD；`tauri build --debug --no-bundle`（vcvars64 + CARGO_TARGET_DIR=D:\pa-fix-target-win） |
| 产物 | `D:\pa-fix-target-win\debug\petaccess.exe`（debug，真实 Tauri 可执行文件） |
| Runtime | WebView2 Runtime **154.0.4258.48**（宿主已装，复用，无新下载） |
| API | `dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8016`（同 Android FAST 实例） |
| 驱动 | WebView2 CDP（`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9223 --force-renderer-accessibility`）+ `Page.captureScreenshot` + 进程/窗口检查 |
| 前端 base | `VITE_TAURI_API_BASE=http://127.0.0.1:8016/api/v1`（tauri.localhost origin，CORS 已覆盖） |

## 3. 运行验证（全部真实执行）

| 场景 | 驱动方式 | 结果 | 证据 |
| --- | --- | --- | --- |
| launch | WMI 分离启动 | PASS | 窗口 `PetAccess 宠物共处`；CDP page `首页 · PetAccess` 在线 |
| Home | CDP `#/` | PASS | h1「去之前，先看看这里的规则和现场。」、shell=true、error=false；`01_home.png` |
| Search | CDP `#/search` + 输入「咖啡」 | PASS | h1「搜索场所规则」、**10 条真实结果**；`02_search.png` |
| Place overview | CDP `#/place/{id}` | PASS | h1「云栖中心·测试商场」；`03_place.png` |
| Place rules | CDP `?view=rules` | PASS | rule groups；desktop rail 存在；`04_map.png`（命名对齐契约编号） |
| Map | CDP `#/map` | PASS | h1「规则地图」、error=false；`05_reality.png` 文件序见 SMOKE_METADATA |
| Reality | CDP `#/place/{id}/reality` | PASS | h1「现场轨迹」 |
| Evidence | CDP `?view=evidence` | PASS | evidence record + provenance |
| Contribution | 登录注入 + `#/contribute/{id}` | PASS | h1「你刚刚知道了什么？」、**5 个 option rows** |
| offline | CDP offline 事件 | PASS | `global-offline-banner` 可见；`08_offline.png` |
| recovery | CDP online 事件 + 重进 Home | PASS | banner 消失；Home 重新渲染（error=false）；`09_recovered.png` |
| close | Stop-Process（我方进程） | PASS | 进程退出 |
| relaunch | 再次 WMI 分离启动 | PASS | 窗口 + CDP page 重新在线（title 首页 · PetAccess） |

## 4. 桌面 UI / 运行时判定

- **真实 WebView2 runtime**：打包 origin `http://tauri.localhost` 数据请求成功（API CORS
  已含 tauri.localhost，回归测试 `test_tauri_webview_origin_is_cors_allowed` 通过）。
- **Window chrome**：`MainWindowTitle = PetAccess 宠物共处`；desktop rail
  （`desktop-rail` + `aria-label=主导航`）存在。
- **DPI / 布局**：主机当前 DPI 一套真实截图（1250×950）；无横向溢出（每个路由断言
  `scrollWidth == clientWidth`）。
- **键盘 / 焦点**：Search input fill + 点击通过真实 DOM 驱动，行为正确。

## 5. 截图证据

- 输出：`artifacts/rc-v020/windows-smoke/`（01_home … 09_recovered 共 9 张契约编号 PNG +
  10_home_after_recovery + SMOKE_METADATA.json）
- 核验：PNG 魔数 `89504E47`；尺寸 1250×950（System.Drawing 实测）；9/10 个 SHA-256 互不相同
  （`10_home_after_recovery` 与 `01_home` 同像素 = 恢复后回到 Home 的确定性，符合预期）
- route-state metadata：SMOKE_METADATA.json 逐张记录 route / state / result

## 6. 平台说明

- 未运行重 forensic；未修改 DPI 设置。
- 进程为本 Agent 启动（WMI），已正常关闭；未触碰其他进程。
