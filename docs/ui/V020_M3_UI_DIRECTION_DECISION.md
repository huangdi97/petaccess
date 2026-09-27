# V020 M3 UI DIRECTION DECISION

> Impeccable Shape → frontend-design 受约束探索 → canonical rubric 选择 → DESIGN FREEZE。

## 1. 候选方向（frontend-design 受约束探索产物，保留于 `artifacts/ui-audit/concepts/`）

### A. Urban Editorial
- 特征：更强的编辑感排版（大标题 + 分区编辑线）、更重的层级对比、把"附近已核验/规则待核实"做成编辑式分区而非卡片。
- 优点：第一眼记忆点强；缺点：偏离现有 token 节奏、实现改动面大、编辑感与"工具"定位有张力。

### B. Structured Utility（选定）
- 特征：**保持现有 token 世界不动**（中性、克制 accent、1px 边框、受限 radius），通过"统一 surface 语言 + 收敛 pill/卡密度 + 行级 Reality/Freshness/Evidence 摘要 + 桌面真实层级"完成收口。
- 优点：产品契合最高、DS 一致性最高、Generic-AI-UI 风险最低、实现复杂度最低、与 Canonical "Calm/Neutral/Urban" 完全一致。
- 缺点：视觉冲击弱（但 PetAccess 不需要冲击，需要信任）。

### C. Evidence-first Compact
- 特征：更高信息密度、证据元数据前置。
- 优点：信息工具感强；缺点：与本轮 critique "密度过高"直接冲突，会加重过载。

## 2. Rubric 评分（1–5）

| 维度 | A Editorial | **B Structured** | C Compact |
|---|---|---|---|
| Product fit | 3 | **5** | 4 |
| Information hierarchy | 4 | **5** | 3 |
| Rule/Reality clarity | 3 | **5** | 4 |
| Evidence visibility | 3 | **5** | 4 |
| Visual calmness | 4 | **5** | 2 |
| Density | 4 | **5** | 2 |
| Mobile usability | 3 | **5** | 3 |
| Desktop adaptability | 4 | **5** | 3 |
| Accessibility | 3 | **5** | 3 |
| Implementation complexity | 2 | **5** | 3 |
| DS consistency | 3 | **5** | 4 |
| Generic-AI-UI risk | 3 | **5** | 3 |
| **合计** | 39 | **60** | 38 |

## 3. 决策

**选定 B: Structured Utility（精修现有世界）。** 理由：
1. PetAccess 已有成熟 token SSOT + 语义状态体系（中性、克制、Evidence-first），本轮 gap 是**层级与密度**而非视觉身份——重排结构比换皮更符合 Canonical。
2. "成熟信息工具"的目标由结构达成：统一 surface、收敛 pill、Rule/Reality 双事实可见、桌面真 adaptive。
3. A/C 都增加 Generic-AI-UI 或过载风险，与 Goal §104 直接冲突。

## 4. 拒绝项及原因

- 拒绝 A（Editorial）：大标题编辑感会与"工具可信"定位产生张力，且改动面超过 M3 范围。
- 拒绝 C（Compact）：critique 实证首屏已过载（3 组可点项 + 高 tag 密度），再增密度违背 Distill 原则。
- 拒绝换字体（Google Fonts / 展示字体）：离线/网络依赖 + 与系统栈冲突；PetAccess 是工具，system 栈最稳。
- 拒绝任何 gradient / glassmorphism / 大 radius / 重 shadow：craft-floor 禁令 + Canonical 明确排除。

## 5. DESIGN FREEZE（此后 frontend-design 不再随机换风格）

冻结不变量：
1. Token SSOT 不变：color/typography/spacing/radius/border/shadow 全部从 `@petaccess/design-tokens` 读取，页面不得新增私有值。
2. 语义色不单独表意：状态 = Text + Icon + Structure + Color。
3. 无渐变、无玻璃拟态、无发光按钮、无 AI 紫蓝渐变。
4. Radius 保持受限（sm 6 / control 8 / md 10 / lg 12 / pill）。
5. Card 仅用于 interactive container / strong semantic grouping；Badge 仅用于重要语义状态与小分类元数据。
6. Rule 与 Reality 可区分（badge 族 vs 摘要族）但同属一个设计语言。
7. Home/Search 使用 ConsumerAppShell 框架（移除旧 AppShell 双层包裹），上下文信息收敛为页面内单行。
8. 行级信息：Place identity → Rule 主结论 → Reality 摘要 → Freshness/Evidence 元数据；重要 divergence 仅相关时出现。
9. Desktop（≥768 rail / ≥1280）有真实层级（Home 宽容器 + 分区，Search split 保留）。
10. 移动主导航：首页/地图/贡献/我的（tabbar）；Search 属任务流（rail 第二入口，不强制第五 tab）。
11. Motion 仅服务导航/状态反馈；respect prefers-reduced-motion。
12. 文案沿用 EMPTY_STATE_COPY / FRESHNESS_COPY / REALITY_STATE_LABELS 等共享词汇，不新造。

## 6. 候选概念归档

- `artifacts/ui-audit/concepts/A_urban_editorial.md`
- `artifacts/ui-audit/concepts/B_structured_utility.md`（选定）
- `artifacts/ui-audit/concepts/C_evidence_first_compact.md`
