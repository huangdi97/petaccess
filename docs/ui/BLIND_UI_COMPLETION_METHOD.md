# Blind-Model UI 全量收口 — Completion Method（方法文档）

> 阶段：v0.2.2 Blind-Model UI 全量收口 · 分支 `feat/visual-fidelity-recovery`
> 原则：**不使用任何视觉模型 / 图像理解 / OCR 截图理解**。Agent 只读 DOM / a11y tree / computed styles / bbox / text / layout metrics / 文件存在性与 hash / machine contract；Screenshot 仅是证据产物。

## 1. 为什么需要“盲模型”方法

视觉验收的经典做法是“截图看起来对不对”，但这对 Agent 是**不可验证**的：没有眼睛。本轮的解法是把视觉设计“编译”成机器可读约束，用确定性测量代替审美判断：

1. **契约层**（`docs/ui/contracts/`）：12 份 Markdown + 10 份 JSON 机器契约，把每条设计约束写成 `elements / structure / density / language` 规则（目标值、允许范围、WARN 阈值、FAIL 阈值）。
2. **测量层**（`tools/ui-oracle/`）：Playwright probe 在固定 viewport / 确定性数据 / 冻结动画下测量 `getBoundingClientRect()` 与 `getComputedStyle()` 输出；compare.ts 将 actual 与 contract 逐条比对，产出 PASS/WARN/FAIL。
3. **语义层**（`data-ui` + consumer mapping layer）：关键区域挂稳定 `data-ui` 属性；raw enum 只在 `consumer/labels.ts` 等映射层转成中文，页面禁止自行拼 raw enum。
4. **证据层**：每张截图只做文件存在 / PNG magic / dimensions / non-zero bytes / hash distinct 校验。

## 2. 执行顺序

| 阶段 | 内容 | 产物 |
|---|---|---|
| Phase 0 | 契约 + Oracle 基建 + 基线自证（改 UI 前） | `reports/phase-0-baseline.json`（117 PASS / 11 WARN / 30 FAIL，覆盖 8 类已知问题） |
| Phase A | Search 双栏 / 行密度 / detail 内容宽度 / quiet 控件 | search.desktop 22/22、search.mobile 15/15 |
| Phase B | Place dossier + sticky inspector / zone 消费者文案 / progressive disclosure | place.desktop 15/15、place.mobile 11 PASS + 1 WARN（首屏 42 行，契约 warnAt=30） |
| Phase C | Home 去 perspective pill；Map 去 pill wall → SVG 空间底图 + 筛选 N | home 12/12、map 13/13 |
| Phase D | Reality event log / Evidence provenance / Contribution 认证态交易流 | reality 14/14、evidence 16/16、contribution 14/14 |
| Final | 全量 10 契约 probe + compare + language + density | `final.json`：TOTAL PASS=164 WARN=1 FAIL=0；language FAIL=0 |

## 3. 关键机制

- **In-page 测量**：`page-eval.ts` 把 probe 函数与 helper 以 `const` 注入同一闭包，解决 Playwright evaluate 无法解析模块导入的问题；`leftRelativeToPane` 取相对最近 pane/inspector 祖先的距离。
- **Page 级规则**：契约规则可用 `pages[]` 限定到具体页面（如 entry 页 vs guard 页、ready 页 vs empty 页），compare.ts 按 `pages[].pageId` 过滤，避免跨状态误判。
- **认证态 probe**：contribution entry 在 `auth: true` 下走真实注册+登录（`pa_token` 进 localStorage），与 `contribute-wizard` e2e 同法——“不能只凭 guard 页存在判 PASS”。
- **端口纪律**：Oracle 栈独立于既有 :8011/:5175 服务；reconstruction/visual/ui-audit 各自端口后移（8013/5177、8014/5178、8015/5179），不杀非本轮启动的进程。
- **数据-ui 命名体系**：语义区域用稳定 `data-ui`（search-shell / place-dossier / reality-timeline / evidence-provenance / contribution-flow 等）；共享组件根 data-ui 由父页面 fallthrough；`PaBottomSheet` 因 Teleport 根不收 data-* 属性而增加显式 `ui` prop。

## 4. 已知 gap（诚实记录，非 FAIL）

- place.mobile 首屏可见文本行 42（契约 `PLACE_MOBILE_FIRST_VIEWPORT_LINES` max=40 / warnAt=30）→ **WARN**：优先 progressive disclosure 而非删信息。
- search.mobile 首屏行 38 → density 诊断 WARN（非契约 FAIL）。
- Android debug APK 在 CDP 调试器附着时，HOME 键背景化会触发 WebView ANR（进程重启）；摘除 CDP 后短生命周期 pid 不变 → 判定为调试器/Harness 产物，非应用缺陷。

## 5. Skill 使用边界

impeccable / frontend-design / ui-ux-pro-max 的模糊建议（“层级更清楚”“留白更多”）**不直接进代码**；其可操作结论先转成数值/结构约束写入契约（行高、宽度、间距、密度、层数），再由 Oracle 测量门禁验证。Playwright 承担 route state setup / deterministic fixture / DOM/bbox/computed style probe / text scan / responsive metrics / screenshots。详见 `BLIND_UI_SKILL_USAGE.md`。

## 6. 退出状态

- `UI_MACHINE_CONTRACT_ACCEPTANCE = PASS`（final gate FAIL=0，WARN=1 已记录）
- `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`（等待人类在 HUMAN_REVIEW 包上签字）
- `UI_VISUAL_CLOSURE = PENDING_HUMAN`
