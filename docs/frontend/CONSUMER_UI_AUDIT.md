# Consumer UI Audit（H5）

> 逐页对照规范 §40–§53、§60–§62。判定基于**源码与 E2E 实况**，不是设计稿。

## 总览

| 页面 | 判定 | 关键依据 |
|---|---|---|
| HOME | PASS | Search-first；`home-title` / `home-search-input` / `附近已核验` / 「规则待核实」均在 E2E 断言内 |
| SEARCH | PASS | 模糊名搜索有 E2E 覆盖；空态、错误态由 `PAGE_STATES` 提供 |
| MAP | PASS_WITH_LIMITATIONS | 覆盖提示、列表/地图切换、定位拒绝态齐备；**地图为 MockMap（无真实 SDK）** |
| PLACE_DETAIL | PASS | canonical 10 段齐全，状态在地址/营业时间之前 |
| RULE_TRACE | PASS | 「为什么是这个结果」独立页：附加条件 / 推导过程 / 被抑制规则 / 未解冲突 |
| EVIDENCE_UI | PASS | §7 来源与时效 + §8 现场记录分离，且明示「现场记录 ≠ 场所正式政策」 |
| CONDITIONS_UI | PASS | §3 条件 与 §6 设施 是两个独立段落，未混为「宠物设施」 |
| UNKNOWN_STATE | PASS | UNKNOWN 文案含「不代表允许」；E2E 有「degrades to an explicit error state, never a guessed verdict」 |
| CONTRIBUTION | PASS | 4 个入口（快速确认 / 拍规则牌 / 我知道规则 / 现场经历）；无场所时先要求选场所 |
| PROFILE | PASS | PetProfile 为工具属性；BoundaryProfile 用接受/不接受/不在意，无百分比匹配分 |

## 逐页细节

### Home（§40）

- 搜索框为第一交互（`home-search-input`），地图在独立 Tab——**未回退为 Map-first**。
- 三种视角 Lens：看场所规则（默认）/ 携带动物 / 共处偏好。
- 分类 chips：全部 / 公园 / 商场 / 餐饮 / 酒店（基于已加载的附近集合，不额外发请求）。
- 「最近查看」本地持久化（`pa.recent.v1`，上限 3），有才显示。
- 「规则待核实」区块显式存在——**没有为了好看隐藏 UNKNOWN**。
- 贡献入口在页脚低优先级（`HomeView.vue:416`）：「AI/OCR 只生成待审候选，不会自动成为规则」。

### Search（§41）

- 模糊名匹配有 E2E（`search finds place by fuzzy name`）。
- 状态：loading / empty / error / offline 由 `PAGE_STATES` 统一提供。
- **消歧（本轮补）**：同品牌两家店返回两行，各自带「所属 X」与地址；
  命中别名时该行自报「以「Y」匹配（曾用名／别称）」；每行给「生效规则 N 条 · 时效」。
- **排序（本轮修）**：原先按名称字母序，导致未收录规则的分店排在已核验总店前面。
  现为匹配质量 → 有无生效规则 → 时效 三级排序。**排序只影响显示顺序，不参与 verdict。**
- 详见 `docs/frontend/SEARCH_DISAMBIGUATION.md`。

### Map（§43）

- 覆盖提示 `coverage-hint`、列表/地图切换 `view-map` / `view-list`、
  定位态 `location-label`、拒绝态 `location-denied`、离线横幅 `offline-banner`、底部 sheet。
- **限制**：`MockMap.vue` 是本地模拟组件，没有接入真实地图 SDK；
  marker 状态由真实评价结果驱动，但地理渲染是模拟的。因此标记 MAP = PASS_WITH_LIMITATIONS。

### Place Detail / Rule Passport（§44–§45）

`PlaceView.vue` 的 10 段顺序即 canonical 顺序：

1. 当前答案（`section-answer`） 2. 哪里可以/不可以 3. 条件 4. 共处边界
5. 怎么进入 6. 设施 7. 来源与时效 8. 现场记录 9. 历史版本 10. 纠错/补充

- 首屏第一信息是答案，不是地址/营业时间/图片。
- 子请求失败降级为 PARTIAL 并点名失败段（`degrade("核验历史")`），不是白屏。
- 「为什么是这个结果」按钮 `open-why` 位于答案区。

### Rule Trace（§46）

`MatchExplainView.vue`：最终结果 → 附加条件 → 推导过程（`explanation_steps`）→
被抑制的规则 → 未解冲突（需人工复核）。展示面向用户，**不输出 UUID / 内部优先级 / 原始 JSON**。

### Evidence Rail（§47）

来源用 `SOURCE_BADGES` 呈现（官方法规 § / 管理方确认 ◉ / 现场核验 ◎ …），
带最近核验日期；URL 不是主视觉。

### Unknown / Stale / Review（§50）

- UNKNOWN = 「尚未核验」，aria 明确写「不代表允许」。
- STALE = 「需要复核 / 证据超出核验时效，结论可能已变化」。
- 三者都有图标 + 文字，不靠颜色。

## 未达标项

| # | 项 | 现状 | 影响 |
| # | 项 | 现状 | 影响 |
|---|---|---|---|
| 1 | 地图为 MockMap | 无真实地图 SDK，**marker 坐标由场所 UUID 哈希合成，与真实经纬度无关** | 地图 Tab 不能用真实导航；**Area/Lens 选择器因此不做**（见 `MAP_AREA_LENS.md`） |
| 2 | ~~A11y 覆盖不完整~~ | **本轮已修**：22 页机器审计 serious/moderate/minor 全为 0，键盘走查无不可见焦点 | — |
| 3 | ~~无可视化回归基线~~ | **本轮已修**：47 张基线 / 5 视口，比对模式 47 passed | — |
| 4 | 渐进式条件询问未实现 | 仍一次性展示全部适用条件 | 条件多时首屏偏长（`PROGRESSIVE_QUESTION = FAIL`） |

## 结论

**Consumer 核心流程 = PASS**（答案优先、UNKNOWN 不误导、条件/设施分离、证据可达、为什么可达）。

原第 2、3 项已在本轮修复并给出可复跑的实测数字（`A11Y_AUDIT.md`、`VISUAL_REGRESSION_BASELINE.md`）。
剩余两项（Mock 地图、渐进式询问）为已知且不影响治理语义，其中 Area/Lens 的**未实现理由与前置条件**
写在 `MAP_AREA_LENS.md`——不做一个会在合成坐标上骗人的版本。
