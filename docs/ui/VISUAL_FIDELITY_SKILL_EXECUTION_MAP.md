# Visual Fidelity — Skill Execution Map（本轮真实读取本机 Skill 文档）

> Goal §21：必须重新读取本机真实 SKILL.md，记录实际路径、文档特征、本轮使用能力、禁止能力与对应 phase。

## 1. Impeccable — 主视觉审查者（Phase A: Search + Place）

- **实际路径**：`C:\Users\Kaiser\.agents\skills\impeccable\SKILL.md`（Skill 加载器返回同一路径）
- **文档特征**：Commands 表（critique/audit/polish/layout/typeset/distill/harden/adapt 等）；Routing；Mode 体系（Operate/Read/…）；禁止 init/onboard/overdrive/bolder/delight/context.mjs 覆盖 Canonical。
- **本轮使用**：
  - `distill`（结果行信息预算：删「已核验：」前缀、删别名匹配机制语言、降规则条数为极轻元数据）；
  - `layout`（Search 桌面 List–Detail 两栏、Place Dossier + Sticky Inspector 比例与节奏）；
  - `typeset`（tokens.css 新增 14/17/18/19/22/26/30 字号阶梯，Decision Inspector 大结论 26px/22px）；
  - `critique` 流程应用于真实截图（见 VISUAL_FIDELITY_REVIEW.html 每格 notes）；
  - `harden`（unknown/empty/error 态保留，Place Unknown 截图取证）。
- **本轮禁止**：`init`（不重写设计生命周期）、`onboard`、`overdrive`、`bolder`、`delight`、盲跑 `context.mjs`（Canonical/Design Freeze 仍为权威）。
- **对应 phase**：Phase A（Search+Place 先 Desktop 后 Mobile），后续 Phase B/C 复用同顺序。

## 2. frontend-design — Production Craft（Phase A 实现层）

- **实际路径**：`C:\Users\Kaiser\.agents\skills\frontend-design\SKILL.md`
- **文档特征**：先 plan（color/type/layout/principles）→ 对照 brief 自检 → build → 自我 critique；避免通用模板 traits； restrained。
- **本轮使用**：CSS grid/flex 双栏构成、selected 行 subtle tint + 2px accent bar、Inspector 判定块（sunken 底 + accent 左边线）、移动端压缩（rules/branch display:none）、disclosure toggle（历史版本折叠）。
- **本轮禁止**：新字体、新 palette、新 icon library、新组件框架、改 product wording（消费者语言由 Consumer Label SSOT 决定）、改 IA。
- **对应 phase**：Phase A；B/C 实现沿用同一 craft 纪律。

## 3. UI UX Pro Max — 定向研究（本轮 0 次检索）

- **实际路径**：`C:\Users\Kaiser\.agents\skills\ui-ux-pro-max\SKILL.md`；search 入口 `python "C:/Users/Kaiser/.agents/skills/ui-ux-pro-max/scripts/search.py" <query> --domain <domain>`
- **本轮使用**：Phase A 的设计方向已由 Design Freeze + Approved Reference + 人工视觉失败证据冻结，未进行新检索（避免漫无边际研究；Goal §24 允许最多 1–2 次定向检索）。
- **本轮禁止**：`--persist` 生成另一套 MASTER；不覆盖 Canonical。
- **对应 phase**：如 Phase B（Map filter panel / bottom sheet 信息优先级）确需定向检索时使用，结果追加 `docs/ui/VISUAL_FIDELITY_PATTERN_NOTES.md`。

## 4. Playwright — Rendered Reality Authority（Phase A 全流程）

- **实际路径**：`C:\Users\Kaiser\.agents\skills\playwright-cli\SKILL.md`；项目内使用 `@playwright/test` + 各 config（e2e / ui-reconstruction / ui-audit / visual）
- **文档特征**：浏览器会话、snapshot、screenshot、route mock、console 采集等能力；WebMCP 提示。
- **本轮使用**：
  - 复用本机已装 Chrome（`PLAYWRIGHT_CHANNEL=chrome`，4 个 config 加 env-conditional channel 覆盖，Goal §11：有兼容 Chromium 就不下载）；
  - 真实渲染截图（`artifacts/visual-fidelity-recovery/{baseline,phase-a}`，Phase A 8 张，0 pageerror）；
  - Consumer Visible Text Leakage Gate（新 spec `tests/ui-reconstruction/consumer-leakage-gate.spec.ts`，Phase A 页面 UUID/raw enum/invariant = 0）；
  - 结构门禁 phase1-gate 25/25、a11y-gate 30/30、e2e affected suites 单跑全绿。
- **本轮禁止**：把 accessibility tree 当视觉判断；为凑数量重跑 90 张矩阵；下载新浏览器（有 Chrome 即禁用）。
- **对应 phase**：A（Search/Place）/ B（Home/Map）/ C（Reality/Evidence/Contribution）均以真实截图 + leakage gate 收口。

## 5. 结论

本轮 Phase A 只用了 Impeccable（critique/distill/layout/typeset/harden）、frontend-design（craft）与 Playwright（rendered reality）。UI UX Pro Max 本轮未检索（方向已冻结）。全部能力使用均以 Canonical + Design Freeze + Approved Reference 为权威，未覆盖任何既有设计母版。
