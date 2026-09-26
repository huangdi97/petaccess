# V020 Android 视觉验收报告（模拟器）

> 目标 §122 · 设备：`emulator-5562`（API 35，1080×2340 @440dpi → 393×851dp 逻辑视口，PHONE-M 档）

## 方法论

- 截图统一命名：`<device>__<route>__<state>__<scenario>.png`（§111）。
- 每张截图做 PNG 魔数（`89504E47`）与灰度/空白检测（区分扫描线直方图）；关键页面以 CDP 读取真实 DOM 文本交叉验证渲染内容，而非仅“看起来正常”（§83）。
- 运行时控制台错误单独采集并归类（Tauri/Console），问题按 VIS-xxx 编号。

## 页面验收结果（PHONE-M 档）

| 页面 | 状态 | 证据 |
|---|---|---|
| Home 空态 / 富态 | PASS（富态渲染真实场所列表；“尚未核验 ≠ 允许/禁止”文案在位） | `phoneM__home__rich__*.png` + CDP text |
| Search（入口 / 结果） | PASS（搜索框、筛选器、结果壳渲染；结果加载由 CDP 深链触发） | `phoneM__search__*.png` |
| Map 壳 | PASS（定位提示、筛选、列表/地图模式入口渲染，无灰屏） | `phoneM__map__shell__*.png` |
| Contribute 入口 | PASS（“现场贡献”入口 + 绑定场所提示） | `phoneM__contribute__entry__*.png` |
| Mine / Settings / Privacy / About | PASS（登录提示、设置说明、隐私清单、关于文案全部渲染） | `phoneM__mine__*.png` 等 |
| Place 详情 | PASS（`星河咖啡·测试店`：生效规则 3 条、当前答案、近期现场、工作人员处理计数、设施摘要） | `phoneM__place__detail__*.png` + `cdp_semantic.json` |
| Reality Trace | PASS（“现场轨迹（≠规则）”、事实/核验分离、“暂无记录不代表现场没有动物”） | CDP text |

## 发现并修复的视觉问题

| ID | 描述 | 修复 | 复测 |
|---|---|---|---|
| VIS-001 | `PaIcon` 把 CSS 变量绑定到 SVG `width/height` 属性，浏览器报 “attribute width/height: Expected length”（每个图标渲染都触发） | `apps/client-h5/src/components/ui/PaIcon.vue`：改用 inline `style`（CSS 变量在 style 中合法） | 模拟器实测 SVG 控制台错误 **0**；新增 Playwright 回归 2 条（151/151 通过） |

## 逐页 PASS/PASS_WITH_DEBT/FAIL

- PASS：Home / Search / Map / Contribute / Mine / Settings / Privacy / About / Place / RealityTrace（PHONE-M 档）。
- PASS_WITH_DEBT：无。
- FAIL：无。

## 备注（诚实记录）

- 本报告仅覆盖 PHONE-M 逻辑宽度（393dp）。PHONE-S/L/Tablet 档位的视觉验收未在本次执行 → Device Sizes = PARTIAL。
- 截图集：`artifacts/android_acceptance/screenshots/`（71 张，全部通过 PNG 魔数与非灰校验）。
