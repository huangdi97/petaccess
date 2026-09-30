# Blind UI v2 — Phase D：Reality + Evidence + Contribution 机器报告

Status: PASS（机器门禁全过；人审门 PENDING）
Branch: `feat/blind-ui-compiler-v2`（HEAD `18646e1`）
执行时间：2026-09-30 ~ 2026-10-01（实测）

## 1. 状态重置表（规范 §1，如实反映）

| 项 | 升级前基线（历史） | v0.2.3 蓝图要求 | 本轮实测 |
|---|---|---|---|
| REALITY_TIMELINE | FAIL（旧 card 化 timeline） | §38 True Timeline | **PASS**（72/24 列 + rail + x 对齐） |
| EVIDENCE_PROVENANCE | FAIL（旧 surface-row 链） | §39 Rail Provenance | **PASS**（24px marker col + 5 步） |
| CONTRIBUTION_STATE_INTEGRITY | FAIL（截图/metadata 漂移） | §40/§41 | **PASS**（choose-type + choice-count=5 实测） |
| CONSUMER_COPY_REFS | FAIL（含 ADR-012 文案） | §17/§40 禁 refs | **PASS**（ADR/RFC/TD/AC/PR 0 命中） |

## 2. 机器门禁（final compare，实测）

| Gate | PASS | WARN | FAIL |
|---|---|---|---|
| reality | 33 | 0 | 0 |
| evidence | 33 | 0 | 0 |
| contribution | 44 | 0 | 0 |
| **Phase D 合计** | **110** | **0** | **0** |

Language scan（reality×2 + evidence×2 + contribution×4 = 8 pages）：**FAIL=0**。

## 3. 蓝图关键点实测

Reality（§38）：
- 内容 max width 820；每事件 time col 72 / rail col 24 / content remaining——PASS。
- 所有 time x 坐标一致、所有 marker x 坐标一致（`xConsistent` spread≤1px）——PASS。
- timeline rail 连续（真实 rail element，height≥60）——PASS。
- event gap 20–28；date group separation ≥28——PASS。
- 事件非 card（radius 0 / 无 shadow / 无 panel-card class）——PASS。
- 空态文案 = `暂无近期现场记录。` + `这并不代表现场没有动物。`——PASS（§38 原文）。
- O6：`data-ui-page=reality`，state ready/empty，fixture reality-ready-v1 /
  reality-empty-v1——PASS。

Evidence（§39）：
- 内容 max width 820；provenance marker col 24px + content remaining——PASS。
- 恰好 5 步且标签为 原始证据 / 地点匹配 / 时间确认 / 来源确认 / 人工核验——PASS。
- marker x 一致；rail 连续；vertical gap 28–36——PASS。
- 禁 UUID（uuidForbidden + 扫描 0 命中）——PASS。
- O6：`data-ui-page=evidence`，state ready/empty，fixture evidence-records-v1 /
  evidence-empty-v1——PASS。

Contribution（§40/§41）：
- 首屏 h1 `你刚刚知道了什么？`；固定 5 选项；choice-count=5——PASS（实测）。
- consumer copy 禁 ADR/RFC/AC/TD/UUID/enum：位置 copy 使用规范正确版
  「位置信息仅用于核验场所，不保存连续位置轨迹。」，旧 `ADR-012` 文案已移除——PASS。
- 桌面 + 移动都真实进入 `choose-type`；capture choose-type / step-1 / step-2 /
  done 状态机器（O6 state 由真实 wizard step 派生）——PASS。
- 契约页：needs-place / entry(choose-type) / step-1 / step-2，认证态 probe——PASS。

## 4. 人审截图（phase-d-rest，7 张全部 VALID）

- reality_desktop_ready / reality_desktop_empty、evidence_desktop_records /
  evidence_desktop_empty、contribution_desktop_choose-type /
  contribution_desktop_step-2、contribution_mobile_choose-type——全部 `valid:true`，
  actual 来自真实 DOM；`_invalid/` 不存在。

## 5. 历史修复（本轮，含 §0/§15/§41 漂移事实）

- Contribution 截图/metadata 漂移：根节点补 `data-ui-page/state/fixture`，状态由
  placeId+signedIn+step 派生，choose-type 断言 h1 + choice-count=5，实测通过。
- Reality 同像素截图：时间线在 900px 折线下导致两张 PNG 一度字节相同；修复为
  断言状态后滚动至 `trace-observations` 再截图，两张图现已不同且仍先断言后截图。
- 消费者 copy：`不保存原始 GPS 轨迹（ADR-012）` → 规范正确版。

## 6. 结论

Phase D 机器门禁全 PASS（110/0/0），7 张截图 VALID，无 FAIL；人审门 PENDING。
