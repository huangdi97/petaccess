# Blind UI Compiler v2 — Method

Status: v0.2.3 全量机器管道 · 实测完成（人审门 PENDING）
Last updated: 2026-10-01
Branch: `feat/blind-ui-compiler-v2`（HEAD `18646e1`，from `e724f1c`；origin/master `842c030` 未动）

## 1. 什么是 Blind UI Compiler v2

把 UI 验收从「范围规则 + 历史 false-positive 契约」升级为**可执行、可测量、可比较、可阶段验收的 Executable Blueprint**：蓝图数值直接变成机器契约，Probe 从真实 DOM 测量，Compare 输出 PASS/WARN/FAIL，截图只作为人审工件（Agent 不看图）。

## 2. 六层 Oracle（O1–O6）

| 层 | 含义 | 实现 |
|---|---|---|
| O1 Semantic | section 顺序 / heading / CTA / page signature / 内部 enum / UUID / ADR-RFC-TD-AC-PR refs / raw invariant / consumer copy | `probe.ts scanLanguage` + `structure` 规则（mustContainText / forbiddenText / forbiddenClass）+ `language-scan.ts` |
| O2 Geometry | bbox / width / height / alignment / sticky / pane ratio / max content width / 最大空 gap / 时间列与 marker 列 x 对齐 | `measureElement`（width/height/left/top/padding/margin/…）+ `measureDensity`（largestVerticalGap 等）+ 新增 `xConsistent`（同列元素 x spread ≤1px）与 `gridTemplateColumns`（固定列前缀） |
| O3 Relative Hierarchy | `PAGE_TITLE_TO_BODY≥1.6`、`DECISION_TO_BODY≥1.75`、`SECTION_TO_BODY≥1.15`、`METADATA_TO_BODY≤0.92` | `measureHierarchy`（两选择器计算 font-size 之比） |
| O4 Content Budget | Search Mobile row ≤5 行、Place Mobile 首屏 ≤22 行、Search Detail 首屏 ≥5 semantic blocks、Place Desktop 首屏 Identity/Decision/Reality 可见 | `measureBudget`（rowTextLines / firstViewportBlocks / firstViewportTextLines） |
| O5 Composition | largestVerticalGap / contentOccupancy / leftDensity / rightDensity / semanticBlockCount / primaryStatusRepeatCount ≤2 | `measureComposition` |
| O6 State Integrity | 截图前断言 route/page/state/fixture/h1/entity id/result count/selected id/critical component count | `measureState` + `PageDef.expect` + human-review `assertState` |

### v0.2.3 新增的 Oracle 能力

- `xConsistent`（StructureRule）：同选择器所有命中元素共享同一 x（时间线 time col / marker col 对齐证明），spread ≤1px 判 PASS。
- `gridTemplateColumns`（ElementRule prop）：比较 computed `grid-template-columns` 的**固定 px 前缀**（`1fr` 会解析成视口相关 px，只比较固定列，例如 `72px 24px` / `24px`）。
- `refs`（LanguageFlags）：`\bADR-\d+\b` / `\bRFC-\d+\b` / `\bTD-\d+\b` / `\bAC-[A-Z0-9-]+\b` / `\bPR-\d+\b` 在 consumer DOM 0 命中。
- `startsWith`（RangeSpec）：字符串前缀匹配（配合 gridTemplateColumns 固定列）。

## 3. 机器管道（phase A–D）

每个 Phase 的执行顺序：

1. 写/改契约 JSON（`docs/ui/contracts/json/*.json`，无注释、无尾逗号）。
2. Playwright probe：`UI_ORACLE_STAGE=<stage>` + `playwright.ui-oracle.config.ts` 访问每个契约页面（认证页走真实注册+登录），**先跑 interactions 再 probe**（保证测量 DOM == 截图 DOM），写入 `artifacts/blind-ui-recovery/probes/<stage>-<contract>.json`。
3. Compare：`node --experimental-strip-types tools/ui-oracle/compare.ts <stage>` → `artifacts/blind-ui-recovery/reports/compare-<contract>.json` + stage 汇总。
4. Language scan：`run-language.ts <stage>` → `artifacts/blind-ui-recovery/language-scan.json`。
5. 阶段报告：`gen-phase-reports` → `artifacts/blind-ui-compiler-v2/reports/{search,place,home-map,rest,final}.json`。

## 4. 结果口径

- PASS = 机器契约行通过（实测）；WARN = 偏离但在容忍带内；FAIL = 偏离必须修复。
- 报告词汇：PASS / NOT_RUN / PARTIAL / BLOCKED_EXTERNAL。Agent 只报实测结果，不写任何人审 PASS。

## 5. 本轮最终门禁

- Final compare：**PASS=332 WARN=3 FAIL=0**（3 WARN 均为既有 place.mobile 容忍项：PLACE_HISTORY_COLLAPSED_MOBILE、PLACE_SECTION_GAP、PLACE_MOBILE_FIRST_VIEWPORT_LINES）。
- Language scan：**24 pages FAIL=0**。
- Human review 包：**16 张截图全部 VALID**，无 `_invalid`。
- 回归：vue-tsc + vite build PASS；eslint PASS；prettier 3.9.6 PASS（本轮做了 repo-wide LF/format pass）；e2e 串行 189/189；ui-audit 70/70；visual 59/59（consumer 基线按蓝图重生成，admin 未动）；ui-reconstruction 串行 180/180；backend pytest 961 passed / 2 skipped / 0 failed。

## 6. 已知限制与诚实边界

- Agent 不读截图；截图仅作为 Human Review Artifact 进入 `artifacts/blind-ui-compiler-v2/HUMAN_REVIEW/`。
- Android / Windows / FF master 留到人审通过后的后续轮次（本轮不产生对应报告文件）。
- 并行跑 e2e / ui-reconstruction 时 contribute-wizard 存在既有 TEST-001 懒加载 flake（仓库 a8bab37 同类先例），串行全绿；本轮如实记录。
