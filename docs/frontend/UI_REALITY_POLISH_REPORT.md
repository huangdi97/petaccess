# UI_REALITY_POLISH_REPORT — CONSUMER_AND_ADMIN_UI_REALITY_POLISH_R1

日期：2026-09-16
范围：Consumer H5 + Admin Console，真实启动、真实渲染、真实截图、真实修复
前序状态：PRE-SIGNATURE ENGINEERING HARDENING 完成（pytest 501 / worktree clean）

---

## 0. 这一轮真正做了什么

**不是**继续堆单元测试数量，而是把两个客户端真正跑起来、逐页截图、按截图找问题、修、再截图。

新增的工具（可复跑，不是一次性脚本）：

| 工具 | 作用 |
|---|---|
| `scripts/ui_capture.mjs` | 真实渲染并截图（首屏 + 整页），Consumer / Admin × 多视口 |
| `scripts/a11y_audit.mjs` | 自动化可访问性审计 + 真实键盘走查 |
| `playwright.visual.config.ts` + `tests/visual/` | 视觉回归基线（Consumer + Admin，三档视口） |

三个工具都自带「等页面真的渲染完」的逻辑——这不是洁癖，是因为**第一版审计脚本把骨架屏当成了页面**，报出一堆并不存在的缺陷（见 §4）。

---

## 1. 修复的真实缺陷

### 1.1 匿名会话持续触发 401（Consumer 全站）

**现象**：以未登录状态打开首页 / 搜索 / 地图 / 场所详情，控制台每一页都有 `401 Unauthorized`。

**根因**：`boundary-profiles/default` 与 `places/{id}/boundary-match` 是**账号维度**的接口，但代码无条件调用：

- `MapView.vue` `onMounted` → `void loadBoundary()`（不判断登录）
- `SearchView.vue` `onMounted` → `client.defaultBoundaryProfile()`
- `PlaceView.vue` `load()` → `client.boundaryMatch(placeId)`
- `MatchExplainView.vue` `loadBoundary()`

`session.signedIn` 早就存在，只是没人用。更糟的是 `MatchExplainView` 的兜底逻辑按错误码 `no_boundary_profile` 分支，而服务端对未登录返回的是认证错误——该分支永不命中，于是**把一条认证错误原文显示在了「为什么」页面上**。

**修复**：四处全部改为 `if (session.signedIn)` 门控；`BoundaryView` 在未登录时跳过网络调用，直接给出人话说明（「共处边界保存在你的账号下：登录后即可设置并同步到各页面。」）而不是把传输层错误甩给用户。

**验证**：全 12 个 Consumer 页面 → **0 个 401、0 个 console error**（修复前每页至少 1 个）。

### 1.2 场所详情页串行 N+1：单页 12 次 `/rules/evaluate`

**现象**：一次场所详情加载发出 12 次 `POST /rules/evaluate`。

**根因**：`packages/client-core/src/modes/query.ts` 的 `evaluatePlace()` 是「1 次场所级 + 逐个 zone」的**串行 for 循环**。云栖中心有 7 个分区 → 每次判定 8 个请求，而详情页要两个答案（我的宠物 / 普通宠物基线）→ 16 个请求排队。这是纯串行等待，不是数据量问题。

**修复**：改为 `Promise.all` 一次发出，再按 zone 顺序折叠结果——并发化但结果顺序仍然确定，`obligations` / `unknownInputs` 的展示顺序不变。

### 1.3 Admin 法规页 500：一行历史数据打挂整个列表

**现象**：`GET /api/v1/regulations` 返回 `internal_error`，Admin「法规」页整页不可用。

**根因**：`jurisdiction_rule` 有 **1 行** `mandatory_level='discretionary'`，这是 ADR-023 之前的旧拼写。`normalize_mandatory_level()` 存在、文档也写着「读取时接受旧值」，但 `RegulationOut` 没有调用它，FastAPI 逐项校验响应 → 整个列表 500。**51 行好数据一行都没到前端。**

**修复（两半，缺一不可）**：

1. `RegulationOut` 加 `field_validator(mode="before")` 归一化。放在 schema 而不是端点里，是因为列表 / 场所维度 / 创建 / 复核四条构造路径都会经过它，将来的新端点不可能漏掉。
2. 迁移 `b8d2f4a1c556` 回填数据库里的旧拼写。读取时归一化是兼容垫片，不是把数据留着不管的理由。

**验证**：500 → 200，`total=52`，旧值以 `operator_discretion` 出现。回归测试 6 项（`tests/integration/test_regulations_contract.py`）。

### 1.4 `<RouterLink>` 里套 `<button>`：嵌套交互元素（全站 8 处）

**现象**：a11y 审计报大量「触控目标 20px < 24px」——例如「设置共处边界」「登录 / 注册」「看地图」「拍规则牌 / 现场核验」。

**根因**：写法是 `<RouterLink to="/boundary"><button>设置共处边界</button></RouterLink>`。这是**链接里嵌套交互内容**：两个重叠控件、一个可访问名，而真正被测量的外层 `<a>` 只有内联文本那么高。`button` 有 `min-height` 规则，`a` 没有——所以按钮本身够高，链接不够。

**修复**：新增 `a.btn` / `a.btn-inline` / `a.pill`，把链接本身做成控件。8 处全部替换。**一个控件、一个名字、一个目标**。

### 1.5 Admin 47 处表单标签未关联

**现象**：Admin 审计 36 项 serious 里绝大部分是「form control without a label or aria-label」。

**根因**：`<label>采集器</label>` 紧跟 `<select v-model="...">`——**没有 `for`、没有 `id`、也没有包裹**。视觉上完全正确，但对读屏软件两个字段都只是「edit text」。登录表单就是这样（`<label>邮箱</label><input type="email">`），此前一版审计脚本正是卡在登录页，把登录页当成七个页面审了七遍。

**修复**：批量把 13 个视图里 **47 组** label/控件关联（`for`+`id`，id 由 `v-model` 派生并在文件内去重），登录表单手工修。另外把 `button[type="submit"]` 显式补上——它此前靠 `<button>` 的默认类型工作，任何用属性选择器的工具（包括我们的审计脚本）都选不中。

### 1.6 搜索结果无法消歧 / 别名搜不到

见 `docs/frontend/SEARCH_DISAMBIGUATION.md`（含迁移、API、UI、9 项测试）。

### 1.7 生成客户端与后端漂移（ADR-011 违规）

**现象**：给 `PlaceSummary` 加字段后，H5 编译失败——`rule_count` / `branch_name` / `matched_alias` 「不存在」。

**根因**：`packages/client-core/src/api/client.ts` **手写**了 `PlaceSummary` 接口，而该文件头部明确写着「业务代码不得手写 DTO（ADR-011）」。后端加了字段，手写副本不知道。同时 `schema.d.ts` 本身也已经过期（重新生成后多出约 600 行）。

**修复**：`api-client` 导出 `ApiSchemas`（来自生成的 `schema.d.ts`），`client-core` 的 `PlaceSummary` 改为从其派生；`schema.d.ts` 按 `pnpm client:gen` 重新生成。**从结构上消除了这一类漂移。**

### 1.8 搜索排序把"没有规则"的分店排在首位

**现象**：给演示数据加了同品牌分店后，搜「星河咖啡」的第一行是**尚未收录规则**的分店，答案（总店）在第二行。

**根因**：`list_places` 的 `order_by(Place.canonical_name)` 是纯字母序，没有相关度、没有"这个场所能不能回答问题"的概念。

**修复**：`_search_order()` 三级排序——匹配质量（精确 → 前缀 → 子串 → 仅别名）→ 有生效规则优先 → 时效新者优先，名称兜底。同时转义 `ILIKE` 模式里的 `\ % _`，否则用户输入一个 `%` 会匹配全表。**排序只排显示顺序，不参与任何 verdict 计算。**

### 1.9 `branch_name` 这个名字本身是错的

**现象**：分店行显示「位于 星河咖啡·测试店」尚可，但总店在旧字段语义下是"分店的分店"；而且「位于」对"品牌分店"和"商场里的店铺"两种父级关系只能对一半。

**修复**：字段改名 `parent_place_name`（值就是父级的正式名，名字应当说明它**是什么**），UI 文案改为「所属 X」——对两种父级关系都成立。改名同时暴露并纠正了 `client-core` 里手写 DTO 的注释（见 1.10）。

### 1.10 截图用例不断言"页面是否正确"

**现象**：预览服务器的 API 代理指向了错误端口（`:8000` 而非 `:8010`），**11 个消费者页面全部渲染「加载失败」**，而视觉用例"通过"了 20 个。

**根因**：`toHaveScreenshot` 只比像素，不比正确性。一张「加载失败」的截图，和下一张「加载失败」的截图，永远匹配。唯一暴露它的用例，是因为它需要点击一个错误页上没有的按钮。

**修复**：`tests/visual/fixtures.ts::assertNotErrorState()`，在**每次截图前**检查 `[data-state="ERROR"|"NETWORK_ERROR"]`，命中即抛错并打印页面上的原话。做成 `shot()` 的内建步骤而不是各用例自行调用——否则总有人忘。这也顺带修掉了基线：错误态截图已全部作废重生成。

### 1.11 `webServer.env` 覆盖了整个环境变量表（**两个** config 都有）

**现象**：`playwright test` 与 `playwright test -c playwright.visual.config.ts` 都在 60 秒后
只报一句 `Timed out waiting 60000ms from config.webServer`。

**根因**：Playwright 的 `webServer.env` **不是 merge，是 replace**。写进去 `{ VITE_API_PROXY }`
之后，子进程就没有 `PATH` 了，`pnpm` 直接"not found"，预览起不来。

这个 bug 一直藏得住，是因为**只有需要真正启动的那个服务会暴露它**：API（:8010）与 Admin（:5173）
恰好已经在跑，`reuseExistingServer` 直接跳过启动，看上去"配置是好的"。
以为自己在测"一条命令跑全套"，实际上依赖一个手工起着的服务器。

**修复**（`playwright.config.ts` 与 `playwright.visual.config.ts` 都修）：

- `env: { ...process.env, VITE_API_PROXY: ... }`
- 探测方式从 HTTP `url` 改为 TCP `port`，并去掉 `--strictPort`
  —— 偶发的探测失败不再让 Playwright 对着一个已被占用的端口再启一份，并以 "already in use" 收场。

值得注意的是，`playwright.config.ts` 的原注释写着「Playwright owns it now, so a run is
self-contained（现在由 Playwright 托管，运行自包含）」——**注释说得比代码好，而只有真正跑一次才发现。**

### 1.12 原始枚举值直接上屏

`residential_community` 出现在消费者搜索结果里，Admin 候选表整屏 `ordinary_pet` / `url_monitor` / `integration_fixture` / `MATCH_PENDING` / `PENDING`。这是「开发 Demo 感」最主要的来源。

**修复**：新增 `packages/client-core/src/labels.ts`（场所类型 + 时效措辞）与 `apps/admin/src/labels.ts`（动物范围 / 动作 / 效果 / 抽取方式 / 候选状态 / 规则层 / 证据等级 + 边界判定）。查找**一律回退到原始值**——新增枚举成员会显式地以原文出现（提醒补映射），而不是变成空白。

Admin 候选表另外修掉：`P: 89bd859e… / Z:`（UUID 片段 + 空的分区行）→ **场所名称 + 「分区 xxx」**，无分区时整行不渲染；空场所显示「未归属具体场所（属地规则）」。

---

## 2. 实测结果

### 2.1 消费者 12 页 × Admin 10 页真实渲染

零 console error、零 4xx/5xx（修复后）。截图见 `artifacts/ui-capture/`。

### 2.2 a11y

| | 修复前 | 修复后 |
|---|---|---|
| 问题总数 | 53 | **0** |
| serious | 36 | **0** |
| moderate | 0 | **0** |
| minor | 17 | **0** |

覆盖 22 页（消费者 12 + Admin 10），键盘走查（首页 / 场所详情 / Admin 候选队列）不可见焦点为 0。
详见 `docs/frontend/A11Y_AUDIT.md`。

### 2.3 视觉回归基线

| 项 | 值 |
|---|---|
| 基线总数 | **47**（消费者 33 + Admin 14） |
| 视口 | 5：`h5-390` / `h5-768` / `h5-1440` / `admin-1440` / `admin-768` |
| 比对模式 | **47 passed** |
| 生成后复验 | **47 passed**（基线可复现） |

详见 `docs/frontend/VISUAL_REGRESSION_BASELINE.md`。

### 2.4 本轮最终回归数字（全部当场实跑）

| 门 | 命令 | 结果 |
|---|---|---|
| pytest | `pytest -q`（`--basetemp` 指向一次性新目录，见下方注） | **517 passed** |
| 功能 E2E | `playwright test` | **17 passed** |
| 视觉回归 | `playwright test -c playwright.visual.config.ts` | **47 passed** |
| a11y | `node scripts/a11y_audit.mjs` | **0 issues** |
| ruff check / format | 167 文件 | 全通过 |
| mypy（api app） | 75 文件 | 无问题 |
| eslint / prettier | 全仓 | 全通过 |
| H5 build | `pnpm --filter @petaccess/client-h5 build` | PASS |
| Admin build（含 `vue-tsc` 类型检查） | `pnpm --filter @petaccess/admin build` | PASS |
| bandit | 18,262 行 | HIGH/MEDIUM **0**，剩 15 LOW |
| npm audit --prod | — | 0 |
| 治理冻结 | `governance_snapshot.py --compare baseline` | **UNCHANGED**（SHA256 一致） |
| 语义等价 | `verify_revision_semantic_equivalence.py` | **PASS**（8/8） |

> pytest 的 `--basetemp` 必须指向**仓库外**的一次性新目录。两点原因，都不是洁癖：
> 1. `tests/unit/test_publish_register_resolution.py::test_registry_display_survives_path_outside_repo`
>    专门验证"注册表路径在仓库外时展示不崩"；把 `basetemp` 设在仓库内会让它变成假失败（实测 516 passed / 1 failed）。
> 2. pytest 默认的临时根目录里堆积了早前被中断的 `garbage-*` 目录，每次启动都会试图清理并触发批量删除护栏，
>    导致收尾失败、**汇总行不打印**。换一个全新的根目录即可绕开。

### 2.5 功能 E2E 的两处失败＝"断言没跟上改进"

改完后跑 `playwright test`，16 例里有 2 例红。都不是回归，而是**产品改好了、断言还停在旧形态**：

| 用例 | 失败原因 | 处置 |
|---|---|---|
| `search finds place by fuzzy name` | `getByText("星河咖啡·测试店")` 命中 **2** 个元素——旗舰店本身，和分店行的「所属 星河咖啡·测试店」。Playwright strict mode 报冲突 | 改为按 testid 取结果行 |
| `pet profile requires auth and offers the login path` | 期望 `role=button` 的「登录 / 注册」，实际已是 `role=link`（参见 1.5 的嵌套交互元素修复） | 断言改为 `role=link`，并加 `toHaveCount(1)` |

同时新增 1 例 `same-brand branches come back as two labelled rows, answer first`，
把「同品牌两行各自可辨、父子关系可见、有规则的排在前」固化成 E2E——补上的正是原先只用集成测试守的那层。

---

## 3. 明确没有做的（不冒充通过）

| 项 | 状态 | 说明 |
|---|---|---|
| `MAP_AREA` / `MAP_LENS` | **FAIL** | 地图仍只有「地图 / 列表」视图切换。规范要求 Area（当前城市 / 行政区 / 附近 / 当前地图区域）与 Lens（原始规则 / 我的宠物 / 我的边界）选择器，本轮未实现。见 `docs/frontend/MAP_AREA_LENS.md` |
| `PROGRESSIVE_QUESTION` | **FAIL** | 渐进式条件询问未实现，仍是一次性展示全部适用条件 |
| `APP_NATIVE_SYNC` | **SPEC_READY_NOT_IMPLEMENTED** | 无原生壳代码；本轮只把 tokens / 标签 / 状态语义整理为可复用 contract |
| `pip-audit` | **NOT_RUN** | 见 `docs/engineering/SECURITY_AUDIT.md` §本轮补跑 |
| Admin「AI 建议 vs 人工决定」视觉分离 | **FAIL** | 候选表只有状态列，没有并列的 AI 建议列；规范 §15 要求的强视觉分离未达成。当前 Human Review 走「签署包 + `publish_reviewed_r1.py`」流程，UI 里只有状态机说明 |
| Admin 表格 sticky header / 列宽控制 | **FAIL** | 长来源、长引文在窄屏会撑高行高；无 sticky header |
| Admin 发布前影响范围预览 | **FAIL** | 不展示「将影响 N 条规则 / M 个场所」 |
| Evidence Detail 独立页（消费者侧） | **NOT_COVERED** | 消费者只有 PlaceView 的第 7 段与证据入口，没有独立证据页；视觉基线里也没有 |
| RESTRICTED / STALE / NETWORK_ERROR 状态页 | **NOT_COVERED** | 状态词汇有实现，但没有单独出图 |

> 更正：「Admin 危险按钮二次确认」上一版记为 PARTIAL（"未见确认弹窗"）——**该结论是错的**。
> 代码核实 `RuleCandidatesView.vue:86-113` 存在 `guard()` 两次点击确认，发布与驳回都走它，
> 第一次点击后按钮文案变「再点一次确认发布/驳回」且 class 转 `danger`。
> 已改为 PASS，并据此修正 `ADMIN_UI_AUDIT.md`。这类"上一版说 PARTIAL、其实已经做了"的结论同样要当场核实。

## 4. 方法论教训（值得写下来）

**审计脚本自己会撒谎。** 第一版 `a11y_audit.mjs`：

1. 用 `waitUntil: networkidle` + 450ms 固定等待 → 场所详情页的第二波请求还没回来，审的是骨架屏，于是报出**并不存在的**「没有 h1」。
2. 用 `button[type="submit"]` 选登录按钮 → 该按钮没有 `type` 属性，30 秒超时；退化成 `catch(() => {})` 之后，**Admin 七个页面审的全是登录页**（控件数完全相同：24），而报告看不出来。
3. 用 `#/review`、`#/publish` 等**不存在的** hash 路由 → 路由回落到登录页。

一个会凭空造缺陷的报告，比没有报告更糟——它训练读者忽略它。三处都改为：等骨架屏消失、用真实选择器、用真实路由，并且**登录失败要显式失败**（`expect(page.url()).not.toContain("/login")`）。

**「上次报告写 PASS」不等于现在 PASS。** 本轮 a11y 从 36 项 serious 降到 0，中间还纠正了自己上一版的 3 类假阳性。数字必须当场跑出来。
