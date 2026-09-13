# UI_STATE_MATRIX.md

> 每个核心页面的状态完整性矩阵 · 对应 `UI_UX_IMPLEMENTATION_SPEC.md` §5.5 与 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` P3 §5.5
> 图例：✅ 已实现并验证 · 🟡 部分实现 · ❌ 未实现（需数据层或后续阶段）

**重要前提**：本轮数据层（PostGIS）不可用（ENV-01），因此「已实现」指**代码路径存在且构建通过**，不指已在真实数据上跑通。

---

## 1. 消费端（apps/client-h5）

| 页面 | loading | skeleton | empty | success | partial | stale | conflict | error | offline | permission denied |
|---|---|---|---|---|---|---|---|---|---|---|
| 启动 / Onboarding | ✅ | ❌ | n/a | ✅ | n/a | n/a | n/a | 🟡 | ❌ | 🟡 |
| 定位授权 | 🟡 | n/a | n/a | 🟡 | n/a | n/a | n/a | 🟡 | ❌ | 🟡 |
| 地图首页 | 🟡 | ❌ | 🟡 | ✅ | 🟡 | ❌ | ❌ | 🟡 | ❌ | ❌ |
| 搜索 / 发现 | 🟡 | ❌ | ✅ | ✅ | 🟡 | ❌ | ❌ | 🟡 | ❌ | ❌ |
| Place Card | n/a | ❌ | 🟡 | ✅ | 🟡 | ❌ | ❌ | 🟡 | ❌ | n/a |
| Place Detail | 🟡 | ❌ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ❌ | n/a |
| Zone 明细 | n/a | n/a | ✅ | ✅ | 🟡 | 🟡 | 🟡 | ✅ | n/a | n/a |
| Boundary Profile | 🟡 | ❌ | ✅ | ✅ | 🟡 | n/a | 🟡 | 🟡 | ❌ | ❌ |
| Pet Profile | 🟡 | ❌ | ✅ | ✅ | 🟡 | n/a | n/a | 🟡 | ❌ | ❌ |
| Contribution | 🟡 | ❌ | ✅ | ✅ | 🟡 | n/a | n/a | ✅ | ❌ | 🟡 |
| 证据上传 | 🟡 | n/a | 🟡 | 🟡 | 🟡 | n/a | n/a | 🟡 | ❌ | 🟡 |
| Watch / 关注 | 🟡 | n/a | ✅ | ✅ | n/a | n/a | n/a | ✅ | ❌ | 🟡 |
| 纠错 / 异议 | 🟡 | n/a | n/a | ✅ | n/a | n/a | n/a | ✅ | ❌ | 🟡 |
| 隐私 / 数据控制 | 🟡 | n/a | 🟡 | 🟡 | n/a | n/a | n/a | 🟡 | ❌ | ❌ |
| 关于 / 数据方法论 | ❌ | n/a | ❌ | ❌ | n/a | n/a | n/a | n/a | n/a | n/a |

### 已实现的关键状态（本轮）

| 状态 | 实现 | 位置 |
|---|---|---|
| `UNKNOWN ≠ 允许` | 明示「暂无已收录规则（信息不足 ≠ 允许）」；状态徽标文案「尚未核验」+ aria「不代表允许」 | `PlaceView.vue`、`design-tokens/src/index.ts` |
| `CONFLICT` 呈现 | `CONFLICT` 语义色 + ⚠ 图标 + 「来源存在不一致」 | `StatusBadge.vue` |
| `STALE` 呈现 | `STALE` 语义色 + ⟳ 图标 + 「需要复核」 | `design-tokens` |
| 现场记录 ≠ 政策 | 分区标题即写明「现场观察（与规则并存，不构成规则）」，页脚另有免责声明 | `PlaceView.vue` |
| 权限失败 | 关注/核验/异议失败时给出「需要登录后才能核验」类文案，而非静默 | `PlaceView.vue` |
| 错误 | `error` ref 渲染为 panel 文本 | `PlaceView.vue` |

### 明确缺口

1. **skeleton 全缺**：无骨架屏实现。
2. **offline 全缺**：无网络状态检测与离线提示。
3. **地图首页与搜索为工具级**：`MockMap.vue` 为静态占位，无 marker clustering、无 bottom sheet、无 filter chips、无定位、无 list/map 切换、无 data coverage hint（`UI_UX_IMPLEMENTATION_SPEC` §2.1/§2.2 要求）。这需要真实地图 provider（B-04）与数据层。
4. **Place Detail 未覆盖 §2.4 的 10 个 Section**：现为 4 个板块（当前答案 / 分区规则 / 来源与核验 / 现场观察），缺条件、共处边界、进入方式、设施、版本历史等 Section。
5. **无 Place Card 独立组件**：列表场景未实现。
6. **无纠错/异议独立页**：仅 Place Detail 内一个按钮。

---

## 2. Admin 端（apps/admin）

| 页面 | loading | empty | success | error | pagination | filter | sort | permission | audit |
|---|---|---|---|---|---|---|---|---|---|
| Dashboard | 🟡 | 🟡 | ✅ | 🟡 | n/a | n/a | n/a | ✅ | n/a |
| Candidate Queue | 🟡 | ✅ | ✅ | ✅ | 🟡 | ✅ | 🟡 | ✅ | ✅ |
| Evidence Viewer | 🟡 | ✅ | ✅ | ✅ | 🟡 | ✅ | 🟡 | ✅ | n/a |
| Review Decision | 🟡 | ✅ | ✅ | ✅ | n/a | n/a | n/a | ✅ | ✅ |
| Source Monitor | 🟡 | ✅ | ✅ | ✅ | 🟡 | 🟡 | n/a | ✅ | ✅ |
| Freshness | 🟡 | ✅ | ✅ | 🟡 | 🟡 | 🟡 | n/a | ✅ | n/a |
| Organization / Template | 🟡 | ✅ | ✅ | 🟡 | 🟡 | n/a | n/a | ✅ | ✅ |
| Publish / Rollback | 🟡 | n/a | 🟡 | 🟡 | n/a | n/a | n/a | ✅ | ✅ |
| Audit Log | 🟡 | ✅ | ✅ | 🟡 | ✅ | ✅ | 🟡 | ✅ | n/a |
| Data Quality | ❌ | ❌ | ❌ | ❌ | n/a | n/a | n/a | n/a | n/a |

Admin 具备 24 个视图与 `require_role` 权限门；缺口集中在 **skeleton/loading 统一化**、**Data Quality 面板**、**rollback 的端到端验证**（需数据层）。

---

## 3. 响应式覆盖

| 断点 | 覆盖 |
|---|---|
| mobile portrait | ✅ H5 以 480px 为设计宽度 |
| mobile landscape | 🟡 未针对性优化 |
| tablet | 🟡 布局未重排 |
| desktop H5 | 🟡 居中 480px 容器，未利用宽屏 |
| Admin desktop | ✅ 表格布局 |

---

## 4. 判定

```text
UI_FRONTEND_PRODUCTION_GATE = PARTIAL
```

已达成：设计令牌体系、状态三通道语义、中性文案守卫、可访问性基线、H5 与 Admin 构建通过。
未达成：骨架屏、离线态、真实地图交互壳、Place Detail 全 Section、视觉回归截图基线。

未达成项中，**地图交互壳与视觉回归依赖数据层与地图 provider（ENV-01 / B-04）**；其余为可继续实现的工程项。
