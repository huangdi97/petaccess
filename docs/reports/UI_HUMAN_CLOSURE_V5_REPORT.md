# UI Human Closure V5 Report — 机器收口报告（Human Visual Closure / Interaction & Brand Polish）

> 实现基准：`IMPLEMENTATION_BASE` = v5 代码与测试完成后的实现 commit（分支历史内可查；
> 本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准；feature branch pushed）。
> 分支基点 = v4 head `e5a9949`；`origin/master` = `842c030` 未动；`v0.1.0` tag 未动。

## 1. 结论

- **UI_HUMAN_CLOSURE_V5 = MACHINE_PASS**（本轮机器门禁全部实测通过）。
- 七页 `*_CANDIDATE = READY_FOR_HUMAN`；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`
  （等待人工视觉签字，Agent 不代替）；`UI_VISUAL_CLOSURE = PENDING_HUMAN`。
- `VISUAL_BASELINE_PROMOTED = NO`（`tests/visual/**-snapshots/*.png` 零改动）；
  `MASTER_MERGED = NO`；Android FAST / Windows Smoke = NOT_REQUIRED。

## 2. 工作区 / Git 基线

- `git rev-parse --show-toplevel` = `E:/AI/宠物管理`。
- 分支 = `feat/ui-human-closure-v5`；基点 = v4 head `e5a9949`（`git merge-base --is-ancestor
  origin/master HEAD` 0 退出，feature 仍是 master descendant）。
- `master` = `842c030`（本地 = origin，未变）；`v0.1.0` tag 未移动；无 force push、无历史改写；
  工作树 tracked clean（最终状态）。
- `git diff <v4-base>..HEAD --stat tests/visual/` 为空（canonical visual baseline 零改动）。

## 3. Oracle 结果（final）

| 契约 | PASS | WARN | FAIL |
| --- | --- | --- | --- |
| contribution | 47 | 0 | 0 |
| evidence | 35 | 0 | 0 |
| global | 32 | 0 | 0 |
| home | 18 | 0 | 0 |
| map | 20 | 0 | 0 |
| map.mobile（新增 §49） | 22 | 0 | 0 |
| place.desktop | 64 | 0 | 0 |
| place.mobile | 35 | 0 | 0 |
| reality | 35 | 0 | 0 |
| search.desktop | 52 | 0 | 0 |
| search.mobile | 38 | 0 | 0 |
| **TOTAL** | **398** | **0** | **0** |

- 8 个新 gate 全部 FAIL 级且实际执行：PLACE_NO_STRAY_GLYPH / PLACE_NO_ENGINEERING_INVARIANT_COPY /
  PLACE_RULE_GROUP_HAS_CONTEXT / PLACE_MOBILE_OVERVIEW_SUMMARY_PRESENT / MAP_MOBILE_SHEET_OVERLAY /
  MAP_MOBILE_SHEET_ABOVE_TABBAR / CONTRIBUTION_STEP_CONTEXT_PRESENT / CONTRIBUTION_OPTION_ROWS_NOT_PILLS。
- 语言扫描 final：28 页 FAIL=0（含 §48 禁词 `≠`/UNKNOWN/ALLOWED/PROHIBITED/CONDITIONAL/
  source_id/rule_id/zone_type 用户可见 DOM 0 命中）。
- density 诊断 final：21 行 FAIL=0（与 compare gate 使用同一契约值来源，杜绝矛盾）。
- 命令：`$env:UI_ORACLE_STAGE="final"; pnpm exec playwright test -c playwright.ui-oracle.config.ts`
  （13/13 全绿，含 human-review v4 + v5 两个捕获测试）；`node --experimental-strip-types
  tools/ui-oracle/compare.ts final`；`run-language.ts final`；`run-density.ts final`。

## 4. 七页候选结果

| 页面 | v5 关键实测 |
| --- | --- |
| Search | selected tint 轻；Empty 单 primary CTA；mobile toolbar「结果 N|筛选」；detail CTA「查看完整场所 →」 |
| Place | Rule Groups（context 10 组实测）；Unknown Overview 最小化（natural copy）；mobile overview summary rows ×2（56–64px）；Inspector 320px 左对齐、无重复 identity |
| Home | `附近已有依据`/`附近待补充`；nearby row 无重复「已核验：…」 |
| Map | mobile 恒 overlay sheet：half top<700、bottom≤tabbar、overlap map、不 overlap tabbar；expanded ≤78vh；segmented 地图|列表；marker 1.3x+halo |
| Reality | Date=metadata / Time=strong / Fact=body strong / 待核验 small muted+clock |
| Evidence | record identity 更强；stats 层级明确；provenance pending empty-circle muted |
| Contribution | Step Shell（place context + progress + radio option rows）；reality cluster 表单；Done「已提交待核验…」；privacy copy 恢复 |

## 5. 机器门禁（全部实际执行，附命令）

| Gate | 命令 | 结果 |
| --- | --- | --- |
| vue-tsc | `pnpm --filter @petaccess/client-h5 exec vue-tsc --noEmit` | PASS |
| client-h5 build | `pnpm --filter @petaccess/client-h5 build` | PASS |
| admin build | `pnpm --filter @petaccess/admin build` | PASS |
| eslint | `pnpm lint:fe` | 0 error |
| prettier check | `pnpm format:check:fe` | PASS |
| ui-oracle | 见 §3 | 398/0/0 + 13/13 tests |
| language scan | `node --experimental-strip-types tools/ui-oracle/run-language.ts final` | 28 页 FAIL=0 |
| density | `node --experimental-strip-types tools/ui-oracle/run-density.ts final` | 21 行 FAIL=0 |
| state integrity | human-review O6（v4 24 张 + v5 27 张全部 VALID） | PASS |
| responsive | `playwright.ui-reconstruction.config.ts`（8 断点 360/390/430/768/1024/1280/1440/1920，无横向溢出、无 clipped tab、Place mobile tab 横滑、sheet/footer 正确、inspector 仅 desktop、tabbar 仅 mobile） | **180/180** |
| a11y | a11y-gate（1 h1、heading order、focus visible、44px target、radio/option 语义、sheet dialog/region、Esc、reduced-motion） | PASS |
| e2e | `pnpm exec playwright test -c playwright.config.ts` | **189/189 ×2 全绿** |
| backend pytest | `python -m pytest tests services/api/tests`（Celery worker 同 shell，petaccess_test DB） | **961 passed / 2 skipped / 0 failed** |

## 6. 本轮修复的真实 bug（非视觉，纳入回归）

1. Contribution 隐私 copy「提交内容会进入人工核验」丢失 → 恢复（ContributionStepShell + ContributeEntry）。
2. Reality 提交错误 silent failure → 恢复 `reality-error` alert（ContributeRealityForm）。
3. 客户端幂等键同毫秒冲突 → `crypto.randomUUID()`（packages/client-core）。
4. PlaceOverviewPane 宠物上下文行丢失 → 恢复「我的宠物：豆豆」（consumer copy，非工程痕迹）。
5. e2e/reconstruction 并行 boot race → 确定性 token 注入 + 15s bounded waits。
6. `--pa-color-warning` 缺失导致 app CSS 硬编码 hex → token 化（test_design_tokens 恢复 10/10）。

## 7. 人审包

`artifacts/ui-human-closure-v5/HUMAN_REVIEW/`：§42 清单 27 张（search 4 / place 5 / home 2 /
map 4 / reality 3 / evidence 3 / contribution 6），全部 `valid: true`（O6 actual 来自真实 DOM），
含 HUMAN_REVIEW_INDEX.html 与每张 metadata JSON。**metadata 只证明真实状态，不宣称视觉通过。**

## 8. 状态（不得写作 PASS）

`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN` ·
`VISUAL_BASELINE_PROMOTED = NO` · `MASTER_MERGED = NO` · `UI_HUMAN_CLOSURE_V5 = MACHINE_PASS`。
