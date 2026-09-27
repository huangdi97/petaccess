# UI Reconstruction — Visual Audit

> 依据：`UI_RECONSTRUCTION_DESIGN_FREEZE.md`（v0.10-R1 Canonical Master + Approved Reference 冻结）
> 证据集：`artifacts/ui-reconstruction/final/{ui-360,ui-430,ui-800,ui-1280,ui-1440}/*.png`（90 张）
> 对比基准：`artifacts/ui-reconstruction/baseline/`（85 张，M2 旧 UI）
> 画廊：`UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html`（90 格 before→after，可直接打开）

## 审计方法（真实执行项）

| 维度 | 方法 | 证据 |
|---|---|---|
| 结构断言 | Playwright 门禁（phase1/phase2/phase3/a11y gate） | `tests/ui-reconstruction/phase1-gate.spec.ts`、`phase3-gate.spec.ts`、`a11y-gate.spec.ts` 全 PASS |
| 横向溢出 | `document.scrollWidth <= clientWidth` 全页面 × 9 viewport | `tests/e2e/responsive.spec.ts` 72/72 PASS（含 place/reality/evidence） |
| 截图真实性 | PNG 魔数 `89504E47`、尺寸、非纯色采样 | 全 90 张存在；抽样 10 张 distinct colors 4–9（空转页会只有 1–2 色） |
| 桌面/移动转换 | 同一页面在 ui-1440 与 ui-430 的截图对 | 见下方逐页条目 |

## 逐页审计（final stage，桌面 1440 / 移动 430）

### Home — Task Launcher（AC-P4）
- 结构：QueryContextBar → 覆盖范围行 → 主搜索 → 查询视角（3 内联键）→ 最近查看 → 附近已核验/规则待核实 divider 行 → 次级镜头入口 → 语义注脚。
- 无 Hero 照片、无彩色 feature card、无 category chips：模板核验（HomeView.vue 无 hero/img、无 `.panel`）；phase gates 断言 `.home-card` 为 divider 行。
- 移动 430：单列，搜索按钮 44px 触控目标（a11y gate PASS）。
- 状态：loading（骨架）、empty（home-empty 引导到地图/贡献）、error（ERROR 状态块 + 重试）、offline（全局离线横幅）全部有截图。

### Search — List–Detail Workspace（AC-P1）
- 桌面：Rail + 360–420px 结果窗格 + 右侧 Detail Inspector 同时可见（phase1-gate 断言两栏并存、无每结果卡片、无右侧占位空白卡片）。
- 移动：结果列表 → 点击 → Place 全页（无挤压两栏；phase1-gate 断言）。
- 状态：loading / empty（“没有找到已收录场所”）/ error / offline 均有截图。

### Map — Spatial Workspace（AC-P5）
- 桌面：400px 结果窗格 + 全幅地图画布（flex:1, min-height 480px）+ 选中场所单一浮动 PlacePreview（radius 10–12px + elevation）。
- 移动：全屏地图 + 底部 sheet；地图/列表切换。
- marker 为 shape+语义状态（StatusBadge 图标+文字+颜色），非友好绿/红（StatusBadge.vue 核验 + a11y gate 断言 label/icon 非空）。
- 错误态：桌面在结果窗格、移动在地图画布内（本重构新增的移动错误面）；均有截图。

### Place — Dossier + Decision Inspector（AC-P2）
- 桌面：主档案（身份/总览/区域/规则/现场/设施/证据）+ 粘性 Inspector（当前查询/主状态/条件/重大例外/来源与新鲜度）。
- 空间与区域为 divider 行（公共区域/餐饮堂食区/户外区域），无三卡片。
- 无大照片 Hero：PlaceView 无 hero img（核验）。
- Unknown（无效 place id）、Conflict 语义由 StatusBadge 词汇覆盖（consumer-contract-closure C5 测试断言 lens 投影不改变 Domain 事实）。

### Reality — Temporal Event Log（AC-P7）
- `.trace-row` divider 时间线，事件无 `.panel` 卡片面（phase3-gate 断言 `trace-observations` 内 `.panel` 计数 0）。
- 筛选为轻量 select/popover（模板核验无 pill wall）。

### Evidence — Evidence Record + Provenance（AC-P8）
- 5 步 Provenance 链（photo→place→observed→source→review）+ 时间记录 + 证据条目 + 来源列表；永久文案“现场事实不代表正式准入规则。”（phase3-gate 断言）。
- 无装饰性建筑旅游照：观察 API 无媒体 URL，页面渲染“暂无原始证据图片”说明（真实性优先）。

### Contribution — Transaction Flow（AC-P9）
- 首问“你刚刚知道了什么？”，五个消费者语言选项；提交结果“已提交待核验”（ContributeView 模板核验），页面无内部 Domain 名词泄漏。
- 无场所时显示占位门禁（contribute-needs-place），弱化全局导航。

## 视觉密度与对齐核验
- divider 行半径 0（tokens `--pa-radius-*` + 页面样式核验），默认无阴影；唯一浮动面 = 地图预览（`--pa-elevation-3`）。
- 卡片数量：各页面无 `.panel` 列表墙（gates 断言计数）。
- 徽章数量：StatusBadge 仅出现在结论行/预览/详情头（a11y 抽样断言 6 个以内均有文字）。

## 需要人工目视复核的项（诚实标注）
以下依赖人类目视，自动化只能提供代理证据（截图存在、尺寸正确、非纯色、无溢出、结构断言通过）：
- 字距/对齐微差、间距观感、深浅对比舒适度；
- 移动转换的整体美感（截图对已生成，可打开 `UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html` 目视）；
- 动画流畅性（本环境仅验证 prefers-reduced-motion 存在）。

## 结论
自动化审计全部通过；`UI_VISUAL_CLOSURE` 是否置为 PASS 见 `PROJECT_STATE.md`（只有真实完成视觉复核后置 PASS）。
