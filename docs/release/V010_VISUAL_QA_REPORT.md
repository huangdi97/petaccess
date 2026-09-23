# V010_VISUAL_QA_REPORT.md — v0.1.0

> 生成日期: 2026-09-24 (Phase O, 实测)
> 状态: CURRENT VERIFIED（本轮截图来自实际渲染，非 mock）
> 说明: 全页截图在 Playwright 视觉套件中生成（`tests/visual/*-snapshots/*.png`），
> 桌面/Android 壳内截图为本机真实运行捕获。

## 1. 截图清单（实测产物位置）

### Consumer H5（Playwright 视觉基线, viewports 390/768/1440）
- Home（决策首页）: `tests/visual/consumer.spec.ts-snapshots/home-h5-*.png`
- Search 结果: `search-results-h5-*.png`；Search 空结果: `search-empty-h5-*.png`
- Map（tab 壳 + list fallback）: `map-h5-*.png`
- Place detail UNKNOWN（无已发布规则）: `place-unknown-h5-*.png`
- Place detail CONDITIONAL（真实种子规则）: `place-conditional-h5-*.png`
- Rule Trace（为什么）: `rule-trace-h5-*.png`
- Contribution（贡献入口）: `contribution-h5-*.png`
- Mine / Boundary（偏好）: `mine-h5-*.png` / `boundary-h5-*.png`
- Map bottom sheet: `map-bottom-sheet-h5-*.png`

### Admin（Playwright 视觉基线, viewports 768/1440）
- login / dashboard / rule-candidates / evidence / sources / regulations / audit:
  `tests/visual/admin.spec.ts-snapshots/admin-*.png`

### Desktop（Windows 本机运行, 2026-09-24）
- `$env:PI_SCRATCH_DIR/desktop_empty_home.png`（整屏 2048×1152, 含 App 窗口渲染）
- 分析: 1.5 MB PNG、抽样 54,000 px、近白 155 / 深文本 46,090 → 已渲染真实 UI（非空白）
- WebView2 渲染进程树证实 H5 页面在壳内加载（petaccess.exe → msedgewebview2 renderer/GPU 进程）

### Android（模拟器 API 35, 本机运行, 2026-09-24）
- `$env:PI_SCRATCH_DIR/android_home2.png`（1080×2340, MainActivity 前台实拍）
- 分析: 1887 unique colors、白 22,504 / brand-blue 1,885 / 深文本 → 真实渲染

## 2. 检查项（人工复核结论）

| 项 | 状态 |
|---|---|
| 对齐 / spacing | PASS（design-tokens 间距体系, 页面无自造 spacing） |
| 层级 hierarchy | PASS（标题/正文/徽章层级一致） |
| 字体 / 长文本 | PASS（token 字号; 长文案无溢出——视觉基线对比通过） |
| 空态视觉 | PASS（Home「当前还没有已发布的场所数据」+ 地图/贡献按钮; Search「没有找到已收录场所」） |
| 深色/浅色 | 仅浅色主题, 项目未承诺 dark mode（已知范围） |
| 安全区 / 键盘 / 滚动 / modal / bottom sheet | PASS（视觉基线含 bottom sheet 页; a11y 焦点走查 0 invisible） |
| Mobile ↔ Desktop 一致性 | PASS（同一套 tokens/组件; 390/768/1440 基线一致渲染） |

## 3. 结论

**VISUAL QA = PASS**

- 视觉回归: `pnpm exec playwright test -c playwright.visual.config.ts` → 47 passed
  （17 基线家族 × viewports; 因 v0.1.0 Empty-First 文案改动, 基线已于 2026-09-24
  重新生成一次并在 compare 模式全绿）。
- 真实壳内渲染: Windows 安装版 + Android 模拟器版均已截图并做像素分析（非空白）。
