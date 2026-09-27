# V020 M3 SKILL CAPABILITY MAP

> 基于本机实际安装的 Skill 文档（2026-09-27 读取）逐项记录，不假设网络版本。
> 本机 Skill 根目录：`C:\Users\Kaiser\.agents\skills\`（Skill 工具加载路径）。

## 1. Impeccable（设计主导）

- **名称/版本**：impeccable（Skill id: `impeccable`）；目录 `C:\Users\Kaiser\.agents\skills\impeccable\`，含 SKILL.md + reference/*.md + agents/*.toml。
- **入口**：Skill 工具加载 SKILL.md；另有 `node <skill-base>/scripts/context.mjs`（Setup），本仓库无 `.agents/skills` 落地脚本（脚本目录不随项目分发），故 context.mjs 不可执行——以 SKILL.md + reference 文档为准执行（记为环境差异，不影响能力）。
- **可用命令**（reference 文档确认存在）：`init`（PRODUCT.md）、`document`（DESIGN.md 生成）、`extract`、`critique`（双评估：设计审查 + detector）、`shape`（UX 结构）、`layout`、`typeset`、`distill`、`harden`、`adapt`（+ native）、`audit`（技术审计）、`polish`、`bolder`、`quieter`、`animate`、`colorize`、`delight`、`overdrive`、`clarify`、`optimize`、`live`（浏览器视觉变体）、`new-work`（视觉世界替换）、`craft-floor`（质量底线）、`hooks`/`doctor`/`pin`。
- **适用场景**：设计上下文建立（PRODUCT/DESIGN）、现状 critique、UX shape、布局/字体/蒸馏/加固/适配/审计/polish。
- **输入要求**：PRODUCT.md（产品真相）、DESIGN.md（视觉决策）、目标文件或路由；critique 需可解析目标 + 双评估（有 Task 工具时须子代理隔离运行）。
- **输出**：chat 评审结论 + 可持久化快照；layout/typeset 等返回结构改动方案；craft-floor 提供不可违反的质量底线（对比度 ≥4.5:1、正文 measure 45–75ch、禁 eyebrow/kicker、禁 hero-metric 模板等）。
- **能否浏览真实页面**：critique 要求 viewable target 时浏览器检查（可用时）；live 模式接浏览器。
- **能否截图**：通过浏览器层截图（依赖可用浏览器工具）。
- **能否直接改代码**：layout/typeset/distill/harden/adapt/polish 等命令均为改代码流程；本轮按其方法论由 Agent 直接编辑实现。
- **本轮用法**：shape（Home/Search 结构重排）→ critique（现状）→ layout/typeset（实现）→ distill（减噪）→ harden（状态矩阵）→ adapt（360–1440 响应式）→ audit/polish（收尾）。

## 2. frontend-design（受约束探索）

- **名称/版本**：frontend-design（Skill id: `frontend-design`）；`C:\Users\Kaiser\.agents\skills\frontend-design.md`（9351 B）。
- **入口**：Skill 工具加载（单文档，无脚本）。
- **可用命令**：无 CLI；方法论 = 两遍式：① 设计计划（token 系统：颜色 4–6 命名色、字体角色、布局概念 + ASCII wireframe、原则）；② 对照 brief 复核唯一性后写代码。
- **适用场景**：构图/视觉方向探索，避免 Generic AI UI；受限：不得覆盖 DESIGN.md、不得改变产品定位、不得自行添加强烈艺术方向。
- **输入要求**：brief 或产品上下文；输出：设计计划 + 代码。
- **能否浏览/截图**：否（纯方法论）。
- **能否直接改代码**：是（在其工作流内）。
- **本轮用法**：方向探索期生成 2–3 个候选视觉概念的 token 方案（Urban Editorial / Structured Utility / Evidence-first Compact），供 rubric 选择；DESIGN FREEZE 后不再换风格。

## 3. UI UX Pro Max（设计研究员）

- **名称/版本**：ui-ux-pro-max（Skill id: `ui-ux-pro-max`）；目录 `C:\Users\Kaiser\.agents\skills\ui-ux-pro-max\`，含 scripts/search.py + references/（quick-reference.md、pro-rules.md）+ 数据（79 styles / 192 palettes / 74 font pairings / 119 UX guidelines / 105 icons / 17 GSAP / 25 charts / 22 stacks）。
- **入口**：`python "C:/Users/Kaiser/.agents/skills/ui-ux-pro-max/scripts/search.py" "<query>" --domain <domain>`（本机 python 可用，已验证）。
- **可用命令**：`--design-system`（聚合产品/风格/色板/字体 + reasoning）、`--domain ux|style|color|typography|icons|landing|gsap|web|product|chart|google-fonts`、`--stack <vue|...>`、`--json`、`-f markdown`、`--persist/--output-dir/--page`（写设计系统文件）。
- **适用场景**：模式检索、typography/color/navigation/mobile/desktop 模式、a11y heuristics、anti-patterns。
- **输入要求**：查询 2–5 个有意图的词 + 约束；0 结果须重试一次，再空则明示 fallback，不得伪造匹配。
- **输出**：结构化推荐（pattern/style/colors/typography/effects/avoid + 清单）。
- **能否浏览/截图**：否。
- **能否直接改代码**：否（只做研究/推荐；--persist 可写设计系统文档，本轮不采用）。
- **本轮用法**：`--design-system "urban city information utility trust evidence-first neutral"` 已执行（Trust & Authority + Minimalism/Swiss Style 参考），再补 domain 检索（search result anatomy / status presentation / offline UX / desktop adaptation），结果入 `docs/ui/V020_M3_UI_REFERENCE_RESEARCH.md`。

## 4. Playwright（真实验证层）

- **名称/版本**：playwright-cli（Skill id: `playwright-cli`）＋ 仓库 `@playwright/test` 1.63.0（`npx playwright --version` = 1.63.0）。
- **入口**：`playwright-cli`（CLI 0.1.21）或 `npx playwright test --config ...`（仓库既有 config：playwright.config.ts e2e / playwright.visual.config.ts visual / 本轮新增 playwright.ui-audit.config.ts）。
- **可用命令**：open/goto/click/fill/press/snapshot/find/eval/screenshot/console/requests/route（mock）/setOffline/emulation（viewport/device）/go-back/go-forward/reload/run-code 等。
- **适用场景**：真实启动页面、真实 viewport、真实状态、截图、overflow assertion、navigation、URL state、offline/error、responsive、console error/pageerror/unhandled rejection 检查。
- **输入要求**：已启动的服务（本轮：petaccess_visual seed → API :8011 → preview :5175，由 config webServer 自管）。
- **输出**：页面快照 / 截图文件 / console 与请求日志 / 断言结果。
- **能否浏览真实页面**：是（headless Chromium + work-panel 浏览器）。
- **能否截图**：是（已产出 70 张取证截图）。
- **能否直接改代码**：否（测试/验证工具）。
- **本轮用法**：UI-0 修改前取证（70 shots）、M3 后全视觉矩阵（360/430/800/1280/1440 × 状态）、e2e 回归、console 门禁、overflow 断言、Android FAST 的 CDP 截图（按 runbook）。

## 5. 其他已安装 Skill（不在本轮职责内）

- `3d-animation-short-generator` / `brand-promo-video-generator` / `co-op-game-intro-generator` / `handdrawn-live-video-generator` / `minimalist-product-ad-generator` / `music-video-subtitle-generator` / `paper-collage-explainer-generator` / `papercraft-stop-motion-explainer` / `h3-prompt-writing` / `imagegen`：均为内容/视频/图像生成技能，与 PetAccess Consumer UI 无关，本轮不调用（记录于能力清单，避免误用）。

## 职责冻结（Goal §6）

Canonical Master → PRODUCT/DESIGN Context → **Impeccable = Design Lead** → frontend-design（探索）/ UI UX Pro Max（研究）/ Playwright（验证）各自受限；冲突时 Canonical / DESIGN.md wins。
