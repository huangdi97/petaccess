# UI_STATE_MATRIX.md

> 每个核心页面的状态完整性矩阵 · 对应 `UI_UX_IMPLEMENTATION_SPEC.md` §5.5 与 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` §5.5
> 图例：✅ 已实现并有守卫 · 🟡 部分实现 · ❌ 未实现 · n/a 不适用
> 基准 commit `716b163`

**重要前提**：数据层（PostGIS）不可用（ENV-01），因此「已实现」指**代码路径存在且构建通过、且有源码级机读守卫**，不指已在真实数据上跑通。视觉回归截图无法采集，见 `FRONTEND_ACCEPTANCE.md` §5。

---

## 0. 状态词汇与共享组件

状态不再由各页面自行编写文案，统一来自 `@petaccess/design-tokens`：

| 词汇 | 条目 | 强制字段 |
|---|---|---|
| `STATUS_SEMANTICS` | ALLOWED / CONDITIONAL / RESTRICTED / UNKNOWN / CONFLICT / STALE | icon + label + ariaLabel + colorVar + bgVar |
| `PAGE_STATES` | LOADING / EMPTY / ERROR / OFFLINE / PARTIAL / STALE / CONFLICT / PERMISSION_DENIED | icon + title + description |

| 组件 | 位置 | 作用 |
|---|---|---|
| `StateMessage.vue` | H5 + Admin | 渲染非 loading 的页面态；`role="status"`，icon + title 必现 |
| `SkeletonList.vue` | H5 | 加载骨架；`aria-busy`，卡片/行两种变体 |
| `.skeleton` / `.skeleton-table` | Admin | 桌面端骨架 |
| `composables/useOnline.ts` | H5 | 在线状态检测；**离线不排队写入** |

机读守卫：`tests/unit/test_ui_states.py`（8 项）与 `tests/unit/test_design_tokens.py`（10 项）。

---

## 1. 消费端（apps/client-h5）

| 页面 | loading | skeleton | empty | success | partial | stale | conflict | error | offline | permission denied |
|---|---|---|---|---|---|---|---|---|---|---|
| 启动 / Onboarding | ✅ | ❌ | n/a | ✅ | n/a | n/a | n/a | 🟡 | ❌ | 🟡 |
| 定位授权 | 🟡 | n/a | n/a | 🟡 | n/a | n/a | n/a | 🟡 | ❌ | 🟡 |
| **地图首页** | ✅ | ✅ | ✅ | ✅ | ❌ | 🟡¹ | 🟡¹ | ✅ | ✅ | ❌ |
| **搜索 / 发现** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Place Card | n/a | ❌ | 🟡 | ✅ | 🟡 | 🟡¹ | 🟡¹ | 🟡 | ❌ | n/a |
| **Place Detail** | ✅ | ✅ | ✅ | ✅ | 🟡 | 🟡¹ | ✅ | ✅ | ❌ | 🟡² |
| Zone 明细 | n/a | n/a | ✅ | ✅ | 🟡 | 🟡¹ | 🟡¹ | ✅ | n/a | n/a |
| **Boundary Profile** | ✅ | ✅ | 🟡 | ✅ | ❌ | n/a | ❌ | ✅ | ✅ | 🟡² |
| Pet Profile | 🟡 | ❌ | ✅ | ✅ | 🟡 | n/a | n/a | ✅ | ❌ | 🟡² |
| Contribution | 🟡 | ❌ | ✅ | ✅ | 🟡 | n/a | n/a | ✅ | ❌ | 🟡² |
| 证据上传 | 🟡 | n/a | 🟡 | 🟡 | 🟡 | n/a | n/a | 🟡 | ❌ | 🟡² |
| Watch / 关注 | 🟡 | n/a | ✅ | ✅ | n/a | n/a | n/a | ✅ | ❌ | 🟡² |
| 纠错 / 异议 | 🟡 | n/a | n/a | ✅ | n/a | n/a | n/a | ✅ | ❌ | 🟡² |
| Match Explain | ✅ | ❌ | ❌ | ✅ | 🟡 | 🟡¹ | ✅ | ✅ | ❌ | ❌ |
| 隐私 / 数据控制 | 🟡 | n/a | 🟡 | 🟡 | n/a | n/a | n/a | 🟡 | ❌ | ❌ |
| 关于 / 数据方法论 | ❌ | n/a | ❌ | ❌ | n/a | n/a | n/a | n/a | n/a | n/a |

¹ 通过 `StatusBadge` 语义呈现（STALE / CONFLICT），非独立页面态。
² 以登录提示形式呈现，非全页态。

**加粗行 = 本轮新接入状态三件套的页面。**

### 已实现的关键状态

| 状态 | 实现 | 位置 |
|---|---|---|
| `UNKNOWN ≠ 允许` | 「暂无已收录规则（信息不足 ≠ 允许）」；徽标「尚未核验」+ aria「不代表允许」 | `PlaceView.vue`、`design-tokens` |
| `CONFLICT` 呈现 | CONFLICT 语义色 + ⚠ + 「来源存在不一致」 | `StatusBadge.vue` |
| `STALE` 呈现 | STALE 语义色 + ⟳ + 「需要复核」 | `StatusBadge.vue`、Admin `RulesView.vue`（逾期规则） |
| 现场记录 ≠ 政策 | 分区标题写明「现场观察（与规则并存，不构成规则）」 | `PlaceView.vue` |
| 离线 | 顶部横幅 + 提交类按钮置灰；**不排队写入** | `useOnline.ts` + 4 个核心页 |
| 空态 | 统一说明「未收录 ≠ 不存在规则」 | `PAGE_STATES.EMPTY` |
| 错误可恢复 | `StateMessage(ERROR)` + [重试] 按钮重新发起请求 | HomeView / SearchView / PlaceView / BoundaryView |
| 权限失败 | 「需要登录后才能核验」类文案，而非静默 | `PlaceView.vue` 等 |

### 明确缺口

1. **PARTIAL 全页态未实现**：`PAGE_STATES.PARTIAL` 已定义但无页面渲染它（部分数据场景目前直接展示可用部分）。
2. **PERMISSION_DENIED 全页态未实现**：目前为内联提示。
3. **地图首页与搜索仍为工具级**：`MockMap.vue` 为静态占位，无 marker clustering、bottom sheet、filter chips、定位、list/map 切换、coverage hint（`UI_UX_IMPLEMENTATION_SPEC` §2.1/§2.2）。依赖真实地图 provider（B-04）与数据层。
4. **Place Detail 未覆盖 §2.4 的 10 个 Section**：现为 4 个（当前答案 / 分区规则 / 来源与核验 / 现场观察）。
5. **无 Place Card 独立组件**：列表场景未抽取。
6. **无纠错/异议独立页**：仅 Place Detail 内一个按钮。
7. **PetNewView / MineView / ContributeView 未接骨架屏**。

---

## 2. Admin 端（apps/admin）

| 页面 | loading | skeleton | empty | success | error | pagination | filter | permission | audit |
|---|---|---|---|---|---|---|---|---|---|
| **Dashboard（数据质量）** | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| Candidate Queue | 🟡 | ❌ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ |
| Evidence Viewer | 🟡 | ❌ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | n/a |
| Review Decision | 🟡 | ❌ | ✅ | ✅ | ✅ | n/a | n/a | ✅ | ✅ |
| Source Monitor | 🟡 | ❌ | ✅ | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ |
| Freshness | 🟡 | ❌ | ✅ | ✅ | 🟡 | 🟡 | 🟡 | ✅ | n/a |
| Organization / Template | 🟡 | ❌ | ✅ | ✅ | 🟡 | 🟡 | n/a | ✅ | ✅ |
| Publish / Rollback | 🟡 | ❌ | n/a | 🟡 | 🟡 | n/a | n/a | ✅ | ✅ |
| **Rules** | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| **Sources** | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| Audit Log | 🟡 | ❌ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | n/a |

**本轮变化**：Dashboard 从「4 项全 ❌」变为完整实现，并新增 3 组真实指标（规则构成与时效 / 候选管线 / 证据完整性）；Rules 与 Sources 接入骨架屏、空态与共享状态徽标。

Admin 具备 24 个视图与 `require_role` 权限门；剩余缺口集中在 **skeleton 统一化**（其余 21 个视图）与 **rollback 的端到端验证**（需数据层）。

---

## 3. 响应式覆盖

| 断点 | 覆盖 |
|---|---|
| mobile portrait | ✅ H5 以 480px 为设计宽度 |
| mobile landscape | 🟡 未针对性优化，`NOT_RUN` |
| tablet | 🟡 布局未重排，`NOT_RUN` |
| desktop H5 | ✅ 居中 480px 容器；`BREAKPOINTS.xl` 已定义 |
| Admin desktop | ✅ 表格布局；`.two-col` 在 900px 以下折叠 |

---

## 4. 判定

```text
UI_FRONTEND_PRODUCTION_GATE = PARTIAL
```

**已达成**：设计令牌单一真源（两端消费，有机读守卫）、状态三通道语义、中性文案守卫、可访问性基线、核心页 loading/skeleton/empty/error/offline 五态、Admin 数据质量看板、两端构建与类型检查通过。

**未达成**：视觉回归截图基线、地图交互壳、Place Detail 全 Section、PARTIAL 与 PERMISSION_DENIED 全页态、多断点与真机 QA、暗色主题、uni-app x 端接入。

未达成项中，**地图交互壳与视觉回归依赖数据层与地图 provider（ENV-01 / B-04）**；其余（PARTIAL 全页态、Place Detail 补齐、暗色主题、其余视图骨架屏）为**可立即实施**的工程项。
