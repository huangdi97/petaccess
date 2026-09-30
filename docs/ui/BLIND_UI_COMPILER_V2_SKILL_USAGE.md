# Blind UI Compiler v2 — Skill Usage

> v0.2.3 规范 §9–§13。本文件如实记录本轮实际读取/使用的 Skill、每个 Skill 在本轮
> 的真实职责，以及「模糊 skill 输出 → 数值契约」的编译过程。**只记录真实发生的事**，
> 不虚构“已使用”。本轮所有验收仍是无视觉机器验收；截图只作为人审工件。

## 1. 实际读取的 Skill（本轮）

| Skill | 读取方式 | 本轮真实职责 |
|---|---|---|
| impeccable | 已加载（会话内 Skill 文档） | 将“craft / 层级 / 留白”类模糊语言编译为可测量数值约束；输出进入契约 JSON 与 tokens |
| frontend-design | 已加载（会话内 Skill 文档） | 契约 → 实现计划的落地约束（token 引用、布局策略、组件抽取边界） |
| ui-ux-pro-max | 已加载（会话内 Skill 文档） | 针对性 pattern research → RULE / IMPLEMENTABLE CONSTRAINT / ANTI-PATTERN；本轮用于 timeline/provenance/bottom sheet/dossier 等具体 pattern |
| playwright-cli | 已加载（会话内 Skill 文档） | 浏览器驱动、确定性 fixture、DOM/bbox/computed probe、Capture State Integrity、截图证据 |

说明：以上 Skill 在本会话以文档形式加载过一次；模糊输出一律先编译成数值契约再进入
代码（见 §2）。本轮没有调用任何视觉模型；Agent 不“看”截图。

## 2. 模糊 Skill 输出 → 数值契约（编译过程）

| Skill 模糊语言 | 编译后的数值/结构契约（进入 `docs/ui/contracts/json/*.json` 或 tokens） |
|---|---|
| “层级要清楚” | identity 28/650、decision 30/650、section title 18/26/600、metadata 12–13；相对层级 `SECTION_TO_BODY≥1.15`、`DECISION_TO_BODY≥1.75`（Search/Place）、`PAGE_TITLE_TO_BODY≥1.6` |
| “留白不要空洞” | largestVerticalGap 上限（Search Detail ≤72、Home ≤180）；section gap 用 token 阶梯 4/8/12/16/20/24/28/32/40/48 |
| “行要干净 / 不要卡片” | divider row：`radius=0`、`box-shadow:none`、`border-bottom`；structure 规则 forbiddenClass `panel/card`（Search 行、Reality 事件、Provenance 步） |
| “时间线要对齐” | time col 72px / rail col 24px / content remaining；`xConsistent`（同列 x spread ≤1px）；`gridTemplateColumns startsWith "72px 24px"`；rail 连续（real rail element height≥60） |
| “来源链要清楚” | marker col 24px + content remaining；`gridTemplateColumns startsWith "24px"`；marker x 一致；step gap 28–36；恰好 5 步且标签为 原始证据/地点匹配/时间确认/来源确认/人工核验 |
| “contributor 要诚实” | §41：`data-ui-page=contribution`、`data-ui-state=choose-type`、h1=你刚刚知道了什么？、choice-count=5；consumer copy 禁 ADR/RFC/TD/UUID/enum（位置 copy 用规范正确版） |

## 3. 本轮各 Skill 的实际产物

- **impeccable** → 六层 Oracle 中 O3/O4/O5 的阈值来源（相对层级、内容预算、构图上限），
  并约束“禁止 hero/card/pills/chips 化 Home、禁 rule-count 行”等结构红线。
- **frontend-design** → Search 桌面 4 区（rail 68 / topbar 60 / results 400 / detail 列
  704）、Place dossier+sticky inspector、Reality/Evidence max-width 820、Contribution
  向导步骤机的实现落地；全部尺寸引用 design-tokens，未发明新数值。
- **ui-ux-pro-max** → pattern research 产物（timeline rail、provenance rail、bottom
  sheet radius 16、selected row tint+2px indicator、empty-state onboarding），全部
  编译为契约行后才实现；未持久化新 design system。
- **playwright-cli** → `tests/ui-oracle/oracle.spec.ts` + `human-review.spec.ts`
  （probe 先于 interactions 之后测量、每张截图先断言真实 DOM 状态再保存）、
  `playwright.ui-oracle.config.ts`（petaccess_visual + API:8012 + preview:5176）。

## 4. 本轮 Skill 产出一览（机器可验证）

- `docs/ui/contracts/json/*.json`（10 份，含 expect 状态块与 refs 扫描开关）；
- `tools/ui-oracle/{contracts,probe,compare,language-scan,run-language}.ts`
  （O1–O6 六层实现，新增 xConsistent / gridTemplateColumns / startsWith / refs）；
- `tests/ui-oracle/*.spec.ts`（probe + Capture State Integrity 人审包）；
- `artifacts/blind-ui-compiler-v2/{HUMAN_REVIEW,reports}/`（16 张 VALID 截图 + 5 份阶段报告）；
- 页面实现：Search/Place/Home/Map/Reality/Evidence/Contribution 七个视图 + tokens。

## 5. 诚实边界

- 未调用视觉模型；截图仅作为 Human Review Artifact；
- 模糊建议未经数值编译不进入代码；本表即编译记录；
- 本文件只记录真实加载与使用的 Skill 及真实产物，不虚构。
