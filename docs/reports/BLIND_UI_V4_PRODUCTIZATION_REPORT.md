# Blind UI V4 Productization Report — 机器产品化收口报告

> 实现基准：`IMPLEMENTATION_BASE = e1c5ca7`（完成代码与测试后的实现 commit）。
> 分支最终 HEAD 以 Git 查询为准（feature branch pushed）。

## 1. 结论

- **UI_MACHINE_PRODUCTIZATION = PASS**（本轮机器门禁全部实测通过）。
- **UI_HUMAN_VISUAL_ACCEPTANCE = PENDING**（等待人工视觉签字，Agent 不代替）。
- **UI_VISUAL_CLOSURE = PENDING_HUMAN**（视觉 baseline 未提升，等人工 PASS）。
- MASTER_MERGE = NOT_PERFORMED；VISUAL BASELINE UPDATED = NO。

## 2. 工作区 / Git 基线

- `git rev-parse --show-toplevel` = `E:/AI/宠物管理`。
- 分支 = `feat/blind-ui-productization-v4`；基点 = `feat/blind-ui-compiler-v2 @ 90d57e6`
  （先行 28 / 落后 0 与契约一致）。
- `master` = `842c030`（本地与 origin 均未变）；`v0.1.0` tag 未移动；无 force push、无历史改写。
- `tests/visual/**-snapshots/*.png` 在本分支无改动（`git status --porcelain tests/visual/` 为空）。

## 3. 七页产品化结果

| 页面 | 规格 | Oracle 结果 | 关键实测 |
| --- | --- | --- | --- |
| Search | §11–14 | search.desktop PASS=52 / search.mobile PASS=38，FAIL=0 | 无 duplicate badge；detail 620–680；row 92–108/88–104 |
| Place | §15–28 | place.desktop PASS=61 / place.mobile PASS=32，FAIL=0 | Overview desktop 1181px(<=1500)；mobile 465px(<=2000)；首屏 22 行(<=24)；section gap 24(<=40) |
| Home | §29–31 | home PASS=18，FAIL=0 | main max 960；divider rows；无大白卡/pending card/为什么 pill |
| Map | §32–33 | map PASS=20，FAIL=0 | desktop 无地图/列表 pill；divider rows；selected marker 1.2–1.4x + halo |
| Reality | §34–36 | reality PASS=35，FAIL=0 | timeline-first；first event top 275.5px(<=360)；一行 metadata |
| Evidence | §37–40 | evidence PASS=35，FAIL=0 | 解析 place/zones/time；identity + provenance 5 步；不显示“0 条依据” |
| Contribution | §41–43 | contribution PASS=45，FAIL=0 | 5 choice rows（icon+title+desc+chevron）64–72px；5/5 首屏可见；隐私降权 |

## 4. Oracle 与机器门禁（全部实际执行）

| Gate | 命令 / 证据 | 结果 |
| --- | --- | --- |
| ui-oracle compare final | `node --experimental-strip-types tools/ui-oracle/compare.ts final` | **TOTAL PASS=368 WARN=0 FAIL=0** |
| 语言扫描 final | `node --experimental-strip-types tools/ui-oracle/run-language.ts final` | 26 页 FAIL=0 |
| vue-tsc | `pnpm --filter @petaccess/client-h5 exec vue-tsc --noEmit` | PASS |
| client-h5 build | `pnpm --filter @petaccess/client-h5 build` | PASS |
| admin build | `pnpm --filter @petaccess/admin build` | PASS |
| eslint | `pnpm exec eslint .` | 0 error |
| prettier check | `pnpm exec prettier --check .` | PASS |
| state integrity (O6) | human-review 每张截图 DOM 断言 | 24/24 VALID |
| responsive | ui-reconstruction 180 tests（1440×900 / 430×932 等 5 视口） | 180 passed |
| a11y | ui-reconstruction a11y-gate | PASS（包含在 180 内） |
| 完整 e2e | `pnpm exec playwright test -c playwright.config.ts` | 189 passed |
| 完整 backend pytest | `python -m pytest -q`（含 Celery worker，petaccess_test DB） | **961 passed / 2 skipped** |

## 5. Oracle 变更记录（最小修正）

- `docs/ui/contracts/json/place.mobile.json`：`PLACE_MOBILE_FIRST_VIEWPORT_BLOCKS/LINES` 增加
  `pages: ["place-mobile-ready"]` 作用域（§28 首屏 gate 针对 overview 页；深链 rules view
  不属于该 gate，避免 false-positive）。阈值保持 max 24 / warn 22 / FAIL >24 不变。
- `tools/ui-oracle/probe.ts`：`sectionGap` 只统计顶层 block（不把 section 内部 h2/row 当成 gap），
  修正密度度量的 inflate。
- `tests/ui-oracle/human-review.spec.ts`：24 张 curated 截图 + O6 integrity 断言
  （输出 `artifacts/blind-ui-productization-v4/HUMAN_REVIEW/`）。
- 未删除 / 未弱化任何既有 O1–O6 断言。

## 6. WIP 阶段发现并修复的缺陷

1. presence/indoor/dining lens 的 `row-lens-headline` 显示 decision 而非 reality（§11 lens 语义）。
2. Place 模式切换（普通携带 ↔ 服务犬通行）后结论不重算（恢复 session watch）。
3. Contribution reality 父流程步骤显示「步骤 5 / 3」（修正为「步骤 2 / 3」）。
4. e2e/reconstruction 并行 worker 下 hash-only goto 可能被 SPA boot 初始导航覆盖，
   统一加 `page.reload()` 加固（与 human-review 同模式，非弱化断言）。

## 7. 退出状态

```
UI_MACHINE_PRODUCTIZATION = PASS
UI_HUMAN_VISUAL_ACCEPTANCE = PENDING
UI_VISUAL_CLOSURE         = PENDING_HUMAN
MASTER_MERGE              = NOT_PERFORMED
VISUAL BASELINE UPDATED   = NO
```
