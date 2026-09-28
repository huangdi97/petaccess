# Visual Fidelity Recovery — Design Contract (Phase A: Search + Place)

> 契约来源：`PetAccess_v0.2.1_Visual_Fidelity_Recovery_Local_Only_GOAL_2026-09-28.md` §32–§36
> 设计权威：`UI_RECONSTRUCTION_DESIGN_FREEZE.md`（v0.10-R1 Canonical + Approved Reference）→ 本契约只做实现解释，不重定义产品语义。
> 人工视觉失败证据：Goal §3.1（Search）/ §3.2（Place），本契约逐项关闭。

## 1. 产品感觉（冻结）

> 一个可信、冷静、空间化的城市动物准入事实工具。
> 不是数据库 schema viewer、不是 QA 工具、不是组件 demo、不是宠物友好地图。

## 2. Search Desktop — 设计解释

### 2.1 Result Row 信息预算（每行严格六项）

```text
Place identity          ← 名称（lg→xl，medium）
Type · distance         ← 类型 · 距离（muted，13–14）
Primary decision        ← 大结论行：可以进入/不可进入/有条件进入/信息不足（lg，medium）
1 key condition         ← 最重要的一个条件（muted，有则显示，无则不显示）
Recent reality          ← realityLine + evidenceLine（13–14）
（极轻元数据）           ← ruleSummaryLabel 一行小字（13，可含「生效规则」）
```

**禁止显示（同时）**：verification type（已核验前缀）、生效规则条数作为主信息、内部 source 计数、匹配机制（别名/父场所）抢视觉、重复的 scope、重复条件。

- `已核验：` 前缀 → 删除；结论行直接是判定词。
- `条件：{{ scope }}` 重复行 → 删除（它重复了 scope 而非条件）。
- `result-alias`（以「…」匹配）→ 删除（机制语言，无决策价值）。
- `result-branch`（所属 …）→ 保留但降为极轻 metadata（仅桌面可见，移动隐藏）。
- `result-rules`（生效规则 N 条 · 时间）→ 保留文案（测试契约要求含「生效规则」「尚未收录规则」），降为 13px 极轻元数据行。

### 2.2 Selected 态

- subtle tint（`--pa-color-accent-weak`）+ 1 个明确指示（左侧 2px accent bar）。
- 不 rounded card、不重边框。

### 2.3 Decision Inspector（不是 label/value 表）

层级（自上而下）：

```text
Identity           ← 名称（2xl→3xl）+ StatusBadge
Meta               ← type · address
──────────────────
Current Context    ← 当前查询：普通犬 · 进入 · 公共区域（muted 小行）
Primary Decision   ← 大结论（26px desktop / 22px mobile，medium）
                    适用范围（secondary 一行）
Conditions         ← 条件列表（✓ 前缀行；空则不显示）
Major Exception    ← 差异/例外（divergence，有则显示）
Recent Reality     ← 近期现场一行 + 依据提示（13–14）
Source/Freshness   ← 时效 / freshness（13–14 muted）
──────────────────
Open Full Dossier  ← primary 按钮
```

禁止：`<dl>` label/value 平铺表、把整个 dossier 复制进 inspector、右对齐值列。

## 3. Search Mobile — 设计解释

- 单条结果 ≤4 个视觉行组：名称+状态 / 类型·距离 / 大结论（+1 条件，条件与结论合并一组）/ reality·evidence。
- 不显示「生效规则 N 条」、不显示验证机制、不显示父场所/别名。
- Filter：`筛选 N` 按钮 → **bottom sheet**（移动端）；不再铺 chips。
- 点击结果 → 进入 Place；QueryContext 保持轻量 sticky。

## 4. Place Desktop — 设计解释

### 4.1 Main Dossier 顺序（自上而下）

```text
1. Identity          ← h1 名称（4xl→30px），type · address · distance；关注/为什么按钮行
2. Current Query + Decision   ← 当前查询 + 我的结论（大结论 + 基线并列，不折叠）
3. Recent Reality    ← RealityPanel（flat section，非卡片）
4. Space / Zones     ← 消费者名称行：公共区域/堂食区/户外区 + 各自状态（查看→展开单区结论）
5. Rules + Conditions← 当前规则 + 条件（只显示与当前 context 高相关）
6. Evidence / Provenance ← 来源 + 证据状态 + provenance 语句
7. Staff / Facilities← 共处边界 + 入口/设施（独立事实，不混入 Policy）
8. History / Correction ← 历史版本 + 纠错（下沉，移动端默认折叠）
```

### 4.2 Sticky Decision Inspector

固定 5 个主要块（与 Search 共享组件）：
`Current Context / Primary Decision / Required Conditions / Major Exception / Source·Verified·Freshness`。
**不得复制整个 dossier。**

### 4.3 消费者语言（raw enum → label，全部走统一 mapper）

| 原始值 | 消费者显示 |
|---|---|
| `dining_area` / `pet_area` / `area` 等 zone_type | 堂食区 / 携宠区 / 公共区域 |
| `floor` / `B1` 等 floor_ref | 楼层：B1（不裸显 `floor`） |
| `ordinary_pet` / `service_dog` / `dog` | 普通宠物 / 服务犬 / 犬 |
| `enter` / `stay` 等 action | 进入 / 停留 |
| `superseded` / `withdrawn` 等 status | 已被取代（历史）/ 已撤回 |
| `explicitly_allowed` 等 staff_action | 明确允许 / 未观察到干预 |
| `entered` / `present` 等 observed_action | 进入 / 在场 |
| `active` / `removed` 等 facility 状态 | 正常使用中 / 已移除 |
| `allowed` / `prohibited` 等 coexistence value | 允许 / 禁止 |
| `uuid-slice`（`来源 + id.slice(0,8)`） | `来源信息暂不可用`（禁止任何 UUID 片段可见） |

## 5. Typography Gate（§36 落地）

- tokens.css 新增：`--pa-font-size-14`（metadata/evidence）、`--pa-font-size-17/18/19`（section）、`--pa-font-size-22`（decision mobile）、`--pa-font-size-26`（decision desktop）、`--pa-font-size-30`（page identity desktop）。
- 页面不得 invent 数值；一律引用 token。
- 放不下 → 删次要信息 / progressive disclosure，不缩字号。

## 6. 禁止项（Phase A 不破）

- 不引入新依赖、新字体、新 icon pack、新 UI framework。
- 不重定义 Rule/Reality 语义、不重写 evaluator/repository。
- 保持所有 data-testid（`search-input/btn/clear/filter-toggle/result-*/result-branch/result-rules/result-reality/row-answer-error/row-rule/decision-inspector/inspector-verdict/inspector-divergence/inspector-freshness/inspector-open/section-answer/answer/answer-status/answer-conditions/answer-missing-inputs/answer-scope/answer-boundary/answer-provenance/query-context/reality-panel/open-reality-trace/zone-toggle-*`）不变。
- 每页单一 h1；状态 icon+文字+颜色；触控目标 ≥44px；reduced-motion 保留。
