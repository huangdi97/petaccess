# F06 BOOT SEQUENCE（本轮实证 + 标记化）

## 1. 启动链（Android MainActivity → Home Ready）

```
Android OS（模拟器 API35）
  ↓
MainActivity（com.petaccess.map.MainActivity，Tauri 模板）
  ↓（Tauri runtime 初始化 plugins; mobile_entry_point；webview 创建）
WebView（全屏 android.webkit.WebView，ui.xml 实测 bounds [0,0][320,640]）
  ↓（加载 asset:// tauri localhost index.html）
dist/index.html (script type=module → /src/main.ts)
  ↓
main.ts：INDEX_LOADED → configureApi(resolveApiEndpoint(runtime)) → VUE_CREATED
  ↓
Vue createApp(App).use(router).mount("#app")；router.isReady → ROUTER_READY
  ↓
App.vue → ConsumerAppShell（onMounted → APP_SHELL_MOUNTED；含 GlobalOfflineBanner/AppBoundary）
  ↓
RouterView → HomeView（onMounted { session.restore → load() → HOME_READY }）
```

## 2. 每层契约

| 层 | input | output | ready signal | failure signal | timeout | fallback |
|---|---|---|---|---|---|---|
| MainActivity | Intent | Activity resumed | dumpsys activity topResumedActivity | process 死亡 / crash | — | — |
| Tauri runtime | manifest | webview window | logcat chromium 启动 | AndroidRuntime FATAL | — | — |
| WebView | asset index.html | DOM | ui.xml WebView 节点 | 无节点 | — | — |
| JS bundle | dist asset | Vue mount | PETACCESS_BOOT=VUE_CREATED | pageerror | — | AppBoundary |
| Router | hash history | 首路由 '/' | PETACCESS_BOOT=ROUTER_READY | isReady reject → ROUTER_FAILED | — | bootFailed 态 |
| AppShell | — | shell chrome | PETACCESS_BOOT=APP_SHELL_MOUNTED | onErrorCaptured → 错误面板 | — | reload/retryBoot |
| Home | session+data | 首屏渲染 | PETACCESS_BOOT=HOME_READY | load() catch → 错误/离线态（非灰屏） | loading must settle | offline banner |

## 3. 可观测性（本次新增，debug-only）

- `apps/client-h5/src/config/bootTrace.ts`：`VITE_BOOT_TRACE=1` 时输出 `console.info("PETACCESS_BOOT=<stage>")`；生产不带该 env 时零输出（常量折叠，无泄漏）。
- 阶段：INDEX_LOADED、VUE_CREATED、ROUTER_READY、APP_SHELL_MOUNTED、HOME_READY（+ROUTER_FAILED 失败信号）。
- Android debug 构建（WebView debugging 开启）→ 阶段标记进入 logcat（chromium CONSOLE 行）；Windows debug 构建 → WebView2 devtools/console。
- 矩阵 A/B/C 的 ready 判定未依赖标记（无标记版本），采用 Activity/WebView/渲染统计三证据（见 F03）。

## 4. 实证结果（矩阵运行）

A/B/C 三对象均到达 Home 渲染；logcat 窗口无 AndroidRuntime FATAL / 无未捕获 JS（见 F09）；C 为 v0.2 界面（201 色，非灰屏）。

F06 = PASS（链路贯通 + 可观测性闭环）。