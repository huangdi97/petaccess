# Visual Fidelity — Pattern Notes（定向研究沉淀）

> Goal §24：UI UX Pro Max 只做定向研究时，结果追加至此；不生成另一套 MASTER。
> Phase A 未触发新检索（方向由 Design Freeze + Approved Reference + 人工视觉失败证据冻结）。

## 落地模式（Phase A 实际采用）

1. **Judgment Inspector**：Inspector = 判定面而非字段表。做法：删除 `<dl>`；决策块 = sunken 底 + accent 左边线 + 26px 判定词；条件为 ✓ 前缀行；时效为顶部细线分隔的元数据。参考：Apple Split Views / inspector-style panes（Goal §73）。
2. **Result Row 信息预算**：6 项上限（identity / type·distance / decision / 1 condition / reality / 极轻 metadata）。降级规则：放不下 → 删次要（移动端隐藏 rules/branch），不缩字（Goal §36）。
3. **Selected 态**：subtle tint + 单一指示（左侧 2px accent bar），非 rounded card（Goal §32）。
4. **Consumer Label SSOT**：一个 mapper 覆盖全部 enum 域；fallback 为消费者安全词；UUID 片段禁止（Goal §29/§30/§3.4）。
5. **Mobile Filter Sheet**：`筛选 N` → PaBottomSheet，复用餐具组件；桌面保留轻量面板。
6. **Progressive Disclosure**：历史版本默认折叠（`disclosure-toggle` + aria-expanded），移动端不无限平铺（Goal §35）。
7. **Typography Token Ladder**：tokens.css 新增 14/17/18/19/22/26/30，页面一律引用 token（Goal §36）。
8. **Leakage Gate**：visible text 层面 UUID/raw enum/invariant 扫描；explicit denylist 防误伤；Phase 分层（A pages / C pages，`LEAKAGE_SCOPE=all` 终态全量）。

## 后续 Phase 待研究问题（Gate B/C 需要时定向检索，最多 1–2 次）

- Map：filter panel 与 bottom sheet 信息优先级（Gate B）
- Reality：时间线视觉节奏（Gate C）
- Evidence：provenance 视觉路径（Gate C）
- Contribution：动态表单信息优先级（Gate C）
