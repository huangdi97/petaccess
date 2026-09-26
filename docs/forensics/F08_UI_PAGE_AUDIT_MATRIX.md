# F08 UI PAGE AUDIT MATRIX（本轮实测 + 既有验收证据交叉核验）

> 评级依据：本 Goal 代码阅读（template/script/style 抽查）、h5-shell/backend-down E2E（本轮 5 spec 实测）、矩阵 Android 实机渲染（F03）、M2–M8 报告验收（HISTORICAL 但已在本轮以构建+运行复验）。
> 评级：PASS / PASS_WITH_DEBT / FAIL（FAIL=0）。

| 页面 | template/script/style | data source | loading | empty | error | offline | routing | a11y | responsive | 结果 |
|---|---|---|---|---|---|---|---|---|---|---|
| Home | 已通读 | client.nearby→enrich（bounded 4 并发，失败→UNKNOWN） | SkeletonList（loading 必收敛） | Rule 待核实空态（无数据可渲染） | StateMessage + presentDescription | AppShell 级 GlobalOfflineBanner + 离线 banner | `/`（hash） | label/visually-hidden/aria-pressed 实测（h5-shell spec） | 旧代 AppShell 内框（FF-003） | **PASS_WITH_DEBT**（FF-003 legacy 组件；其余 PASS，含本轮 backend-down E2E 无 uncaught） |
| Search | M3/M4 重构（SearchView 544L），split-view 桌面化 | 统一 CoexistenceSnapshot 消费（commit e7ecf08） | Search skeleton（loading/） | 空结果态 | 统一错误（errors.ts 六类） | 全局 banner | `/search` | 验收覆盖（M3/M8） | 1280/1440/1920 + 360/390/430 | **PASS** |
| Map | MapView 455L + split-view/深链/状态收口（M4） | mapConfig 等 | MapLoadingOverlay | 空态 | 统一错误 | 全局 banner | `/map` | M4 验收 | split-view 桌面/移动 tab | **PASS_WITH_DEBT**（M4 记录 BLOCKED_EXTERNAL：外部地图 provider 依赖；本仓 FEATURE_REAL_MAP=false 时为 shell） |
| Place | PlaceView 826L（>300 warn，FF-006）| placeDetail + zones + coexistSnapshot 聚合 | PlaceSkeleton | 空态组件 | 统一错误 | 全局 banner | `/place/:id` | M3/M4 验收 | 阅读列/证据语言（M4） | **PASS_WITH_DEBT**（文件规模 FF-006；行为 PASS） |
| Contribution | ContributeView+Wizard（M7 重建）| createRealityReport 等（REVIEW_PENDING 落地） | 表单交互相关 | 无场所引导选择 | 统一错误 | 全局 banner | `/contribute/:id?` | M7 验收（a11y 标题层级） | 表单组件 >150L（FF-007 warn） | **PASS_WITH_DEBT**（FF-007） |
| Evidence | EvidenceMeta/EvidenceStatus 域组件 | reality/evidence 端点 | EvidenceSkeleton | 空态 | 统一错误 | 全局 banner | 页面内面板 | 域组件统一标签 | 适应 | **PASS** |
| Reality Trace | RealityTraceView（M5）+ fact/review 分离 | realityTrace 端点 | skeleton | 空态 | 统一错误 | 全局 banner | `/reality-trace`（独立深链 per M5） | M5 验收（a11y 快照绿） | 适应 | **PASS** |
| Rule Trace | 规则溯源（answer→why 深链） | access-answer 证据链 | skeleton | 空态 | 统一错误 | 全局 banner | `/match-explain` | 无堆绿色墙（§12 已改） | 适应 | **PASS** |
| Settings | SettingsView + About/Privacy/Mine/Notifications | 本地+账户 | 表单态 | — | 统一错误 | 全局 banner | `/settings` 等 | shell-spec e2e 覆盖（h5-shell） | 360/390/430+桌面 | **PASS** |
| About/Mine/Privacy/Notifications | 子页面（shell-spec 覆盖） | 本地/会话 | — | — | 统一错误 | 全局 banner | 各自路由 | e2e 覆盖 | 适应 | **PASS** |
| Error | AppBoundary（onErrorCaptured→六类呈现，reload/retryBoot） | — | — | — | 错误面板（无裸 stack） | — | 全路由 | role 标注 | 适应 | **PASS**（代码通读 + backend-down e2e） |
| Offline | GlobalOfflineBanner + useOnline + reconnect 事件抖动 | navigator.onLine | — | — | — | banner v-if !online（z-index token） | 全路由 | role=status | 适应 | **PASS**（代码通读 + e2e） |

## Console Runtime Gate（§33，本轮实测）

`endpoint-resolution.spec`（4/4）+ `backend-down-home.spec`（1/1）共 5 tests 全部通过：/api 全中断时 AppShell+Home 渲染、**0 未处理 JS 错误**（仅浏览器资源失败日志被排除——见 spec 内注释）。

## 结论

- FAIL = 0；CRITICAL/HIGH UI 级问题 = 0
- 遗留（tracked）：FF-003（HomeView 旧代组件）、FF-004/FF-006/FF-007（规模/复杂度 warn）
- F08 = PASS_WITH_TRACKED_DEBT