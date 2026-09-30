# Blind UI v2 — Phase A：Search 机器报告

Status: PASS（机器门禁全过；人审门 PENDING）
Branch: `feat/blind-ui-compiler-v2`（HEAD `18646e1`）
执行时间：2026-09-30 ~ 2026-10-01（实测）

## 1. 状态重置表（规范 §1，如实反映）

| 项 | 升级前基线（历史） | v0.2.3 蓝图要求 | 本轮实测 |
|---|---|---|---|
| SEARCH_VISUAL_COMPOSITION | FAIL（历史 false-positive 契约） | 蓝图 §21–26 | **PASS**（本轮机器契约全过） |
| STATE_INTEGRITY_ORACLE | FAIL（升级前） | §14/§41 | **PASS**（O6 接线，4 张截图 VALID） |
| CONTENT_BUDGET_ORACLE | FAIL（旧行预算） | §21.5 row ≤5 行 | **PASS**（line-box 桶合并计数） |

旧 PASS 不删除，仅附本表解释；warm pass（radius 12 / shadow 行）仅保留在 git 历史。

## 2. 机器门禁（final compare，实测）

| Gate | PASS | WARN | FAIL |
|---|---|---|---|
| search.desktop | 52 | 0 | 0 |
| search.mobile | 38 | 0 | 0 |
| **Search 合计** | **90** | **0** | **0** |

Language scan（search.desktop×2 + search.mobile×2 = 4 pages）：**FAIL=0**
（uuid / enums / invariants / allcaps / refs 全 0 命中）。

## 3. 蓝图关键点实测

- 桌面 1440×900 四区：Rail 68 / Topbar 60 / Results 400 / Detail 列（972 布局，
  detail 内容列 704）——element 契约 PASS。
- Row：高 112–132、radius=0、divider（border-bottom）、文本 ≤5 行——PASS。
- Selected row：subtle tint + 2px 指示，禁 floating card——PASS。
- Detail：Decision y=212–284、首屏 ≥5 semantic blocks、最大语义 gap ≤72——PASS。
- Empty：只存在于 ResultsPane、右侧 onboarding、禁 shadow/radius≤8/width≤340——PASS。
- Mobile 430×932：row 高 108–128、bottom nav 58–64、filter bottom sheet
  radius 16——PASS。
- **§21.5 移除**：规则数量/来源计数行不再上 Search row（蓝图明文禁止）；旧 e2e
  断言（`result-rules`）同步为 decision-line 语义（flagship 有 `row-rule`、branch
  无 answer 无 `row-rule`、`result-rules` 计数为 0），并保留「同品牌分行 + 所属标注 +
  answer-first」意图——不是删测试。

## 4. 人审截图（phase-a-search，4 张全部 VALID）

- `search_desktop_ready` / `search_desktop_empty` / `search_mobile_ready` /
  `search_mobile_filter`；metadata 的 actual 全部来自真实 DOM；
  `_invalid/` 不存在。
- 状态断言：desktop ready → `state=ready-selected`（桌面自动选中首行，真实 DOM
  行为）；empty → `state=empty`；mobile filter → `state=filter`。

## 5. 回归影响

- e2e `h5-journey`「同品牌分行」按蓝图同步断言后串行通过；全量 e2e 串行 189/189。
- visual 基线：Search 相关 consumer 基线按蓝图重生成（见 final report）。

## 6. 结论

Phase A 机器门禁全 PASS（90/0/0），4 张截图 VALID，无 FAIL；人审门 PENDING。
