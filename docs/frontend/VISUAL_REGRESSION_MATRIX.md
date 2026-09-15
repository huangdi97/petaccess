# Visual Regression Matrix

> 现状：仓库**没有截图基线**。本文档记录真实覆盖范围，以及为什么本轮没有新增快照。

## 1. 当前真实状态

| 项 | 真实值 |
|---|---|
| Playwright 配置 | `playwright.config.ts`，`testDir: ./tests/e2e`，默认视口（1280×720），**无 `projects` 多视口** |
| E2E 用例 | 16 例，全部为**功能断言**（`getByTestId` / `getByRole` / `getByText`） |
| `toHaveScreenshot` | **0 处** |
| `playwright-out/` `test-results/` | 空（1K，仅目录占位） |
| Admin E2E | 无 |

判定：**VISUAL_REGRESSION = FAIL**（规范 §63 要求的基线并不存在）。

## 2. 为什么本轮没有补

1. 规范 §63 明确要求「动态 timestamp 用 fixture 固定」「不要 snapshot 整个动态页面造成 flaky」。
   当前 H5 首页/详情直接吃真实 API（`:8010` 种子数据），没有固定 fixture 层；
   在没有冻结数据源之前加截图，产出的会是**必然 flaky 的基线**，比没有基线更糟。
2. 生成基线需要先人工确认「这就是正确的样子」，而本轮禁止 AI 代替人类做产品判断。
3. 因此本轮把它作为**明确的开放项**记录在案，而不是造一批假绿的快照。

## 3. 规范要求的矩阵 vs 现状

| 页面 / 状态 | 规范视口 | 现状 |
|---|---|---|
| Home / Search / No Result / Map / Bottom Sheet / Place Detail / Rule Trace / Evidence / UNKNOWN / CONDITIONAL / RESTRICTED / Contribution / Profile | 390 / 768 / 1440 | ❌ 无截图；仅 390 以外视口连功能断言都没有 |
| Admin Review Queue / Review Detail / Evidence / Publish Gate / Audit | 390 / 768 / 1440 | ❌ 无任何 Admin E2E |

## 4. 落地所需的三条前置（下一步，不在本轮）

1. **冻结 E2E 数据**：为 H5 增加只读 fixture 模式（固定 `CAFE_ID` 之外的时间戳与种子），
   使 `latestVerified`、相对时间不再漂移。
2. **多视口 projects**：在 `playwright.config.ts` 增加
   `projects: [{name:'mobile-390'},{name:'tablet-768'},{name:'desktop-1440'}]`，
   并给每个 project 独立 `snapshotPathTemplate`。
3. **先功能后视觉**：先补 Admin 的功能 E2E（登录 → 候选 → 详情 → 审计），
   再对稳定页面开 `toHaveScreenshot({ maxDiffPixelRatio: 0.02 })`。

## 5. 结论

**VISUAL_REGRESSION = FAIL（未实现，非回归）**。
它是对规范 §63 的诚实缺口，不影响签署语义；但签署后进入试点前应当补齐。
