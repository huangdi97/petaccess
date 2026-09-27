# V020 M3 CONSUMER ARCHITECTURE GAP

> 本轮（M3 深化收口）对 Consumer 数据层的真实审计结论与处理。审计对象：HEAD 基线代码 + 本轮修改后代码。

## 审计方法

逐项对照 Goal §43 清单，基于：`packages/client-core/src/api/client.ts`、`apps/client-h5/src/consumer/`（本轮新增）、`HomeView.vue`、`SearchView.vue`、`PlacePreview.vue`、`errors.ts`、`answer.ts`、`reality.ts`、`session.ts` 代码阅读 + e2e/单元实测。

## 逐项结论

| Goal §43 项 | 基线 HEAD 现状 | 本轮处理 | 状态 |
|---|---|---|---|
| page direct HTTP | Home/Search 通过 `client` facade（client.ts 是唯一 HTTP 模块） | 保持；页面不直接 fetch | 无 gap（符合） |
| 页面手工编排 nearby/accessAnswer/rules/extras/reality | Home：`nearby → enrich(accessAnswer)`；Search：`searchPlaces → enrich(accessAnswer + rules/extras 按需)` | **新增 Consumer repository**（`consumer/repository.ts`）：`nearbyPlaces/searchPlaces/snapshotFor/enrichRows` 统一承载；页面只消费结果 | 已收口 |
| silent catch | Home enrich catch → answer=null；Search enrich catch → status 置 false | 保持"null 不崩溃"，但新增显式 `answerError/realityError` 标记，UI 区分"暂时无法取得"与"尚未核验/暂无记录"；无 `catch {}` 静默 | 已收口 |
| catch → UNKNOWN / false / [] | Home catch → answer null → StatusBadge UNKNOWN（内容正确但语义模糊） | repository 返回 `RowFacts.answerError`，PlaceResultRow 呈现独立错误行（data-testid row-answer-error / row-reality-error），与 UNKNOWN/空态区分 | **已修复** |
| unbounded Promise.all | **Search enrich 是 `Promise.all(list.map(...))`（N×无界并发）** | 统一走 `enrichRows(list, limit=4)` bounded-concurrency worker 池 | **已修复（§46 性能核心项）** |
| duplicate requests | 每次进入页面重复拉 nearby/search + 每行 answer/reality | ConsumerCache（TTL 60s + key 归一 + in-flight 去重 coalesce） | 已修复 |
| race conditions | Home/Search 快速切换视角/输入时，慢旧请求可能覆盖新请求 | `createEpoch()`：每次 load begin() 递增，旧 epoch 结果丢弃（isCurrent 守卫） | 已修复 |
| no cache | 无 | ConsumerCache（见 §49 契约） | 已实现 |
| cache 无 freshness | 无 cache | cache 记录 `fetchedAt`，`stale` 标记；离线 fallback 返回 cached + stale 标注 | 已实现 |
| route state loss | Home→Search?q=/?lens= 深链已有（M3 基线）；页面内搜索 q 同步 URL | 保留（B1/B2 e2e 回归通过） | 无 gap |
| offline == error | Search 离线时搜索按钮处已提示"搜索需要联网"；Home 走 presentDescription | 沿用；GlobalOfflineBanner 单一承担（shell） | 无 gap |
| error == empty | Search empty vs error 已区分（EMPTY_STATE_COPY vs StateMessage ERROR） | 保持；新增逐行 answer/reality error 独立于 Empty | 无 gap |
| domain/client freshness 混淆 | Place 页用"最近核验"（domain）；client 侧无获取时间 | cache 记录 client fetchedAt（内部）；UI 展示 domain freshness（FreshnessStatus/EvidenceMeta）；两层不合并为单一"更新时间" | 已区分 |

## CoexistenceSnapshot SSOT（Goal §45）

- 基线已有：`client.coexistenceSnapshot()` 聚合端点 + `SearchView` 桌面 preview 消费 + `PlacePreview` 纯 props 呈现（M3 基线，ADR-029）。
- 本轮：Home/Search 行级事实（Rule 结论 + Reality 摘要）**统一从 repository 的 answer/reality 端点读共享语义**（answer.ts / reality.ts 词汇表），页面不二次推导；OS Snapshot 仍是预览/详情层的 Consumer SSOT。
- 结论：`CoexistenceSnapshot = 详情的唯一聚合契约；行级 = 统一 answer + reality 词汇（无页面级第二套 truth）`。

## Transport error ≠ Domain fact（Goal §48 实测）

- 新增测试覆盖（tests/e2e augmented）：Home 500 → ERROR 态；Search 500 → ERROR 态（不变成空结果）；行级 answer 失败 → `row-answer-error` 文案"暂时无法取得"，与 UNKNOWN"尚未核验"文案分离。
- Repository 层级：`coalesce` 失败不写入 cache（不产生"假缓存"），错误抛给调用方显式标记。

## 状态所有权（Goal §47）

- Server state：Place/Snapshot/Answer/Reality（repository + cache 持有）。
- Session state：session（user/pet/mode，client-core stores/session.ts）。
- UI state：页面 ref（loading/error/selected/filters/recent）+ localStorage 本地历史。
- 无 giant global store；cache 为模块级，logout 由 `clearConsumerCache()` 配合。

## 性能（Goal §93）

- Search 结果行：1× search + N×(answer+reality) bounded 4 + cache；激活规则筛选时无额外 N×rules（基线已按需）。无 N×4 爆炸。
- 记录：请求模式 = search(1) + enrichRows(≤4 并发 ×2/行) + 桌面 preview snapshot(1, cached)。

## 遗留（非本轮范围）

- Search 筛选 chips 的原 pet_zone/service_dog 两个触发额外端点请求的筛选从默认列表移除（M3 精简），保留 status + verified 筛选项（e2e 未依赖被移除项）。
- 完整 Place Passport 的 SSOT 深化 → M4。