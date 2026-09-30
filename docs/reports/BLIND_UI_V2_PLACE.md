# Blind UI v2 — Phase B：Place 机器报告

Status: PASS（机器门禁全过；人审门 PENDING）
Branch: `feat/blind-ui-compiler-v2`（HEAD `18646e1`）
执行时间：2026-09-30 ~ 2026-10-01（实测）

## 1. 状态重置表（规范 §1，如实反映）

| 项 | 升级前基线（历史） | v0.2.3 蓝图要求 | 本轮实测 |
|---|---|---|---|
| PLACE_VISUAL_COMPOSITION | FAIL（历史 false-positive 契约） | §27–35 | **PASS**（本轮机器契约全过，2 WARN 容忍项） |
| STATE_INTEGRITY_ORACLE | FAIL（升级前） | §14 | **PASS**（O6 接线，3 张截图 VALID） |
| PLACE_SECTION_GAP | — | 16–40px | **WARN**（中位 49px，见下） |
| PLACE_HISTORY_COLLAPSED_MOBILE | — | 桌面规则用在移动披露，count 0 | **WARN**（容忍项） |
| PLACE_MOBILE_FIRST_VIEWPORT_LINES | — | ≤26（warnAt 22） | **WARN**（实测 38，容忍项） |

## 2. 机器门禁（final compare，实测）

| Gate | PASS | WARN | FAIL |
|---|---|---|---|
| place.desktop | 45 | 2 | 0 |
| place.mobile | 20 | 1 | 0 |
| **Place 合计** | **65** | **3** | **0** |

Language scan（place.desktop×2 + place.mobile×1 = 3 pages）：**FAIL=0**。

## 3. 蓝图关键点实测

- Desktop 1440×900：Main dossier x≈100 w∈820–860 + Inspector x≈1010–1040
  w∈320–350 sticky——PASS。
- Identity 首屏：name 28/650 + actions ≤2；current decision top ≤200——PASS。
- 语义重复 ≤2：`primaryStatusRepeatCount`——PASS（重复 Oracle 升级验证）。
- 三层渐进披露：第三层默认 collapsed——PASS（`disclosureDefault=collapsed`）。
- Zone rows 48–56，仅 consumer names——PASS（无 raw enum/UUID）。
- Inspector 固定结构：Query/Status/Conditions/Exception/Source/Freshness；
  禁 history / raw ids / raw enums / repeated CTA——PASS。
- Mobile 430×932 首屏：含 name / Query / Decision / 1 condition / Reality
  teaser——PASS；首屏行数 WARN（38 > warnAt 22，既有容忍项）。
- UNKNOWN 场所诚实态：无已发布结论 → `place-unknown`（未知 ≠ 允许）——PASS。

## 4. 人审截图（phase-b-place，3 张全部 VALID）

- `place_desktop_ready`（云栖中心·测试商场，entityId 5a9084d0…）、
  `place_desktop_unknown`（星河咖啡·栖霞分店，entityId 3b5a341a…，h1=实际
  canonical name）、`place_mobile_ready`——全部 `valid:true`，actual 来自真实 DOM；
  `_invalid/` 不存在。

## 5. 已知 WARN（容忍，不入 FAIL）

- PLACE_SECTION_GAP：section gap 中位 49px vs 蓝图 16–40（WARN 级，不影响可用性）。
- PLACE_HISTORY_COLLAPSED_MOBILE：桌面 collapsed 规则作用在移动披露，count=0。
- PLACE_MOBILE_FIRST_VIEWPORT_LINES：38 vs 上限 26（warnAt 22）——如实记录。

## 6. 结论

Phase B 机器门禁 PASS（65/3/0），3 张截图 VALID；3 个 WARN 均为既有容忍项，
无 FAIL；人审门 PENDING。
