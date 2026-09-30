# Blind UI v2 — Phase C：Home + Map 机器报告

Status: PASS（机器门禁全过；人审门 PENDING）
Branch: `feat/blind-ui-compiler-v2`（HEAD `18646e1`）
执行时间：2026-09-30 ~ 2026-10-01（实测）

## 1. 状态重置表（规范 §1，如实反映）

| 项 | 升级前基线（历史） | v0.2.3 蓝图要求 | 本轮实测 |
|---|---|---|---|
| HOME_DASHBOARD_COMPOSITION | FAIL（旧 hero/card/pills/chips） | §36 Task Launcher | **PASS**（五结构 + divider rows） |
| MAP_SPATIAL_WORKSPACE | FAIL（旧布局） | §37 Rail+Results+Map | **PASS** |
| STATE_INTEGRITY_ORACLE | FAIL（升级前） | §14 | **PASS**（O6 接线，2 张截图 VALID） |

## 2. 机器门禁（final compare，实测）

| Gate | PASS | WARN | FAIL |
|---|---|---|---|
| home | 17 | 0 | 0 |
| map | 18 | 0 | 0 |
| global（7 页通用签名） | 32 | 0 | 0 |
| **Phase C 合计（home+map）** | **35** | **0** | **0** |

Language scan（home + map = 2 pages）：**FAIL=0**（含 refs 扫描 0 命中）。

## 3. 蓝图关键点实测

Home：
- 非 Dashboard：max width 920；五结构 = Location+Context / Primary Search /
  Recent / Nearby / Secondary Lens——PASS。
- 删除 hero / feature-card / pills / chips 墙：structure 规则
  `HOME_NO_FEATURE_CARD_WALL` / `HOME_NO_PERSPECTIVE_TRIO`——PASS。
- Recent / Nearby 用 divider rows 而非卡——PASS。
- 最大语义 gap ≤180——PASS。
- h1 `去之前，先看看这里的规则和现场。`、state=ready/fixture=home-ready-v1——PASS。

Map：
- Spatial workspace：Rail 68 + Results 380–420 + 地图剩余——PASS。
- 单一「筛选 N」无状态 pill wall：`MAP_NO_FILTER_PILL_WALL`——PASS。
- MockMap：line network（path≥3）/ area polygons（polygon≥2）/ markers（≥4）/
  selected marker（≥1）/ zoom affordance / floating preview（w=280–320 仅一个）——
  全 PASS。
- h1 `规则地图`、state=ready/fixture=map-ready-v1——PASS。

## 4. 人审截图（phase-c-home-map，2 张全部 VALID）

- `home_desktop`（h1=去之前，先看看这里的规则和现场。）与 `map_desktop`
  （h1=规则地图）——全部 `valid:true`，actual 来自真实 DOM；`_invalid/` 不存在。

## 5. 结论

Phase C 机器门禁全 PASS（35/0/0 + global 32/0/0），2 张截图 VALID，无 FAIL；
人审门 PENDING。
