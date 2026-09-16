# Visual Regression Matrix

> **本文件的旧结论已被取代。** 旧版记录「仓库没有截图基线，VISUAL_REGRESSION = FAIL」。
> 当前真实状态见 `docs/frontend/VISUAL_REGRESSION_BASELINE.md`（47 张基线，比对模式全绿）。
> 这里保留的是**历史缺口记录**与当时的判断，用于对照 §4 的三条前置是否真的被满足。

## 1. 旧版记录的真实状态（已不成立）

| 项 | 当时真实值 |
|---|---|
| Playwright 配置 | `playwright.config.ts`，`testDir: ./tests/e2e`，默认视口，无 `projects` 多视口 |
| E2E 用例 | 16 例，全部为功能断言 |
| `toHaveScreenshot` | **0 处** |
| Admin E2E | 无 |

当时判定：**VISUAL_REGRESSION = FAIL**。

## 2. 当时给出的三条前置，以及本轮的落地情况

| # | 前置 | 本轮结果 |
|---|---|---|
| 1 | 冻结 E2E 数据（时间戳、相对时间不漂移） | **已完成**：`page.clock.install({time: "2026-09-15T04:00:00Z"})` 逐例冻结时钟 |
| 2 | 多视口 `projects` + 独立快照路径 | **已完成**：`playwright.visual.config.ts` 5 个 project（390 / 768 / 1440 / admin-1440 / admin-768），快照按 `{name}-{project}-{platform}` 分目录 |
| 3 | 先补 Admin 功能 E2E，再对稳定页面开截图 | **已完成**：Admin 7 页进入视觉基线（登录 → dashboard → 候选 → 证据 → 来源 → 法规 → 审计） |

另有一条当时未列入、但实际是必要条件的：**截图必须能失败**。本轮补了 `assertRendered()` 与
`assertNotErrorState()` 两道护栏，否则错误态与空白页都会被写成"通过的基线"（详见新文件的 §3）。

## 3. 规范矩阵 vs 当前覆盖

| 页面 / 状态 | 规范视口 | 当前 |
|---|---|---|
| Home | 390 / 768 / 1440 | ✅ 3 视口 |
| Search / Search Empty | 390 / 768 / 1440 | ✅ 3 视口 |
| Map / Map Bottom Sheet | 390 / 768 / 1440 | ✅ 3 视口 |
| Place Detail（UNKNOWN） | 390 / 768 / 1440 | ✅ 3 视口 |
| Place Detail（CONDITIONAL） | 390 / 768 / 1440 | ✅ 3 视口 |
| Rule Trace | 390 / 768 / 1440 | ✅ 3 视口 |
| Contribution | 390 / 768 / 1440 | ✅ 3 视口 |
| Profile / Mine | 390 / 768 / 1440 | ✅ 3 视口 |
| Boundary（共处边界） | 390 / 768 / 1440 | ✅ 3 视口 |
| Evidence Detail（独立页） | 390 / 768 / 1440 | ❌ 只在 Admin 侧覆盖 |
| RESTRICTED / STALE / NETWORK_ERROR 状态页 | 390 / 768 / 1440 | ❌ 未单独出图 |
| Admin 登录 / Dashboard / 候选 / 证据 / 来源 / 法规 / 审计 | 768 / 1440 | ✅ 2 视口 |
| Admin Publish Gate（发布确认） | 768 / 1440 | ❌ 需要交互态，未出图 |
| Admin 390 | 390 | ❌ 未做（Admin 是桌面治理工具，未定 390 断点要求） |

## 4. 结论

**VISUAL_REGRESSION = PASS**（当前状态见 `VISUAL_REGRESSION_BASELINE.md`）。

§3 里带 ❌ 的 4 行是本轮**明确的未覆盖项**，不冒充为通过。
