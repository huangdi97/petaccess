# Blind UI V4 Human Review Manifest — 人审截图包清单

> 实现基准：`IMPLEMENTATION_BASE = e1c5ca7`。
> 证据位置：`artifacts/blind-ui-productization-v4/HUMAN_REVIEW/`（已 commit 进分支）。
> 每张截图的 integrity metadata（expected/actual route、page、state、fixture、entity、h1、
> component counts）来自真实 DOM（O6 延续）；metadata 只证明「截图是真实状态」，
> 不宣称视觉通过。Agent 不代替用户做视觉签字。

## 1. 总览

- 截图总数：**24 张 curated viewport 截图（全部 VALID）** + `HUMAN_REVIEW_INDEX.html`。
- 视口：desktop 1440×900；mobile 430×932（§47）。全部为 viewport 截图；
  无 full-page 截图（`place_fullpage_audit.png` 本轮未生成，长度审计由 oracle
  `PLACE_*_OVERVIEW_FULLPAGE_HEIGHT` 契约覆盖）。
- 截图从 page top capture（§51 Reality gate 不靠 scrollTo 证明）。
- 全部通过 Capture State Integrity：`valid=true`、mismatches=[]。

## 2. 分相清单（24 张）

### phase-a-search（4）

| 截图 | 视口 | fixture | h1 | 说明 |
| --- | --- | --- | --- | --- |
| search_desktop_ready | 1440×900 | search-ready-v1 | 搜索场所规则 | list-detail；toolbar 结果数\|筛选；row 92–108 |
| search_desktop_empty | 1440×900 | search-empty-v1 | 搜索场所规则 | inline empty；右侧 onboarding copy |
| search_mobile_ready | 430×932 | search-ready-v1 | 搜索场所规则 | 单列 rows 88–104 |
| search_mobile_filter | 430×932 | search-filter-v1 | 搜索场所规则 | 筛选 bottom sheet |

### phase-b-place（5）

| 截图 | 视口 | fixture | entity / h1 | 说明 |
| --- | --- | --- | --- | --- |
| place_desktop_overview | 1440×900 | place-ready-v1 | 5a9084d0… / 云栖中心·测试商场 | Overview 五块 |
| place_desktop_rules | 1440×900 | place-ready-v1 | 5a9084d0… / 云栖中心·测试商场 | 规则 view（折叠历史） |
| place_desktop_unknown | 1440×900 | place-unknown-v1 | 3b5a341a… / 星河咖啡·栖霞分店 | UNKNOWN 只渲染有数据部分 |
| place_mobile_overview | 430×932 | place-ready-v1 | 5a9084d0… / 云栖中心·测试商场 | 首屏 ≤22 lines |
| place_mobile_rules | 430×932 | place-ready-v1 | 5a9084d0… / 云栖中心·测试商场 | 横滑 text tab；规则 view |

### phase-c-home-map（5）

| 截图 | 视口 | fixture | h1 | 说明 |
| --- | --- | --- | --- | --- |
| home_desktop | 1440×900 | home-ready-v1 | 去之前，先看看这里的规则和现场。 | max 960；divider rows |
| home_mobile | 430×932 | home-ready-v1 | 同上 | 单列 rows + lenses |
| map_desktop | 1440×900 | map-ready-v1 | 规则地图 | List+Map；divider rows |
| map_mobile_ready | 430×932 | map-ready-v1 | 规则地图 | 未选中态 |
| map_mobile_selected_sheet | 430×932 | map-ready-v1 | 规则地图 | bottom sheet（tabbar 上方） |

### phase-d-rest（10）

| 截图 | 视口 | fixture | h1 | 说明 |
| --- | --- | --- | --- | --- |
| reality_desktop_ready | 1440×900 | reality-ready-v1 | 现场轨迹 | timeline 首屏（first event top 275.5px） |
| reality_desktop_empty | 1440×900 | reality-empty-v1 | 现场轨迹 | inline empty |
| reality_mobile_ready | 430×932 | reality-ready-v1 | 现场轨迹 | timeline-first |
| evidence_desktop_ready | 1440×900 | evidence-records-v1 | 证据与来源 | identity + provenance 前 3 步 |
| evidence_desktop_empty | 1440×900 | evidence-empty-v1 | 证据与来源 | 存在记录时不显示「0 条依据」 |
| evidence_mobile_ready | 430×932 | evidence-records-v1 | 证据与来源 | mobile identity + provenance |
| contribution_desktop_choose-type | 1440×900 | contribution-choose-type-v1 | 你刚刚知道了什么？ | 5 choice rows（>=4 首屏） |
| contribution_desktop_step-1 | 1440×900 | contribution-step-1-v1 | 现场贡献 | 步骤 1 / 3 |
| contribution_desktop_step-2 | 1440×900 | contribution-step-2-v1 | 现场贡献 | reality 父流程 步骤 2 / 3 |
| contribution_mobile_choose-type | 430×932 | contribution-choose-type-v1 | 你刚刚知道了什么？ | 932px 内 >=4 choice rows |

## 3. Integrity 机制（O6 延续）

每张截图的 `*.json` 记录：

```
route / page / state / fixture / entityId / selectedId / count / counts
expected（契约）+ actual（真实 DOM）+ valid + mismatches
```

- 全部 24 张 `valid=true`，`mismatches=[]`（实测 0 invalid）。
- 截图在 O6 断言通过**之后**才写入正式目录；失败的进 `_invalid/`（本轮 0 张）。
- `HUMAN_REVIEW_INDEX.html` 汇总 24 张 VALID + 每张的 phase/viewport/route/integrity/note，
  不做任何美学评价。

## 4. 机器证据交叉核对

- compare（final）：10 契约 TOTAL PASS=368 WARN=0 FAIL=0；place.desktop 61 / place.mobile 32 /
  reality 35 / evidence 35 / contribution 45 / search.* 90 / home 18 / map 20 / global 32。
- language scan（final）：26 页 FAIL=0。
- 完整 e2e 189 passed；ui-reconstruction（responsive/a11y/leakage/phase gates）180 passed。

## 5. 人审步骤（给用户）

1. 打开 `artifacts/blind-ui-productization-v4/HUMAN_REVIEW/HUMAN_REVIEW_INDEX.html`。
2. 目视 24 张截图，对照每张 note 的规格要点。
3. 确认后请明示 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`，届时才允许：
   - 更新 `tests/visual/**-snapshots/*.png` baseline；
   - master 集成（另行请求，不自动执行）。
