# V020 M3 UI DESIGN GAP AUDIT（Impeccable Critique）

> Impeccable 主设计视角的现状 critique。评估基于：70 张真实截图（360–1440）、源码阅读（AppShell/Home/Search/PlacePreview/tokens）、UI UX Pro Max 研究。
> 页面标记：FINAL / M3-PARTIAL / NEEDS-REDESIGN / FUTURE-M4 / FUTURE-M5 / FUTURE-M7 / RUNTIME-ISSUE。

## 0. 总览

PetAccess 当前不是"丑"，而是**层级未收口**：骨架（AppShell、状态、深链）已成熟，但 Consumer 视觉密度与桌面 hierarchy 停在"功能页面"阶段。M3 深化 = 在不重做 Domain/架构的前提下，把 Home/Search/AppShell 的视觉与信息层级推到"成熟信息工具"。

---

## 1. AppShell（标记：`M3-PARTIAL`）

### 当前视觉第一眼
Desktop rail（深色标签 + 版本脚注）+ 底部 tabbar（mobile）存在，中性、克制、不喧宾夺主。离线 banner / toast / dialog 均 token 化。

### Critique 逐问
- **视觉焦点**：rail 是唯一 chrome，焦点正确地在内容区。
- **下一步**：清楚（tab 即导航）。
- **信息层级**：正确 —— chrome 不含 Rule/Reality 计算（职责正确，无需改）。
- **问题**：
  1. **双重 chrome 残留**：Home/Search 仍包裹旧 `components/AppShell.vue`（ModeBar + 宠物档案 panel），与 ConsumerAppShell 并存 → 桌面出现 "rail + ModeBar + panel" 三层条，宠物档案信息在 Home 顶部与 Search 档案块**重复出现**。这是 M3 必须关闭的层级 gap。
  2. rail 高度/间距为默认 token 值，未显式定义 rail 宽度节奏（可接受，不追求重排）。
  3. 版本脚注存在（合规），但 visual 中性，可保留。

### 处置
- 移除旧 AppShell 双层包裹：Home/Search 直接使用 ConsumerAppShell 框架；ModeBar/宠物档案信息收敛为内容内单处（保留 ModeBar 的查询视角语义，移入页面级工具条，不再作为全页 chrome）。

---

## 2. Home（标记：`M3-PARTIAL`）

### 当前视觉第一眼
标题 + 搜索面板 + 4 个 entry 卡（2×2）+ 视角 pill + 类别 pill + 结果卡。**首屏功能感强、节奏感弱**：全部元素挤在首屏，无主次停顿。

### Critique 逐问（§29 清单）
- **视觉焦点**：无单一焦点 —— 标题、搜索、4 entry、两组 pill 同级竞争。
- **用户是否马上知道下一步**：大致是（搜索框显眼），但 4 个 entry + 3 视角 + 5 类别的三组可点项叠加，选择过载。
- **信息层级是否正确**：部分。标题 > 搜索 > entry > 结果是合理顺序，但 **entry 卡与结果卡是两套卡语言**（entry=border+无填充；结果=panel 白卡），且结果卡内又有 pill（为什么？）+ badge（状态）+ 条件文本，一级信息（规则状态）与二级（条件、原因）混排。
- **Rule 是否过重/过弱**：过弱。每卡只有一个 StatusBadge（小徽标）+ 条件文本；**Rule 结论没有以"主结论"视觉地位呈现**。
- **Reality 是否过重/过弱**：**缺位**。Home 完全不展示 Reality 摘要、Freshness、Evidence —— 与 Goal "Rule + Reality summary" 不符。
- **Evidence 是否存在但看不到**：是。有证据链数据（snapshot），但 Home 不呈现。
- **Freshness 是否清楚**：否。无任何"信息多久前取得/规则何时核验"的可见表达。
- **Card 是否太多**：多。搜索面板 1 + entry 4 + recent（有则）+ 结果卡 N → 白卡墙风险。
- **Pill 是否太多**：多。3 视角 + 5 类别 + 每卡 1 "为什么" + recent "清空" → pill abuse 高风险。
- **Radius 是否太大**：否（10px md，合理）。
- **Shadow 是否太重**：否（无 shadow，正确）。
- **Typography 是否稳定 hierarchy**：基本稳定（h1 2xl / 卡内 strong / muted 元数据），但**无 Reality/Freshness/Evidence 的排版角色**。
- **Whitespace 是否有节奏**：部分。区块间距 24px 均匀，缺乏"第一屏重、第二屏轻"的节奏。
- **信息密度**：mobile 首屏过载；desktop 利用率不足（单列拉满）。
- **Desktop 是否真 adaptive**：否。Home 在 1440 仍是宽度 100% 单列（唯一桌面化是 entry 变 4 列）。**违背 Goal §63/§65**。
- **Android 是否像网页套壳**：底部 tabbar 已原生感；但首屏堆叠在 360dp 显得拥挤。
- **Empty/Error/Offline 是否像正式产品**：**是**（70 张截图验证：空态、错误态、离线 banner 均正式）。

### 具体 Gap 清单（M3 关闭）
1. 首屏三组可点项（entry/视角/类别）选择过载 → 收敛为"搜索 + 一个主视角选择"，类别保留为次级。
2. entry 卡与结果卡两套卡语言 → 统一 surface 语言。
3. Rule 结论弱化为小徽标 → 结果行给 Rule 主结论更明确的排版地位（状态标签 + 摘要句）。
4. Reality / Freshness / Evidence 在 Home 缺位 → 结果行加入 Reality 摘要 + freshness/evidence 元数据（来自 snapshot/现有端点，不新增后端）。
5. Desktop hierarchy 缺失 → Home ≥1280 使用内容宽度约束（max-width + 双列或分区）而非拉满。
6. 双重 chrome → 移除旧 AppShell。

---

## 3. Search（标记：`M3-PARTIAL`）

### 当前视觉第一眼
搜索面板 + 最近搜索 pills + lens hint + 档案信息 + 8 筛选 chips + 结果卡 + 桌面右侧 preview。**功能齐全、密度过高**。

### Critique 逐问
- **视觉焦点**：搜索框（正确）；但下方 6 个区块（recent/lens/档案/筛选/结果/preview）连续堆叠。
- **下一步**：清楚（输入→结果）。
- **信息层级**：结果行顺序基本正确（identity→meta→rules→tags），但 **tags 密度高**（已核验/独立携宠区/含服务犬信息/尚未收录规则/conflict 最多 5 个并排）。
- **Rule 状态**：StatusBadge 正确出现。
- **Reality**：桌面 preview 有（PlacePreview 消费 snapshot）✓；**移动端结果行无 Reality 摘要** —— 移动用户看不到"现场最近发生了什么"。
- **Freshness / Evidence**：preview 有 FreshnessStatus/EvidenceMeta ✓；移动端无。
- **Card 是否太多**：搜索面板 + 档案 + lens + 结果行均为 panel → 白卡墙风险中等。
- **Pill 是否太多**：8 筛选 chips + recent pills 高。
- **Desktop 是否真 adaptive**：**是**（唯一 split 页面）✓；但 800px 时 list+preview 并排较挤（已有 VIS-002 修复，需回归保持）。
- **Empty/Error/Offline**：正式 ✓（验证过）。

### 具体 Gap 清单（M3 关闭）
1. 移动端结果行加入 Reality 摘要 + freshness 元数据（与 Home 同组件复用）。
2. 结果行 tags 减负：合并/降级为 1–2 个关键语义标签（如 conflict 单独显式，其余并入 meta 文本）。
3. 筛选 chips 视觉减噪（8 个 → 分组或默认收起次级筛选）。
4. 桌面 preview 保留并打磨（M3 不动其架构）。

---

## 4. Map / Place Passport（标记：`FUTURE-M4`）

- 本轮仅共享层自然影响（Design Token / Primitive / AppShell）。已具备：split view、深链、统一错误、证据视觉语言（M4 报告）。
- 记录后续 Gap：地图真 provider（BLOCKED_EXTERNAL 已有记录）；Passport 10 段结构在 M4 深化时再做信息层级评审。

## 5. Reality Trace / Evidence Viewer（标记：`FUTURE-M5`）

- 已具备 fact/review 分区、观察时间线、统一证据呈现。本轮不重做。
- 记录后续 Gap：Trace 页信息密度与 Evidence 视觉语言可在 M5 深化。

## 6. Contribution Wizard（标记：`FUTURE-M7`）

- 已重建为 7 步状态机。本轮不触碰。
- 记录后续 Gap：M7 深化贡献向导视觉与 completion 态。

## 7. Mine / Settings / Privacy / About（标记：`FINAL`）

- 既有收口完整（M2/M7 报告确认）。本轮不动。

---

## 8. 通用反模式检查（截图实证）

| 反模式 | 现状 | 处置 |
|---|---|---|
| white-card wall | Home 首屏 1+4+N 卡、Search 6 panel | M3 收敛（分区/文本化，减少无意义 panel） |
| pill abuse | Home 3+5+每卡、Search 8 chips + recent | M3 减负 |
| giant radius | 无（10px md）✓ | 保持 |
| heavy shadow | 无 ✓ | 保持 |
| AI gradient | 无 ✓ | 保持 |
| 移动拉伸到桌面 | Home 是（单列拉满）；Search 否 | Home 加桌面 hierarchy |

## 9. 状态标记汇总

| 页面 | 标记 | 理由 |
|---|---|---|
| AppShell | M3-PARTIAL | chrome 职责正确；双重包裹待清 |
| Home | M3-PARTIAL | 结构完整；首屏过载/Reality 缺位/桌面层级待深化 |
| Search | M3-PARTIAL | 深链/状态完整；移动端 Reality 缺位/密度待减 |
| Map | FUTURE-M4 | 共享层自然影响 |
| Place Passport | FUTURE-M4 | 同上 |
| Reality Trace | FUTURE-M5 | 同上 |
| Evidence Viewer | FUTURE-M5 | 同上 |
| Contribution | FUTURE-M7 | 不触碰 |
| Mine/Settings/Privacy | FINAL | 已收口 |
| Runtime issues | 无 | 70 截图 + e2e 全绿；无溢出/无泄漏 |
