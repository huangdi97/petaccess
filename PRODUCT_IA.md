# PRODUCT_IA.md

> 宠物准入与公共空间共处规则平台 · 产品信息架构
> 对应 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` §4.1 / §4.2 / §4.11
> 基准 commit `716b163` · 生成时间 2026-09-14（GMT+8）

---

## 1. 产品定位对 IA 的约束

IA 由三条红线反推，而不是由"宠物社区"的惯例反推：

| 红线 | 对 IA 的强制约束 |
|---|---|
| Access，不是 Friendly | 一级对象是**场所的准入规则**，不是"宠物友好度" |
| UNKNOWN ≠ allowed | 必须有一等公民的"尚未核验"呈现位，不能被折叠进"允许" |
| AI ≠ final rule judge | 所有规则展示必须能一键回溯到**来源与核验时间**；推断过程可展开 |

因此导航不使用"推荐/榜单/评分"结构，只使用"查询 → 查看规则 → 看依据 → 贡献"这条证据链。

---

## 2. 一级用户任务（Master Goal §4.1）

| 代号 | 用户问题 | 主入口 | 关键页面 |
|---|---|---|---|
| **A 带宠查询** | "我的宠物能不能去？" | 地图 / 搜索 | 地图首页 → Place Detail → 为什么是这个结果 |
| **B 空间边界查询** | "这里普通宠物能到哪里、做到什么程度？" | 地图首页模式切换 → 分区域规则 | Place Detail §2 哪里可以/不可以 + 共处边界 |
| **C 直接看规则** | "这个地方现在怎么规定？" | 搜索直达 | Place Detail §3 条件 / §7 来源 / §9 历史 |

三类任务共用同一个详情页，但**入口与默认展开区不同**：A 默认展开"当前答案"（结合我的 PetProfile），C 默认展开"规则与来源"。这是刻意的——同一事实，不同问题的读法不同。

---

## 3. 主导航（Master Goal §4.2）

采用规范推荐的 4 Tab 结构，已实现于 `apps/client-h5/src/App.vue`：

```text
地图 | 搜索 | 贡献 | 我的
```

**UX rationale（规范允许保留既有 IA，但要求给出理由）**

1. **"地图"与"搜索"并列而非合并**：地图服务"我附近有什么"（空间探索，答案随位置变化）；搜索服务"我知道名字，查一下"（目标导向，答案不随位置变化）。合并会迫使其中一类用户多走一步。
2. **"贡献"独立成 Tab**：贡献是证据链的入口而非社交行为，必须在拇指热区常驻，否则数据补充率会显著下降。
3. **"我的"承载档案与隐私**：PetProfile / BoundaryProfile / 关注 / 隐私控制集中在此，避免设置项散落在各页。
4. **不设"榜单/发现"Tab**：与"不做红黑榜、不做遇宠率"的红线直接冲突。

---

## 4. 页面清单

### 4.1 Consumer（H5，已实现）

| 路由 | 名称 | 页面 | 状态 |
|---|---|---|---|
| `/` | home | 地图首页（Mock 地图壳 + 附近场所列表） | ✅ |
| `/onboarding` | onboarding | 首次使用说明 | ✅ |
| `/search` | search | 搜索 | ✅ |
| `/place/:id` | place | Place Detail（当前答案 / 分区规则 / 来源与核验 / 现场观察 / 操作） | 🟡 4/10 Section |
| `/place/:id/why` | match-explain | 为什么是这个结果（可解释推导 / 被抑制规则 / 未解冲突 / 边界比对） | ✅ |
| `/pet/new` | pet-new | 新建宠物档案（含 AI 建议，需用户确认） | ✅ |
| `/contribute/:id` | contribute | 现场贡献 | ✅ |
| `/mine` | mine | 我的（档案 / 关注 / 边界 / 隐私） | ✅ |
| `/boundary` | boundary | 共处边界设置 | ✅ |

### 4.2 Operator（未单独建站）

规范为条件式（"若 B 端单独 Web"）。当前**未单独建 Operator 站点**，管理方能力通过 Admin 的认领（Claims）与组织（Organizations）承载。若后续需要独立 B 端，见 §6 缺口。

### 4.3 Admin（`apps/admin`，24 视图）

| 分组 | 视图 |
|---|---|
| 数据质量 | Dashboard（数据质量看板） |
| 规则域 | Places / PlaceDetail / Rules / Sources / Regulations / RuleCandidates / Conflicts |
| 证据域 | Evidence / SourceMonitors / AiQueue |
| 贡献域 | Observations / ObservationCandidates / Claims / Disputes |
| 治理域 | Organizations / SpatialExtras / EventRules / MatchDebugger |
| 系统域 | Users / Audit |

---

## 5. 页面 → 状态矩阵

每个核心页面必须具备的 10 个状态，逐页对应关系见 `UI_STATE_MATRIX.md`。本轮已补齐的公共状态组件：

- `StateMessage.vue`（H5 + Admin）：EMPTY / ERROR / OFFLINE / PARTIAL / STALE / CONFLICT / PERMISSION_DENIED
- `SkeletonList.vue`（H5）/ `.skeleton`（Admin）：LOADING
- `composables/useOnline.ts`（H5）：离线检测

状态文案统一来自 `@petaccess/design-tokens` 的 `PAGE_STATES`，不由各页面自行编写，避免同一状态在不同页面措辞漂移。

---

## 6. 未实现 / 缺口（诚实记录）

| # | 缺口 | 阻塞源 | 说明 |
|---|---|---|---|
| 1 | 地图首页交互壳：marker clustering / bottom sheet / filter chips / 定位 / list-map 切换 / coverage hint | 地图 provider（B-04）+ 数据层（ENV-01） | 当前为 Mock 地图壳，可交互但无真实瓦片与聚合 |
| 2 | Place Detail 的 10 个 Section 仅实现 4 个 | 部分依赖后端字段接线（Zone/Amenity/Entrance/AccessPath 表已存在） | 缺 §2 完整分区/楼层、§4 共处边界、§5 怎么进入、§6 设施、§9 历史、§10 纠错入口 |
| 3 | 搜索筛选 chips（明确允许/有条件/明确限制/已核验/最近核验/独立宠物区/仅户外/推车/服务犬/冲突） | 数据层 | 规范 §2.2 要求，UI 可建但无数据可筛 |
| 4 | Operator 独立站点（claim status / basic policy / zone policy / temporary policy / amenities / entrances / access paths / preview / publish / version / disputes） | 产品决策 + 数据层 | 当前由 Admin 承载 |
| 5 | 通知中心页 / 设置页 / 关于与数据方法页 | 可实施 | 规范 §5.4 列出，尚未建页 |
| 6 | 隐私设置页 / 账号删除 / 数据导出 UI | 可实施（后端亦缺） | 见 `FINAL_PRODUCTION_READINESS_REPORT.md` §9 |

**未收录 ≠ 不存在规则**：所有空态文案均显式说明这一点（见 `COPY_GUIDE.md`），这是 IA 层面的硬约束，不是文案偏好。
