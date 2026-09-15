# UI_CORE_CLOSURE_REPORT.md

> 生成时间：2026-09-14（GMT+8）
> 真实基线 HEAD：`53c4c0339ffcaea54b7c4cced46ad7edd28d7bb1`
> 规范依据：`UI_UX_IMPLEMENTATION_SPEC.md`（§2 核心页面 / §5 Boundary / §6 Pet / §7 Contribution / §8 Neutral Copy）
> 前置报告：`UI_UX_IMPLEMENTATION_REPORT.md`、`UI_STATE_MATRIX.md`、`FRONTEND_QA_REPORT.md`

---

## 0. 结论先行

| 优先级 | 项 | 状态 |
|---|---|---|
| **P0-1** | Place Detail 10 Section 补齐 | **DONE** |
| **P0-2** | Map Home 完整交互壳 | **DONE** |
| **P0-3** | Search / Filter | **DONE** |
| **P0-4** | Pet Profile | **DONE**（新建 `PetProfileView.vue`，完整 CRUD） |
| **P0-5** | Boundary Profile | **DONE**（复核并保留，含 spec §5 属性词表） |
| **P0-6** | Contribution / Evidence Upload | **DONE**（真实媒体上传 + OCR 预览，非占位） |
| **P0-7** | Privacy / Data Controls | **DONE**（新建 `PrivacyView.vue`） |
| **P0-8** | PARTIAL / PERMISSION_DENIED / stale / conflict 完整状态 | **DONE** |
| **P0-9** | Published Rule 前端完整呈现 | **DONE** |
| **P1-10** | 通知中心 | **DONE**（新建 `NotificationsView.vue`，诚实标注 Mock 通道） |
| **P1-11** | Settings / About / Methodology | **DONE**（新建 `SettingsView.vue`） |
| **P1-12** | Admin 其余状态完备性 | **PARTIAL**（需真实 DB 端到端，受 ENV-01 阻塞） |
| **P2-13** | 深色主题 | **NOT_STARTED**（按指令排在最后） |

**验证**：ESLint 0 problems · Prettier 全绿 · H5 构建 PASS · Admin 构建 PASS ·
新增离线安全 E2E **7/7 PASS**。

**重要限定**：以下所有"已实现"指**代码路径存在、类型检查与构建通过、且有可运行的 E2E 守卫**。
涉及真实数据渲染的部分（场所列表、规则内容）因 `ENV-01`（无 PostGIS）**未在真实数据上跑通**，
已在 `UI_STATE_MATRIX.md` 与 `FRONTEND_ACCEPTANCE.md` 中一致标注。

---

## 1. P0-1 Place Detail — 10 Section（`apps/client-h5/src/views/PlaceView.vue`）

按 spec §2.4 补齐，模板内显式编号便于对照与回归：

| # | Section | 内容要点 |
|---|---|---|
| 1 | 当前答案 | 一句话结论 + 义务（obligations）+ 来源 + 最近核验时间；未选宠物档案时**显式**说明而非猜测 |
| 2 | 哪里可以 / 不可以 | 按 Zone 分解；每区独立状态 |
| 3 | 条件 | 牵引 / 装载 / 推车 / 不可落地等条件逐条列出 |
| 4 | 共处边界 | 消费 `/places/{id}/extras` 的 `coexistence`（结构化属性，**不作评价**） |
| 5 | 怎么进入 | `entrances` + `access_paths`（入口与路径，含时间窗） |
| 6 | 设施 | `amenities`（饮水 / 拾便袋 / 厕所 / 清洗等） |
| 7 | 来源与时效 | 来源徽标 + 证据强度 + 时效；超 180 天标 `STALE` |
| 8 | 现场记录 | Observation 与规则**并存**展示，明示"现场记录 ≠ 场所正式政策" |
| 9 | 历史版本 | supersession 链与历史版本 |
| 10 | 纠错 / 补充 | 争议提交 + 管理方声明（operator claim）入口 |

补充：`effective-rules` 的 `CONFLICT` / `REVIEW_REQUIRED` / `suppressed` 三种状态均有独立提示块，
并展示被遮蔽规则及原因（不静默丢弃）。

**支撑改动**：新增后端只读端点 `GET /places/{place_id}/extras`（返回 coexistence / amenities /
entrances / access_paths / event_policies），解决 §4/§5/§6 无数据来源的问题。

---

## 2. P0-2 Map Home 完整交互壳（`HomeView.vue` + `components/MockMap.vue`）

| 能力 | 实现 |
|---|---|
| Marker / Cluster 抽象 | `packages/client-core/src/platform/map.ts` 新增 `MapCluster`、`clusterMarkers()`（确定性网格聚类，`unclusterAt=15`） |
| 底图渲染 | `MockMap.vue` 重写为 **provider-neutral** 渲染器：只消费 cluster 列表，不感知腾讯 / Mock |
| Bottom Sheet | `BottomSheet.vue`（新增）：Escape 关闭 + 显式关闭按钮 + 焦点语义 |
| 筛选 | `FilterChips.vue`（新增）+ `STATUS_FILTERS`；提示"信息不足的场所默认仍显示（信息不足 ≠ 允许）" |
| 定位状态 | `LocationState` + `LOCATION_LABELS`（client-core）；一次性定位，**不建立轨迹** |
| 列表 / 地图切换 | `view-map` / `view-list` 双按钮，默认地图 |
| 覆盖度提示 | `coverageHint()` → `data-testid="coverage-hint"`，诚实说明已解析比例 |
| 有界并发 | 状态派生采用有界并发，避免请求风暴 |

**关键设计**：`clusterMarkers()` / `coverageHint()` / `LocationState` 全部放在 `client-core`，
使腾讯地图与 Mock 两条实现路径行为**完全一致**——切换 provider 不改变业务语义。

---

## 3. P0-3 Search / Filter（`SearchView.vue`）

- 搜索 + 附近回退（nearby fallback）
- **8 个筛选器**：明确允许 / 有条件 / 明确限制 / 信息不足 / 来源不一致 / 已核验 / 有独立携宠区 / 含服务犬信息
- 仅在需要时做详情富化（避免 N 次无谓请求）
- **信息不足的场所不被隐藏**（UNKNOWN ≠ prohibited）

---

## 4. P0-4 Pet Profile（`PetProfileView.vue`，新建）

对应 spec §6 字段要求：

| Spec 字段 | 实现 |
|---|---|
| 名称 | 可选（便于区分多档案） |
| species | 犬 / 猫 / 其他 |
| breed | 可选 |
| weight | 留空 ⇒ 相关规则返回"需补充"，**不预填默认值** |
| shoulder height | 留空 ⇒ 保持 UNKNOWN |
| count | 以多档案列表体现（同一用户多条 PetProfile） |
| carrier / stroller | 归入 Boundary Profile（`carrier_required` 等属性），不混入宠物档案 |
| service role | **独立视觉区块**，明示"仅由用户声明，平台不凭照片/品种/体型认定" |

**完整 CRUD**：列表 / 新建 / 编辑（PATCH）/ 删除（带二次确认）/ 设为本次对象。
**状态**：`SkeletonList`（LOADING）· `PERMISSION_DENIED`（未登录，附登录入口）· `EMPTY`（无档案）·
`ERROR`（可重试）· OFFLINE banner（保存暂停）。

**client-core 新增**：`PetIn` / `PetView` 类型、`updatePet()` / `deletePet()`、`myPets()` 改用 `PetView`。

---

## 5. P0-5 Boundary Profile（`BoundaryView.vue`，复核）

已符合 spec §5，本轮复核确认：

- 属性词表覆盖 spec §5 场景：`off_leash` / `designated_area` / `indoor_access` /
  `carrier_required` / `muzzle_required` / `size_limit` / `breed_limit` /
  `peak_hours_restriction` / `dining_together` / `waiting_area`
- 立场词表：可接受 / 希望没有 / 必须禁止（硬性）/ 希望提供
- **不汇总为总分**：逐项判定，页面明示"不是对场所的评分"
- 再次点击可清除 ⇒ 未设置项保持 **UNKNOWN**（不被强制为默认值）
- 服务犬适用独立通行规则，**不在此边界内判断**

---

## 6. P0-6 Contribution / Evidence Upload（`ContributeView.vue`，重写）

按 spec §7 的四个入口重写，且**接入真实媒体上传**（原实现仅有一个不生效的 `<input type="file">`）：

| 入口 | 实现 |
|---|---|
| 快速确认 | "仍然如此 / 已变化 / 不确定" → `verify()`（`event_type=field_check`）；明确告知"不会改变规则内容" |
| 拍规则牌 | `capture="environment"` → **真实** `POST /media/upload`（`purpose=signage_evidence`）→ `GET /media/{id}` 取 **OCR 预览** → 勾选"确认拍摄于本场所" → 提交（`event_type=signage_uploaded`，`evidence_refs=[{media_id}]`） |
| 我知道规则 | 结构化表单（允许 / 限制 / 有条件 + 区域 + 条件）；以"用户陈述"并存展示 |
| 我有现场经历 | Observation 表单（可观察行为 + 工作人员反应 + 确认程度） |

**纪律落实**：
- **无自由评论区**（spec §7 明确要求），只有结构化字段与简短结构化补充
- **OCR 仅为审核预览**，明示"需人工核对"，**不会自动成为规则、不会自动发布**（ADR-005 / ADR-022）
- 提交成功页明确"现场记录 ≠ 场所正式政策"
- 仅发送分桶后的距离 / 精度，**不发送原始 GPS**（ADR-012）
- 上传失败 / 未登录 / 离线均有独立状态；OCR 失败降级为 `PARTIAL` 而非阻断提交

**client-core 新增**：`MediaPurposeKey` / `MediaView` / `MediaMetaView`、
`uploadMedia()`（multipart，唯一直接使用 fetch 的方法，仍复用同一 base URL 与 token）、
`mediaUrl()` / `mediaMeta()` / `deleteMedia()`；
`verify()` / `createObservation()` 类型补全 `zone_id` / `event_type` / `evidence_refs`。

---

## 7. P0-7 Privacy / Data Controls（`PrivacyView.vue`，新建）

| Section | 内容 |
|---|---|
| 数据清单 | 明列采集项与用途 |
| 本机数据 | 本地清除（`data-testid="clear-local"`） |
| 定位 | 说明仅分桶记录、不留轨迹 |
| 账号删除与数据导出 | 提交删除请求；**对"导出"诚实标注为 PARTIAL（尚未实现）**，不伪装成已完成 |
| 数据来源与许可 | 来源与许可说明 |

---

## 8. P0-8 页面状态完备性

所有新页面统一使用 `StateMessage.vue` + `SkeletonList.vue`，状态词表来自
`@petaccess/design-tokens` 的 `PAGE_STATES`（icon + title + description 三者必现，**不靠颜色单独表达**）。

| 状态 | 覆盖位置 |
|---|---|
| `LOADING` | 全部页面（骨架屏） |
| `EMPTY` | Pet Profile（无档案）、Notifications（无订阅）、Home/Search（筛选后为空） |
| `ERROR` | 全部页面（含重试按钮） |
| `OFFLINE` | Home / Boundary / Contribute / Pet Profile / Search（离线**不接受提交**） |
| `PARTIAL` | Place Detail（部分板块缺失）、Contribute 完成页、Privacy（导出未实现）、Notifications（Mock 通道） |
| `STALE` | Place Detail §7（超 180 天未核验） |
| `CONFLICT` | Place Detail（`POTENTIAL_CONFLICT` / `REVIEW_REQUIRED` / `suppressed`） |
| `PERMISSION_DENIED` | Pet Profile / Contribute / Notifications（未登录，附登录入口） |

---

## 9. P0-9 Published Rule 前端完整呈现

`RuleView` 类型扩展 `rule_layer` / `mandatory_level`（ADR-023），前端呈现：

- 规则层级标签：法规 / 监管指引 / 运营方政策 / 临时政策
- 规范力标签：强制 / 建议 / 运营方裁量
- 状态徽标（`StatusBadge`，icon + 文本 + 颜色）
- 时效（`STALE`）、来源、证据强度
- 遮蔽原因、冲突提示、被遮蔽规则明细

---

## 10. P1 项

**P1-10 通知中心**（`NotificationsView.vue`，新建）：展示规则变化订阅列表，支持取消订阅；
**诚实标注通知通道当前为 Mock**，明确"不代表已发送过消息"；未登录时 `PERMISSION_DENIED`。

**P1-11 Settings / About / Methodology**（`SettingsView.vue`，新建）：
- 产品定位（整理 access，不是"友好度"）
- **规则层级**说明（法定要求构成下限，下层不得削弱）
- **证据强度**说明（只描述证据，不改变法律效力）
- **"我们不做的事"**清单（无排名/无评分、不预测是否会遇到宠物、AI 不直接写规则、
  "尚未核验" ≠ 允许或禁止、不记录小区住户、不留轨迹）
- 文案与状态约定、相关页面导航

**P1-12 Admin 状态完备性**：`PARTIAL` — 24 个视图 + 权限门 + 审计已就绪；
Publish / Rollback / Supersession / Evidence Review / Data Quality 的**端到端验证需要真实数据库**，
受 `ENV-01` 阻塞（见 `P0_PUBLISH_CLOSURE_REPORT.md` §2）。

**P2-13 深色主题**：`NOT_STARTED` — 按用户指令排在最后。
设计令牌已按 `color.bg.*` / `color.text.*` / `color.status.*` 组织，具备实现基础。

---

## 11. 导航与路由（本轮接线）

| 路由 | 视图 |
|---|---|
| `/pets` | `PetProfileView`（新增） |
| `/privacy` | `PrivacyView`（新增） |
| `/notifications` | `NotificationsView`（新增） |
| `/settings` | `SettingsView`（新增） |

底部导航调整：**地图 / 搜索 / 宠物 / 我的**（原"贡献"指向 `/pet/new` 属错误指向，已修正；
贡献入口保留在 Place Detail 与 `AppShell` 内）。"我的"页新增通往宠物档案、通知中心、
隐私与数据控制、设置/方法论的入口。

---

## 12. 验证证据（本轮实测）

| 门禁 | 结果 |
|---|---|
| `eslint .` | **PASS** — 0 problems |
| `prettier --check .` | **PASS** — All matched files use Prettier code style |
| H5 `vue-tsc --noEmit && vite build` | **PASS** |
| Admin `vue-tsc --noEmit` + `vite build` | **PASS**（沙箱删除守卫处置见 `P0_PUBLISH_CLOSURE_REPORT.md` §7） |
| Playwright `tests/e2e/h5-shell.spec.ts`（新增，离线安全） | **PASS — 7/7** |
| Playwright `tests/e2e/h5-journey.spec.ts` | **BLOCKED_EXTERNAL** — 7 failed（API :8010 + 种子数据不可用） |
| `tests/unit/test_design_tokens.py`（含禁用语守卫） | **PASS** — 10 passed |

### 新增 E2E 覆盖（`tests/e2e/h5-shell.spec.ts`）

刻意设计为**离线安全**，因此即使 `ENV-01` 阻塞数据库也**可运行、可回归**：

1. Map Home 交互壳（定位状态 / 视图切换 / 地图或显式 ERROR 态，**绝不出现编造的图钉**）
2. Pet Profile 未登录 → `PERMISSION_DENIED` + 登录入口
3. Privacy 数据清单
4. Notifications 诚实标注 Mock 通道
5. Settings 方法论三块（规则层级 / 证据强度 / 不做的事）
6. Boundary 明确"不是对场所的评分"
7. Place Detail 无 API 时降级为显式 ERROR，**不给出猜测结论**

### 同时修正的陈旧断言

`h5-journey.spec.ts` 首个用例原断言首页默认可见"附近场所"标题——
新 IA 默认进入地图视图，该标题仅在切换列表后出现。已改为先断言地图壳、再切列表断言标题，
避免规范与实现长期漂移。

---

## 13. 遗留与技术债（如实登记）

| 项 | 说明 |
|---|---|
| 真实数据渲染未验证 | `ENV-01`（无 PostGIS）⇒ 场所列表 / 规则内容 / 地图图钉未在真实数据上跑通 |
| Admin 端到端未验证 | 同上；Publish / Rollback / Supersession / Evidence Review 需真实 DB |
| 视觉回归截图缺失 | 无法采集（依赖运行中的数据层），已在 `FRONTEND_ACCEPTANCE.md` §5 标注 |
| 深色主题 | `NOT_STARTED`（P2，按指令最后处理） |
| 本轮修复的格式门禁 | `format:check:fe` 在基线 HEAD 上**已为红**（7 个未改动文件即不通过）。本轮已一并修复并登记于 `TECH_DEBT_REGISTER.md` |
