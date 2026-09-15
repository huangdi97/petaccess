# Admin UI Audit（治理工作台）

> 对照规范 §54–§57、§69。Admin 是治理工具，不是营销站：密度优先、装饰最少。

## 1. 页面清单（真实存在）

23 个 view：`Dashboard / Places / PlaceDetail / Rules / RuleCandidates / Evidence / Sources /
SourceMonitors / Regulations / EventRules / Organizations / Observations / ObservationCandidates /
Claims / Disputes / Conflicts / AiQueue / Audit / MatchDebugger / SpatialExtras / Users / Login`。

治理链路所需的页面——**候选 → 证据 → 来源 → 来源监控 → 发布 → 规则 → 审计**——全部存在。

## 2. 逐项判定

| 项 | 判定 | 依据 |
|---|---|---|
| ADMIN_REVIEW（候选队列） | PASS_WITH_LIMITATIONS | 候选状态机、可迁移状态、抽取原文、备注齐备；**无「AI 建议 vs 人类终裁」的视觉分区** |
| ADMIN_EVIDENCE（证据） | PASS | `EvidenceView` 独立页；候选详情内嵌来源 ID、抽取原文、已发布规则、复核备注 |
| ADMIN_PUBLISH（发布） | PASS | 本轮补上二次确认（见下）；发布仅对 `APPROVED` 可见 |
| ADMIN_AUDIT（审计） | PASS | `AuditView` 独立页；`record_audit` 在 rule 更新时写 `before_state`/`after_state` |
| 危险动作区分（§56） | PASS（本轮修复后） | 发布、驳回均为「两次点击 + 变红 + 改文案」 |
| 表格（§57） | PASS_WITH_LIMITATIONS | 有分页/筛选/状态；**未发现 sticky header 或列宽控制** |
| 技术信息暴露（§69） | PASS | 展示 source_id / published_rule_id 等必要技术字段，不展示密钥 |

## 3. 本轮修复：危险动作二次确认

**修复前**：`RuleCandidatesView.vue` 的「发布为规则」是一个普通 `primary` 按钮，单击即写库；
「→ REJECTED」同样单击生效。整个 Admin 中 `confirm(` 命中数为 **0**。
对一个「写进规范性规则集、用户会据此行动」的动作来说，这是不可接受的。

**修复后**：

```ts
const pending = ref("");
function guard(key: string): boolean {
  if (pending.value !== key) { pending.value = key; return false; }
  pending.value = "";
  return true;
}
```

- 第一次点击：记录 pending，按钮文案变「再点一次确认发布」，class 由 `primary` → `danger`；
- 第二次点击：真正执行；
- 驳回（REJECTED）走同一个 `guard`，因为驳回会丢弃人工复核工作。

采用「两次点击」而非 `window.confirm`，是因为后者在部分嵌入环境被拦截、无法与
`prefers-reduced-motion`/键盘可达性一致，且无法复用既有 `danger` 样式。

## 4. 未达标项

| # | 项 | 现状 | 说明 |
|---|---|---|---|
| 1 | AI 建议 / 人类终裁的视觉分区（§55） | 缺失 | Admin 没有「评审详情三栏」页。当前 Human Review 走**签署包 + `publish_reviewed_r1.py`** 流程，UI 里只有一句状态机说明。这是流程设计而非缺陷，但规范要求的三栏工作台并不存在 |
| 2 | 表格 sticky header / 列宽（§57） | 未实现 | 长来源、长引文在窄屏会撑高行高 |
| 3 | 批量操作的影响范围预览（§56） | 未实现 | 发布前不展示「将影响 N 条规则 / M 个场所」 |
| 4 | Admin 响应式 | 仅一处 `@media (max-width: 900px)` | 窄屏可用，但未做完整断点体系 |

## 5. 结论

**Admin 治理工作台 = PASS_WITH_LIMITATIONS**。
核心治理链路（候选→证据→来源→发布→审计）闭合且可用；发布/驳回已有二次确认；
缺的是评审详情三栏工作台与表格高级能力——这些属于「下一步产品形态」，不在本轮
（禁止新增产品功能）范围内。
