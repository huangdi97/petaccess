# F09 ANDROID WEBVIEW RUNTIME（本轮 logcat 分类采集）

## 1. 采集方式

矩阵 A/B/C 各次运行后执行 `adb logcat -d -t 300`，分类 grep：AndroidRuntime / chromium / WebView / cr_ / Console / Uncaught / ERROR / net:: / ERR_ / Tauri。

证据：`artifacts/forensics/F03/{A,B,C}/…logcat_runtime.txt`。

## 2. 分类结果（三对象一致）

| 类别 | 结果 |
|---|---|
| AndroidRuntime FATAL | 0（无 crash；出现的 AndroidRuntime 行均为 uiautomator/系统工具进程 START/EXIT） |
| chromium 启动/加载 | OK：`cr_LibraryLoader: Successfully loaded native library`、`cr_CachingUmaRecorder` 正常、`E2E_Used ViewportFitCover/SafeAreaInsetBottom`（渲染发生） |
| WebView/CSP | 无 `Refused`/CSP 违规行 |
| Console/Uncaught | 0（窗口内未见未捕获 JS） |
| net:: / ERR_ | 0（窗口内未见；数据面失败以 Empty-First 状态呈现，不产生未捕获错误——由 backend-down E2E 断言 0 uncaught 佐证） |
| cr_ 警告级 | 少量 WARNING（Bluetooth 权限缺失、SharedStorage 不可用等 chromium 常规提示，非故障） |

## 3. 说明与边界

- logcat 窗口为滚动 300 行，主要覆盖启动后段与 uiautomator；未捕获 JS 的完备断言以 Playwright console gate（backend-down spec）与 H5 gun 为准。
- 运行期间外部 adb churn（REG-001/005）会截断 transport 导致"窗口内 capture 偏少"或偶发 offline；矩阵脚本在每次捕获前重建 server（自愈），三对象因此仍完成。
- 补充证据：B/C 构建为 release（WebView debugging 关闭，console 不回流 logcat）；修复验证阶段的 debug 构建将带回 `PETACCESS_BOOT=*` 标记（F06）。

F09 = PASS（无 AndroidRuntime FATAL / 无未捕获 JS / 无 CSP 违规；chromium 正常渲染）。