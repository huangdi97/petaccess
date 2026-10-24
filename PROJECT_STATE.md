## Current phase（2026-10-24 — v11 mobile Map chrome compression + spatial-context polish）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮先重新核验远端：进入时 HEAD=`d8048863aafa1527e8074670ccd8a8bf7c4659ec`，相对 2026-10-19 的 `3c614320...` 已前进 **196 commits**；该 HEAD 的 PR CI / UI Direct Validation / UI Direct Visual / Public Preview Stack 均 **SUCCESS**。同 HEAD 最新 Human Review artifact（约 23.2 MB）已实际拉取并目视检查。
- 最新真人视觉复核结论（不代替用户签字）：Home / Search / Place / Reality / Evidence / Contribution 的大框架已稳定进入 Urban Spatial Guide；Map selected sheet（有/无 governed scene media）也已形成 compact spatial bridge。当前最明显残留集中在 **mobile Map 顶部 chrome 仍有三层感** 与 fallback basemap 的工程提示。
- 外部设计复核继续支持本轮方向：
  - Apple HIG Maps：地图应保持可交互、避免长期遮挡地图的非必要 UI；selected place 应使用 place card / sheet，同时保留地图上下文；
  - AllTrails：map pin → bottom card → details，地图保持主表面。
- 本轮直接完成：
  - `ea3ef1e4`：移动 Map 的 Rule / Reality / Facility / Divergence 保持四个一等 Lens，但从永久四段式按钮收口为 compact mobile selector；desktop 四段式不变。
  - `0157a8d0`：mobile query context + Lens selector + map/list control 压入同一第二行，地图从三层顶部 chrome 收为两层；query summary 在窄屏可省略截断但语义仍可编辑。
  - `77e0d2c9` / `71646d78`：fallback map 真实性披露收为一份轻量 caption，删除 MockMap 内重复 provider 提示；不弱化“简化空间底图 / 已收录坐标未核验”事实。
  - `aef608ba` / `e63ec7c1`：Human Review 与 map.mobile visual contract 改为 mobile compact Lens selector；四 Lens 数量和单一 active lens 仍是 FAIL gate。
  - `6ba1eb1c`：E2E 同步 compact mobile basemap disclosure。
  - `1c3a9704`：320–379px 明确覆盖旧 narrow-screen search offset，保持同一两行 overlay stack，不额外吃掉地图高度。
  - `812ea474`：Lens selector / query context / map-list controls 统一为 38px rhythm、12px radius、同一 shadow language，减少拼装感。
  - `f7e5ad9c`：新增 430px mobile Lens route-sync E2E，切换 Reality 后 selector / URL / marker semantics 必须同步。
  - `b85e3f00`：删除 fallback map “缩放 N 级 · 示意比例”调试式 caption；真实 zoom 交互保留，简化底图不暗示额外测量精度。
- 本轮未改变 Rule / Reality / Evidence domain semantics、API、治理审核、Tauri/Android runtime、release signing 或发布状态。
- 当前源码 HEAD（本段写入前）=`b85e3f00c25be8f1e01b1b75145c70668f6b01db`。该 HEAD 的 Actions 已触发但本段写入时尚未取得完成结果；**禁止复用 d8048863 的 SUCCESS 冒充当前最终 HEAD PASS**。
- 下一门禁：同一最终 HEAD 的 UI Direct Validation / PR CI / UI Direct Visual 全绿后，重新拉取 Human Review，重点目视 320/360/390/430 mobile Map 顶部占屏、Lens selector、selected sheet 与 fallback disclosure。机器 PASS 仍不等于用户 Human Visual Acceptance。

## Current phase（2026-10-21 — v11 Place dual-fact signature + Evidence purpose closure）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮在最新 Human Review 基础上继续收口，而不是重做 IA。目视确认当前最大残留已从 card-wall 转为“事实维度辨识度”：mobile Place 的 Rule 与 Reality 虽语义独立，但此前主要依赖顺序区分；Evidence 首屏则更像一条场所记录而不是明确的 provenance 页面。
- 本轮直接完成：
  - `e2683b13` / `3b9a6517` / `999b29ec` / `902df2b5`：Place Overview 冻结可见的 **规则 / 现场** 双事实语法。Rule rail 按 ALLOWED / CONDITIONAL / RESTRICTED / CONFLICT / UNKNOWN 辅助表达，Reality 使用独立 observed-fact rail；手机端两个维度标签保持可见，颜色永不成为唯一含义。
  - `018b5917` / `a7601be4` / `8a8d809c`：Map Selected Sheet / desktop PlacePreview 补齐 CONFLICT rail，避免来源冲突错误退化为 Unknown 的视觉语气。
  - `3bde7152` / `f31afa91`：Place mobile/desktop UI contracts 新增 `PLACE_OVERVIEW_FACT_DIMENSIONS_VISIBLE`，强制 Overview 同时可见“规则”“现场”两个维度，防止未来 Agent 再隐藏其中之一。
  - `0176730f` / `dbf87a29`：Evidence 将“证据与来源”提升为真实可见 page title，地点名退为上下文；Evidence contract 增加首屏可见标题 gate。
  - `ce56d3fc`：v11 母版冻结“Place 双事实签名”和“Evidence = provenance surface，不是另一张 Place detail”。
- 这些改动不改变 Rule / Reality / Evidence domain semantics、API、审核治理、Android/Tauri runtime 或发布状态。
- 当前 branch tip=`ce56d3fca9710bad23abdc77bf6a9b5495d5467b`。PR CI / UI Direct Visual / UI Direct Validation / Public Preview Stack 已触发但本段写入时均为 **QUEUED**；不得复用旧 HEAD 的全绿结论。
- 下一门禁：等待同一 HEAD 的格式、E2E 与 UI contract 结果；若通过，再拉取 Human Review 核验 Place mobile 双 rail、Place desktop reading rhythm、Evidence 首屏 title 与新版 MockMap。机器 PASS 仍不等于用户 Human Visual Acceptance。

## Current phase（2026-10-21 — v11 spatial canvas + selected-place fact-language polish）

- 分支 `feat/ui-direct-craft-v8`；PR #1 保持 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮重新核验远端真实 HEAD=`89a9994a67c466d296768171a10697c4835402f6`；相对 2026-10-19 的 `3c614320...` 已前进 **161 commits**。该 HEAD 的 PR CI / UI Direct Validation / UI Direct Visual / Public Preview Stack 全部 **SUCCESS**。
- 已拉取并目视检查同 HEAD 的最新 Human Review（约 22.9 MB）。结论：Search、Place、Reality、Contribution 和 selected-place bridge 的大框架已经进入稳定 Urban Spatial Guide；当前最明显的残留不是 card-wall，而是 fallback map 仍偏“测试底图”，以及 Map selected surface 的 Rule / Reality / Facility / Divergence 视觉语法仍过于同质。
- 外部设计复核继续支持当前方向：
  - Apple HIG Maps 明确建议 selected place 使用 compact/full place card 并保持地图位置可见，避免重复信息；
  - Apple Sheets 强调默认尺寸应帮助用户保留父级上下文；
  - AllTrails 继续使用 map + drawer / nearby selection 的空间浏览模型；
  - AccessNow 3.0 将地点信息拆成清晰 section，并支持单 feature / photo 贡献。PetAccess 只借鉴空间层级与单事实贡献，不引入总评分。
- 本轮直接完成：
  - `0460f57b`：增强 MockMap 城市空间 fallback——增加多块开放空间、plaza、local road，提升 block / road / river / urban mass 层次；继续明确标注“示意底图（非真实街道）”，不制造场所名、规则或定位精度。
  - `40e2568b`：mobile MapSelectedSheet 为 Rule / Reality / Facility / Divergence 引入 restrained semantic rail；颜色只作辅助，文字结论仍为主。
  - `ef346791` + `773f70a0`：desktop PlacePreview 同步同一 fact-dimension visual grammar；非 Rule lens 不让 Rule 色彩抢占主语义。
  - `7f74af30`：v11 设计母版冻结“fallback map 必须像城市空间但不得伪造地理事实”以及“semantic rail 不能退化为 friendliness score”。
- 当前最终 branch tip 以 GitHub 为准；本段写入后 Actions 会针对最终 HEAD 重跑。旧 HEAD 的 SUCCESS 不得冒充本轮结果。
- 下一视觉门：同一最终 HEAD 的 UI Direct Visual / PR CI；之后重新拉取 Human Review，重点检查 fallback basemap 的城市感、mobile selected sheet 四类 lens、desktop selected preview，以及 320/360/390/430 宽度下是否仍保持地图主表面。

## Current phase（2026-10-21 — v11 visual contract repair + Search hierarchy closure）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release。
- 重新核验时远端已比 2026-10-19 的 `3c614320...` 前进 **158 commits**，v11 已继续大规模落地：`MapSelectedSheet.vue`、Place/Search/Map、Human Review、视觉合同与 `consumer-discovery-v11.css` 均有实质更新。
- HEAD `ca019183...` 的机器结果：PR CI / UI Direct Validation / Public Preview Stack = **SUCCESS**；UI Direct Visual = **FAIL**。失败发生在 `Compare UI contracts`，Human Review 截图捕获本身 SUCCESS。
- 拉取并检查 run `39604053745` 的 `ui-direct-v8-visual`（约 23 MB）后确认：Home / Map / Map mobile / Place desktop / Place mobile / Reality / Evidence / Search desktop 合同均 **0 FAIL**；Search mobile 仅 1 WARN；唯一 FAIL 家族是 Contribution（18）。
- Contribution FAIL 根因不是当前 UI 画面：oracle 的 `contribute-entry` probe 实际被 session-restore race 导回 Home（probe state = `page=home, route=#/`），后续 step-1 / step-2 / review 又可正常进入 Contribution。已在 `tests/ui-oracle/oracle.spec.ts` 中让 authenticated oracle 在写入 token 后完成一次 document reload + settle，再导航到受保护 route，避免把 Home DOM 误标成 Contribution。
- 同一视觉包的 Search mobile 唯一 WARN 为 `SEARCH_MOBILE_PRIMARY_HEADLINE_TO_BODY`：主语义行 16px / body 15px，ratio = 1.07 < 1.1。已把移动 Search 的 Rule/Reality lead 提到 tokenized 17px + medium weight，保持地点名/metadata 结构不变。
- 最新真实截图人工复核（不替代用户签字）：Map selected-place sheet 已形成轻量 spatial bridge；governed-media Place 已呈现 destination surface；Reality 是 timeline-first；Contribution chooser 已是 divider-led one-question flow；Home/Search 均已明显脱离 SaaS/card-wall 原型。
- 本轮提交：
  - `b157d16f` — stabilize authenticated UI oracle session before routing；
  - `03dd56bc` — strengthen mobile Search semantic hierarchy。
- 当前源码 HEAD：`03dd56bc40d6504dde9d07bb1833fdd00b47a9b7`。本段写入时该 HEAD 的新 Actions 尚未返回可核验结果，因此不得写为 PASS。
- `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` 保持；下一门槛是同一最终 HEAD 的 UI Direct Visual 0 FAIL + 新 Human Review，再决定是否继续做更小的视觉精修。

## Current phase（2026-10-21 — v11 hierarchy closure: media serves Rule, CI pending）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮从远端真实 HEAD `21fb486468c0b5f64517233856273bf8e9e1e3c4` 继续；相对 2026-10-19 的 `3c614320...` 已前进 150 commits。该 HEAD 的 UI Direct Validation / UI Direct Visual / Public Preview Stack = SUCCESS；PR CI 仅 Playwright 1/211 FAIL，其余 engineering/frontend/backend 均 SUCCESS。
- PR CI 唯一失败根因不是视觉或 domain：snapshot transport failure 时 desktop Overview Evidence 的“规则依据”已显示“暂时无法取得”，但“现场来源”仍显示“暂无”，与 fail-closed partial truth 不一致。本轮 `6baf681a` 修复为 `snapshotError → 现场来源暂时无法取得`。
- 同 HEAD 最新 Human Review（约 22.9 MB）已实际拉取并目视：
  - mobile selected Map sheet 已形成 dominant map + compact place bridge；有/无 governed media 两种状态都成立；
  - Home 已是 compact city-space launcher，但 governed media / city illustration 仍可继续压缩以让 nearby/Rule 更早进入首屏；
  - no-photo Place 已是 text-led editorial identity；
  - governed-media Place 仍有“媒体先于规则过多”的余量；Reality timeline 已稳定。
- 本轮继续直接完成：
  - `dc900bac`：Home desktop/mobile hero 再压缩；governed-media Place hero desktop/mobile 再压缩，Rule 更早进入首屏；
  - `562cbe4d` / `85036d28`：清理 place mobile/desktop contract 的旧 v9/status-chip 描述，和 v11 单一 Rule owner 对齐；
  - `c611bdfa`：Human Review 增加 `firstViewportTestids`；governed-media Place 强制 `section-answer` 起点位于初始 viewport 内；
  - `3f67d88c`：v11 设计母版冻结“governed media = orientation, not decision；不能把 Rule 推到 fold 以下”。
- 视觉方向保持：Map-first；Place destination-first；Rule=decision、Reality=time、Evidence=provenance；无审核照片绝不补 generic venue imagery；selected-place sheet 只做空间浏览到 Place 的 bridge，不变成 mini dossier。
- 当前最终 HEAD（本段写入前）=`3f67d88c4378f5df9c3d7bd07c163420482179bb`。该 HEAD 的四条主 Actions 已触发并处于 pending/queued；禁止复用旧 HEAD 的 SUCCESS 作为当前结果。
- 下一门禁：同一最终 HEAD 的 PR CI + UI Direct Visual；成功后拉取新的 Human Review，重点核验 governed-media Place 的 Rule 是否真实进入首屏，以及 Home 首屏空间占比是否继续优于上一轮。

## Current phase（2026-10-21 — v11 spatial bridge polish continuation）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮继续只收 Consumer presentation，不改 Rule / Reality / Evidence 语义、API、审核治理或 Android runtime。
- 外部参考再次支持当前结构：AccessNow 最新版将地点信息拆成清晰 section 并允许单 feature / photo 贡献；Mapstr 强调 map→place card→filter/tag 的轻量空间切换。PetAccess 继续拒绝总评分，只借鉴“地图主表面、地点上下文、单事实贡献”。
- 本轮新增/继续完成：
  - mobile Map 当前同行条件从满宽第二横条收为浮动 context chip，搜索保持唯一主输入；
  - governed-media mobile selected sheet 已加入 canonical Human Review shot，今后 CI 同时审有图 / 无图桥接状态；
  - selected Map route 已加入 320/360/390/430/768/800/1024/1280/1440/1920 responsive overflow 矩阵；
  - desktop selected preview 有 governed scene media 时不再同时重复 place-type glyph；“查看场所”从主按钮降为轻量文本动作，继续避免 mini-dossier。
- 上一轮 PR CI 的两个旧 selector 回归已经迁移到 v11 canonical Overview Rule/Evidence owner，并补充 snapshot transport failure 的显式 evidence 文案；同时新增结构门禁：Overview 禁止 duplicate sticky inspector，Rules secondary view 必须保留 context rail。
- 当前源码 HEAD（本段写入前）=`4bd4814e7061993890a0d5549bc31f188f856404`。四条主 Actions 已触发但仍在执行；不得提前声明 PASS。
- 下一视觉门：同一最终 HEAD 的 UI Direct Visual / PR CI 完成后，重新拉取 Human Review，重点看 mobile context chip、governed-media selected sheet、desktop selected preview、320px selected-map state。

## Current phase（2026-10-21 — v11 canonical Overview ownership + PR CI recovery）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮重新核验远端时 HEAD=`3c86db24772617033abb9eda4cd943bf822a6b6d`，相对 2026-10-19 的 `3c614320...` 已前进 136 commits。该 HEAD 的 UI Direct Visual / UI Direct Validation / Public Preview Stack 均 SUCCESS；PR CI 失败于 2 个旧 E2E selector，不是 backend/type/build 失败：Engineering quality / Frontend / Backend 均 SUCCESS，Playwright 199/201。
- 最新 Human Review 已实际拉取并目视复核：
  - mobile Map selected sheet 已形成 dominant map + compact bridge，Rule / Reality 分层清楚；
  - governed-media Place 已形成 destination hero + editorial overview；
  - Home / Search / Reality 均明显摆脱旧 card-wall / SaaS archetype；
  - 当前剩余问题主要进入“层级真实性与回归合同”阶段，而不是重新设计大框架。
- PR CI 两个失败根因：
  1. `h5-journey.spec.ts` 仍查找 Overview 已主动删除的 `inspector-verdict`；v11 canonical owner 已改为 dossier 内 `answer-status`；
  2. `place-route-race.spec.ts` 仍查找 Overview 已删除的 `inspector-evidence`；同时 snapshot transport failure 的 Overview 证据文案需要明确区分“暂时无法取得”与“来源待补充”。
- 本轮直接完成：
  - `d15e1f8f`：PlaceOverviewPane 在 snapshot transport failure 时明确显示“规则依据暂时无法取得”，不把网络失败冒充为数据缺失；
  - `21bb28bb`：mode-switch E2E 改绑 canonical Overview Rule owner（`answer-status`）；
  - `1fb6755b`：partial-error E2E 改绑 `overview-evidence` 并检查 Rule / Reality failure truth；
  - `b8af866c`：v11 设计母版合并重复 Selected Place 章节，冻结 Overview 单一 Rule owner 与 compact Map bridge 语义；
  - `d936bfb0` / `161d93ec`：Map/Place acceptance 新增结构防回退：Overview 必须无 duplicate `place-inspector`，Rules secondary view 必须保留该 context rail。
- 这轮没有修改 Rule / Reality / Evidence domain semantics、API、review governance、Tauri runtime、release signing 或发布状态。
- 当前最终 branch tip 以 GitHub 为准；本段写入后 Actions 会再次按最终 HEAD 执行。任何旧 HEAD 的 SUCCESS 不得冒充当前结果。

## Current phase（2026-10-21 — v11 desktop Place destination hierarchy continuation）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮重新从最新远端事实继续：进入时 HEAD=`822e9fc2404a205df2c4b0aa62ad25fac3b563a2`，相对 2026-10-19 的 `3c614320...` 已前进 126 commits。该 HEAD 的 UI Direct Visual / Public Preview Stack = SUCCESS，但 UI Direct Validation / PR CI 因 **单一 Prettier drift（MapSelectedSheet.vue）** 失败；Backend / engineering gate 已成功，不属于产品行为回归。
- 已使用同 HEAD 成功的 `UI Direct Format Preview` artifact 作为 canonical Prettier 输出来源，而不是手工猜格式；`92cfb43a` 回写 MapSelectedSheet 唯一格式差异。
- 同 HEAD 最新 Human Review 已再次目视复核：mobile selected-place half sheet、Home、Search、Reality、Contribution 已进入稳定的 Urban Spatial Guide 原型；desktop governed-media Place 仍存在一个明显的 dashboard 残留——Overview 主体已经拥有完整 Rule/Reality，但右侧 sticky DecisionInspector 再次重复结论。
- 本轮继续完成 destination-first desktop Place：
  - `f381a0c9`：PlaceOverviewPane 将“desktop 信息密度”与“是否存在外部 decision inspector”解耦；Overview 在 desktop 也能拥有完整自然语言 Rule decision；
  - `ac26d01e`：desktop Overview / Unknown 不再渲染 sticky inspector，并扩展为约 960px 单一 destination reading surface；Rules / Space / Reality 二级视图仍保留 sticky decision context；
  - `5f7fc3b4`：place.desktop UI oracle contract 同步拆分 Overview 960px + primary decision 与 secondary-view 820–860px + subordinate inspector，防止旧 contract 把重复侧栏重新逼回来；
  - `239aed46`：v11 设计母版明确冻结“Overview 不重复 verdict；sticky decision rail 仅用于二级 Place views”的原则。
- 外部设计复核：Apple 当前 HIG 强调 visual hierarchy / simplicity / preserve context；Apple Maps 的 place-card/detail-sheet 模式也把地点详情视作地图上下文中的单一详情表面。这支持 PetAccess 的 `Map → selected-place bridge → single destination Place`，而不是 `Place main content + duplicate verdict dashboard`。
- 当前本段源码与合同已触发新 Actions；写入本段时仍在执行，因此禁止提前写 PASS。下一门禁是同一最终 HEAD 的 Prettier / UI Direct Validation / PR CI / UI Direct Visual，再拉取 Human Review 验证 desktop Overview 去 inspector 后是否真正更像目的地阅读页而不是后台详情页。

## Current phase（2026-10-21 — v11 destination surface continuation）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮重新核验远端真实 HEAD = `cf358366c53d88f8a30f8b51365bc7c3ca231a1a`；相对 2026-10-19 的 `3c614320...` 已前进 122 commits。该 HEAD 的 Public Preview Stack / UI Direct Validation / UI Direct Visual / PR CI 均 **SUCCESS**。
- 已拉取并目视检查同 HEAD 最新 Human Review artifact（约 23 MB）：Home 已是 compact city-space launcher；Reality timeline 已成立；Map selected half sheet 已明显优于 v10；governed-media Place 仍有“inset rounded hero + pill actions”残留。
- 本轮直接完成：
  - `b6f4fc3b`：Map selected sheet 在存在 governed scene media 时，half/closed identity 使用真实小缩略图；无媒体继续只用 place-type glyph，不制造地点图片；
  - `b4fdcafe`：governed-media Place hero 继续去卡片化——desktop 减弱圆角；mobile 改为 full-bleed destination surface；Hero actions 从大 pill 降为轻量文字动作。
- 设计母版同步补充：Selected Place half state 只保留 place identity / active lens fact / 一个必要的跨维事实 / open-place；真实 scene photo 仅作为受治理 destination identity，不存在则绝不补 generic venue imagery。
- 当前源码 HEAD（本段写入前）=`b4fdcafe119e4d23710da4a8c102c67bdc0f6ef7`。四条主 CI 已触发但仍处于 pending；不得提前声明 PASS。
- 下一门禁：等待同一 HEAD 的 UI Direct Visual / PR CI；成功后重新拉取 Human Review，重点看 mobile governed-media Place 是否真正摆脱“卡片 Hero”、Map sheet 有照片/无照片两个分支是否都成立。

## Current phase（2026-10-21 — v11 reading surfaces + field-capture polish, CI pending）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮开始时重新核验远端真实 HEAD = `5f9d9b5754d1c34a9b6d1af6ea25b0f2f72faedf`；相对 2026-10-19 的 `3c614320...` 已前进 105 commits。该 HEAD 的 Public Preview Stack / UI Direct Validation / UI Direct Visual / PR CI 均 **SUCCESS**。
- 已拉取并目视检查同 HEAD 的最新 `ui-direct-v8-visual`（约 25.6 MB）：
  - Home 已从 landing page 收口为较短 city-space launcher；
  - mobile/desktop Map 已形成 dominant spatial canvas + selected-place bridge；
  - no-photo Place 为 text-led editorial identity；
  - governed-photo Place 的 UI 层级已成立，但旧 Human Review fixture 内的大字测试水印会污染视觉判断；
  - Reality / Evidence 仍因专属背景 override 呈现偏灰褐“档案纸”感；
  - mobile Search 已去 card wall，但未知地点的“信息不足”重复层级仍偏响；
  - mobile Contribution 流程正确，但整体仍像一张大表单卡。
- 本轮直接完成：
  - `84699ea3`：Evidence / Reality reading surface 切回 warm-white；Evidence sections 改为 editorial divider-led；mobile Search 再压缩 identity / Rule / Reality 行高与字号；
  - `5b16f52e`：Human Review governed-media fixture 去除图内巨大 CI/NOT-A-REAL-VENUE 文字，改为无文字的明确 synthetic architecture fixture；真实性说明保留在 manifest note，不污染 UI 截图；
  - `b792e1c3`：Search mobile geometry contract 同步到更紧凑的 v11 place-result flow；
  - `01f18e6d`：mobile Contribution 去掉大外框卡片，仅手机变为 in-place field capture；desktop bounded workspace 不变；
  - `e66fd5a8`：Search 中 UNKNOWN 仍明确显示“信息不足”，但降低视觉权重，避免未知地点占多数时形成重复大标题墙。
- 外部参考复核：AccessNow 2025 新版把 place listing 重组为更清晰的 About / Features / Photos / Reviews，并支持只贡献一个 feature 或 photo；这与 PetAccess v11 的“地点分层 + 单事实贡献”方向一致，但 PetAccess 继续保持 Rule / Reality / Evidence 独立，不引入友好度总分。
- 当前源码 HEAD（本段写入前）=`e66fd5a8a82f5f0b5c9c0a775f979adac100e641`。本段自身写入后 HEAD 会再次前进；最新 Actions / HUMAN_REVIEW 必须以最终 branch tip 实测为准，禁止复用 `5f9d9b57...` 的 SUCCESS 冒充当前结果。
- 下一门禁：同一最终 HEAD 的 PR CI + UI Direct Visual 全绿后，重新拉取 HUMAN_REVIEW，重点目视 Search mobile density、Reality/Evidence warm-white、Contribution mobile shell、governed-media Place hero；机器 PASS 仍不等于用户 Human Visual Acceptance。

## Current phase（2026-10-20 — v11 Map/Sheet/Search visual closure + PR CI repair）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 进入本轮前真实远端 HEAD 为 `d003b7c82c6b20f89514fd800247bfb510a973e5`，相对 2026-10-19 的 `3c614320...` 已前进 77 commits；本地/其他 Agent 已重点推进 `MapSelectedSheet.vue`、`PlacePreview`、`MockMap`、Search/Place 与 v11 CSS。
- `d003b7c8...` 机器状态：
  - UI Direct Validation = SUCCESS；
  - UI Direct Visual = SUCCESS；
  - Public Preview Stack Validation = SUCCESS；
  - PR CI = FAILURE，Playwright 196 passed / 4 failed。
- 4 个 PR CI 失败已逐项核验，未把失败简单重跑或隐藏：
  1. Home journey 仍断言旧层级标题“近期值得先看”为 heading；v11 现为“附近场所”主 heading + priority 文本；
  2. transport-recovery contract 仍断言旧 verdict “明确允许”；canonical consumer verdict 已统一为“可以进入”；
  3. reviewed scene test 仍断言旧 caption“经审核允许公开展示的场所场景”；组件当前为“经审核公开的场所场景”；
  4. mobile selected sheet 的 Playwright synthetic PointerEvent 在第二次 drag 的 pointer capture 生命周期超时；真实指针仍需要 capture，但 synthetic pointer 不能假定是 active browser pointer。
- 本轮直接修复：
  - `257e8a11`：MapSelectedSheet 仅对 primary/真实 pointer 尝试 capture，并对 capture/release fail-safe；不降低真实拖动行为；
  - `9c7b49e3` / `f6742f7e` / `45a1e5cb`：同步 v11 Home、verdict、reviewed-scene 三条旧 E2E 文案合同；
  - `69f4d2be`：Home “附近待补充”移除 image-sized generic placeholder，改为 compact place-type glyph；
  - `aea7a9f1`：transport-unavailable nearby rows 同样移除空 scene frame，回到地点身份 + transport truth；
  - `649458df`：Search mobile 结果密度继续收紧（48px visual anchor、104px row），保持 divider-led place list。
- 最新 UI Direct Visual artifact（来自 `d003b7c8...`）已人工抽查：
  - Desktop Map 已形成稳定的 result pane | dominant map | single selected preview；
  - Mobile selected sheet 已正确分离 active lens / Rule / recent Reality，half state 不再堆 evidence/count dashboard；
  - Home v11 已从 landing hero 转为较短 city-space launcher；
  - Place no-photo 状态已是 text-led editorial identity；
  - Search 已去 card wall，但本轮继续降低图块对移动行高的主导。
- 当前最新 HEAD（写入前源码）为 `649458df1dc8995309723144069f9042a5905c8d`。该 HEAD 的新 Actions / HUMAN_REVIEW 尚未完成，因此不得写成 PASS；必须以该 HEAD 后续实际 Actions 为准。
- 下一门禁：等待同一最终 HEAD 的 PR CI + UI Direct Visual；若全绿，再拉取最新 HUMAN_REVIEW 对比本轮 Home/Search/Map selected/no-photo Place/Reality。机器全绿仍不能替代用户视觉签字。

## Current phase（2026-10-20 — Consumer v11 Map/Place visual hierarchy continuation）

- 分支 `feat/ui-direct-craft-v8`；PR #1 继续 **OPEN + DRAFT**；未 merge、未 tag、未 Release。视觉签字仍为 `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 重新核验时远端已从上一轮 `3c614320...` 前进 32 commits 到 `cd695817...`；本地/其他 Agent 已进一步重构 `MapSelectedSheet.vue`、`PlacePreview`、v11 CSS 与 map/search/reality UI contracts，因此本轮只在最新事实之上继续，不覆盖既有成果。
- `cd695817...` 的真实 CI：Public Preview Stack + UI Direct Validation = SUCCESS；PR CI = FAILURE（199/200 E2E，唯一失败为 mobile Map sheet drag pointer 事件）；UI Direct Visual = FAILURE（557 PASS / 2 FAIL，仅 desktop Place 旧 inspector 28px/1.75 hierarchy contract 与 v11 secondary-rail 设计冲突）。
- 已直接修复：
  - `c4bfea16`：MapSelectedSheet drag handle 的 pointer/click 事件 stop propagation，避免拖拽手势泄漏到地图导致 sheet 在 pointerup 前被撤销；
  - `c890b9d8`：Place desktop oracle 升级到 v11 hierarchy——正文拥有完整 Rule decision，sticky inspector 是 secondary reference，不再要求 28px 主视觉；
  - `9d98e13b`：mobile selected-place half sheet 从约 328–352px 收至约 306–324px，保留 Rule/Reality/CTA 但让地图上下文更可见；expanded/closed 同步收口；
  - `2eea4a3d`：v11 阅读画布从偏深 archive-beige 提亮为 warm-white rail surface；mobile Map query context 压成 compact row，lens/view 控件上移，减少顶部 chrome 对地图画布的侵占。
- 最新实际截图复核结论：Home / Place / Reality 已进入正确的 Urban Spatial Guide 视觉原型；下一重点不再是“去 card wall”本身，而是地图空间占比、selected-place bridge 的紧凑层级、warm-white 阅读表面和真实照片 Place 的 destination quality。
- 当前最新源码 HEAD（本段写入前）为 `2eea4a3d12ff2848bce4a06c724dfc1110e83961`；该 HEAD 新 Actions 尚未形成可核验结果，禁止复用 `cd695817...` 的失败或更旧 HEAD 的 SUCCESS 作为当前结论。

## Current phase（2026-10-19 — Consumer v11 Urban Spatial Guide presentation closure in progress）

- 分支 `feat/ui-direct-craft-v8`；PR #1 保持 **OPEN + DRAFT**；未 merge、未 tag、未 Release。当前 `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
- 本轮不是新增 domain 功能，而是继续执行 `docs/ui/PETACCESS_CONSUMER_V11_URBAN_SPATIAL_GUIDE.md`：PetAccess 的 Consumer 第一视觉原型从“规则数据库 / landing page / card wall”收口为 **city-space rule and reality guide**。
- 已直接落地的 v11 视觉原则：
  - Home Hero 从营销式大横幅继续压缩，保留城市空间感但让 Nearby / current task 更早进入首屏；桌面 promo annotation 移除。
  - Map 的“差异”语义解释继续保留在 DOM / accessibility contract，但不再永久占据空间画布；地图本身保持主表面。
  - 无审核场景照片的 Place 不再渲染 generic category scene illustration；只显示明确的“暂无审核场景照片”并回到 text-led place identity，避免把示意图误读成地点事实。
  - 无照片 Place header 改为 editorial / divider-led 结构；操作项降级为文本型动作，不再组成大圆角按钮组。
  - Reality filter chrome 从独立白卡继续降级为内容工具条，timeline 保持主视觉。
  - Search / Map list / Contribution 继续沿用 v11 divider-led / one-question-at-a-time 方向。
- 新真实性回归合同：`tests/e2e/map-passport.spec.ts` 明确要求无审核 scene photo 时 `place-scene-fallback` **必须不存在**，而不是仅隐藏；避免未来 Agent 为视觉填充重新引入 generic venue imagery。
- 本轮提交链截至当前：
  - `a87bf305` — evidence-honest no-photo Place identity；
  - `e3df8d5e` — Map semantic clarification 退出主画布；
  - `af5f1d89` — v11 Urban Spatial hierarchy 收口；
  - `4e2585a5` — 锁定 no-photo evidence-honest E2E contract；
  - `b1f11846` — mobile no-photo Place editorial closure。
- 当前最新 HEAD：`b1f118469fc5a5b22ded85b60da1969b0155f645`。本段写入时该 HEAD 的 GitHub Actions / 新 HUMAN_REVIEW artifact **尚未取得完成结果**，不得沿用旧 HEAD 的 SUCCESS 冒充当前 PASS。
- 下一视觉门：重新生成同一 HEAD 的 desktop/mobile Human Review，重点人工检查 Home 首屏占比、Map 主表面、Selected Place sheet、photo/no-photo Place、Reality timeline；机器 gate 只证明结构/语义/overflow，不替代真人视觉签字。

## Current phase（2026-10-19 — Reference-board visual language + local runtime PASS / CI emulator blocked）

- 分支 `feat/ui-direct-craft-v8`；PR #1 保持 **OPEN + DRAFT**；未 merge、未 tag、未 Release。`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`；机器 PASS 不等于真人视觉验收。
- 本轮 UI 提交：`fea264ca` 目的地视觉层（暖灰画布、深绿主色、场景 Hero、目的地卡片）、`71b43d95` 移动 Hero 构图、`0d6abde1` 去掉打包 WebView 的 backdrop-filter、`66d534a4` 搜索/地图真实审核缩略图 + 无照片场所的“分类场景示意”Hero、`881125c4` e2e 断言同步、`25490727` Android runtime 一次有界重试。这些提交只改 Consumer / Preview workflow / 文档，不改 domain 事实或 API 契约。
- 视觉事实（机器复核，不代替真人验收）：
  - 色板统一到 `#315C46 / #B67232 / #B05446 / #5E7C90 / #E5E1D5 / #1A1A1A / #5E685F`，页面画布为暖灰、内容卡为白；
  - Home 使用原创城市公园插画 Hero（不是真实场所照片），Place 有审核媒体时用真实审核图、无媒体时用同一 Hero 版式并明确标注“暂无审核照片 · 分类场景示意”；
  - Search / Map 列表只把 `purpose === "scene_photo"` 的受治理媒体当缩略图，其余保持分类 glyph；未审核/私有/失败一律 fail-closed。
- UI 合同：本地 UI Oracle **559 PASS / 0 FAIL**（desktop + mobile）。按新目的地 Hero 同步更新 `place.mobile` 首屏行数 38→40、`place.desktop` fullpage 1500→1750 与 first-viewport blocks 3→2，均带 note；没有删除或降低其它闸门。
- 测试：本地 `map-passport.spec.ts` **41/41 PASS**；同 HEAD `25490727` 的 PR CI、UI Direct Validation、UI Direct Visual、Public Preview Stack、Windows Preview Runtime、Android Phone Preview、Branch Autofmt 均 **SUCCESS**。
- 本机真实运行时（Pixel 5 AVD API36 `emulator-5562`，swiftshader，安装 CI 构建的 APK）：
  - FAST = **PASS**、`failure_count=0`；
  - canonical CDP journey = **28/28 PASS**（21 public + 7 authenticated），`horizontalOverflow=false`、safe-area 正常、place-overview 通过；
  - 本地 API 使用 8010，并用模拟器内 iptables DNAT 把 `10.0.2.2:8000` 指向 8010；CI 仍走标准 8000 链路。
- CI Android Preview runtime 仍被外部环境阻塞：API35 在 `hardware_back_from_home` 处 emulator 消失（`adb: device 'emulator-5554' not found`、`Connection refused`）；API36 同类掉线后重试在 launch/CDP 阶段挂起，最终 45 分钟 job 被 cancel。已加入一次有界重试与 20 分钟墙钟上限（`25490727` + 本段），但当前 runner 上仍未取得 CI PASS。
  - 结论：`ANDROID_RUNTIME_ACCEPTANCE`（本机真实模拟器）= **PASS**；CI 侧 = **BLOCKED_BY_EXTERNAL_ENVIRONMENT**，不能写成 CI PASS。
- 当前停止线不变：PR 保持 draft，未 merge、未 tag、未 Release；下一轮在 runner 恢复后重跑 Android Preview，若继续复现再考虑降低 AVD 分辨率或拆分 FAST/journey job。

## Current phase（2026-10-17 — Local×Remote reconciliation + Android Preview runtime closure）

- 分支 `feat/ui-direct-craft-v8`；PR #1 保持 **draft**；master / tag / GitHub Release 均未推进。`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`；机器 PASS 不等于真人视觉验收。
- 本轮先做双向事实核对再开发：工作区 `E:\AI\宠物管理` 当时在 `feat/ui-product-craft-v7-human-review-final`（干净）；ASCII worktree `D:\pa-fix` 在 `feat/ui-direct-craft-v8` 的 `6dc296c`（落后远端 2576 commits，干净）；`git fetch` 后远端为 `d193be30`。本地没有未提交成果或独立提交需要保护，`D:\pa-fix` 直接 fast-forward 到 `d193be30`，未覆盖任何本地工作。
- 本轮提交（在 `d193be30` 之后）：`139e023e` Ruff 格式化；`17dc47f9` CDP journey 终态等待；`57214e90` 生命周期真实进程死亡；`81d4010d` 首页入口卡中文换行；`cd309a1e` 冷启动 Home 有界恢复；`4f6dc690` API 数据接口预热；`59fbd3b7` / `fa9604ec` Windows UTF-8；`30bed586` 场所操作按钮不拆行。
- 源码 HEAD `30bed586` 的远端机器结果（同一 SHA）：
  - Android Preview APK run `39042022036` 四个 job 全 **SUCCESS**：x86_64 emulator APK、ARM64 USB-device APK、API35 runtime smoke、API36 runtime smoke；
  - PR CI `39042025090` SUCCESS（M1 / frontend / backend / Playwright，含 `A1.mobile` 移动端贡献选择器门禁）；
  - UI Direct Validation `39042024956`、UI Direct Visual `39042025029`、Public Preview Stack Validation `39042024984`、Windows Preview Runtime `39042021986`、Android Phone Preview APK `39042022009`、Branch Autofmt `39042022043` 均 SUCCESS。
- 运行时修复有真实证据：
  - API35 lifecycle `process_death` 2/2 PASS：`killMethod=am-force-stop`、`pidAfterKill=null`、`processChanged=true`（此前 `am kill` 并未杀死进程，恢复从未被真正执行）；
  - API36 full journey 28/28 PASS（21 public + 7 authenticated），Search 终态 `search/ready`；此前固定 1.5s 取样会在冷请求时拍到 `loading`；
  - 两条 runtime 均 `horizontalOverflow=false`；Evidence → 系统 Back → Reality，以及 Home → 系统 Back → launcher，由结构化 `androidBackCallback*` 遥测确认。
- 本地真机态复验（Pixel 5 AVD API36 `emulator-5562`，APK 由 `4f6dc69` 构建，`com.petaccess.map.preview`）：
  - FAST = PASS、`failure_count=0`；full CDP journey = **28/28 PASS**；截图与 JSON 证据保留在本轮工作区（不提交二进制）；
  - 本机宿主 8000 被另一 WSL 服务占用，本地 API 临时使用 8010，并在模拟器内用 iptables DNAT 把 `10.0.2.2:8000` 指向 8010；CI 仍走标准 8000 链路，未改变产品 endpoint 契约；
  - 本地运行暴露并修复了 Windows GBK 解码/编码缺陷（`59fbd3b7` / `fa9604ec`），否则成功结果会在汇总阶段被误判为失败。
- 视觉修复（机器复核，不代替真人验收）：移动端首页入口卡文字不再被 45px 图标列挤压逐字换行；393dp 下 Place 三个操作按钮等高、箭头不再单独换行，document 无横向溢出。
- 本段之后的 docs 提交只改文档，不改变 Consumer / runtime；最终停止线不变：PR 保持 draft，未 merge、未 tag、未 Release。

## Current phase（2026-10-13 — direct-v8 Packaged Runtime VERIFIED）

- 分支：`feat/ui-direct-craft-v8`；PR #1 继续保持 **draft**；master / tag / GitHub Release 均未推进。
- 本轮 runtime-verified source HEAD：`be4c14c30bc71740da6cdc99490e6af153e2c287`。
- 同一 source HEAD 的机器链全部通过：
  - UI Direct Validation run `38396421603` = **SUCCESS**；
  - UI Direct Visual run `38396421881` = **SUCCESS**；
  - PR CI run `38396421467` = **SUCCESS**（M1 / frontend / backend / Playwright subset 全绿）；
  - Windows Preview Runtime run `38396412652` = **SUCCESS**；
  - Android Preview APK run `38396412684` = **SUCCESS**。
- Android Preview run `38396412684` 四个 job 全部 **SUCCESS**：
  - x86_64 emulator Preview APK；
  - ARM64 USB-device Preview APK；
  - API 35 packaged-runtime smoke；
  - API 36 packaged-runtime smoke。
- Android runtime evidence artifacts：
  - API35：artifact `11812886680`，约 15.3 MB；
  - API36：artifact `11814505241`，约 14.6 MB；
  - x86_64 Preview APK bundle：artifact `11813260230`；
  - ARM64 USB Preview APK bundle：artifact `11812237961`。
- Android hardware Back 缺陷已由真实 API35 packaged-WebView 证据关闭：在 Evidence 页面触发系统 Back 后，实际 URL 回到 `#/place/<id>/reality`，`uiPage=reality`、`uiState=ready`、`horizontalOverflow=false`；FAST = `PASS`、`failure_count=0`。实现改为 PetAccess 自己的 Consumer route stack，不再把 Android WebView `canGoBack` 当产品导航 SSOT。
- Tauri 官方 `onBackButtonPress` 仍是 Android Back 接管入口；Consumer route stack 决定产品级 back/home/exit。深链无 Consumer 历史时回 Home，并清空深链历史；Home 无 Consumer 历史时退出 Activity。
- Android Preview / Release runtime 边界不变：
  - canonical Consumer = `apps/client-h5`；
  - Android / Windows shell = `apps/client-h5/src-tauri`；
  - `apps/client` uni-app x = `LEGACY_REFERENCE_ONLY`，禁止用于当前构建、人审或 Release。
- 独立 Phone Preview workflow 已存在，但它必须绑定一个真实可公网访问的 HTTPS PetAccess API；workflow 会验证 PetAccess health/ping、`http://tauri.localhost` CORS，并可选强制真实 Tencent map。仓库当前没有 staging/public-beta 部署事实，因此不得伪造“手机下载即独立联网可用”。
- `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` 保持不变。机器 Validation / Visual / Windows / Android PASS 都不能替代用户对当前最终运行画面的真人确认；在明确签字前，不得把 PR 标为 ready，不得 promotion 到 master/tag/Release。

## Current phase（2026-10-13 — Packaged Android Runtime Closure + Mine Personal Center）

- 分支仍为 `feat/ui-direct-craft-v8`，PR #1 保持 **draft**；master / tag / GitHub Release 均未推进。任何机器 PASS 都不等于用户 Human Visual Acceptance。
- 已确认的 Android Preview 基线：Actions run `38345355876`（commit `1a2a8dc6…`）四个矩阵 job 全部 **SUCCESS**：
  - x86_64 emulator Preview APK；
  - ARM64 USB-device Preview APK；
  - API 35 x86_64 packaged-runtime smoke；
  - API 36 x86_64 packaged-runtime smoke。
- API 35 runtime artifact 已人工拆包核验：`Routes=COVERED`、`Authenticated States=COVERED`、`Visual=COVERED`、`Governed Media=COVERED`；19 个 Router 页面 + Place rules/space 共 21 个 public/default case，以及 7 个 authenticated case 都有 packaged-WebView 语义证据与截图。FAST = `PASS`、`failure_count=0`，Evidence → Android System Back → Reality 实证通过。
- Android Preview 是隔离 debug package `com.petaccess.map.preview`，不读取 release keystore；正式 Android release 仍只走 `apps/client-h5 + src-tauri` 的 release workflow。旧 `apps/client` uni-app x 继续保持 `LEGACY_REFERENCE_ONLY`。
- 当前 Consumer UI 继续从“页面能跑”向“真实产品体验”收口：Contribution 手机横向溢出已被真实登录 E2E gate 覆盖；Mine 正在升级为个人出行中心，使用真实宠物/关注/贡献计数并为 0-data 状态提供建档、地图、贡献三个真实动作，不制造虚假个人历史。
- 本段写入时，Mine personal-center 源实现已提交，最新 H5/PR CI/Visual 与新的 Android Preview 正在按最终源码重新执行；在对应 Actions 完成前不得把旧 run 冒充当前最终 HEAD 的 PASS。
- `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` 保持不变。只有用户对当前最终 Web / Windows / Android 实际运行画面明确认可后，才允许 baseline promotion、PR ready、master 集成、tag 或 Release。

## Current phase（2026-10-12 — direct-v8 Android Preview + Runtime Evidence Closure）

- 分支仍为 `feat/ui-direct-craft-v8`；PR #1 保持 **draft**；master / tag / Release 不动。判断状态时仍必须重新读取当前 HEAD / Actions，不能把本文 SHA 当未来事实。
- Consumer runtime 已明确收口：`apps/client-h5` 是唯一当前 Consumer；Windows / Android 使用 `apps/client-h5/src-tauri`（Tauri 2）。`apps/client` uni-app x 已标为 `LEGACY_REFERENCE_ONLY`，禁止用于当前 Android 构建、人审或 Release。
- Android Preview 工作流已落地为隔离 package `com.petaccess.map.preview`，不读取 release keystore，可与正式 `com.petaccess.map` 并存；工程 gate 同时禁止 Release CI 消费 Preview flavor。
- Preview matrix run `38218661525`（commit `682ba4621ec1a0f707969f84df84fe5fe02d9bcf`）真实生成并验证两份 artifact：
  - emulator / x86_64 → `10.0.2.2:8000/api/v1`；
  - usb-device / aarch64 → `127.0.0.1:8000/api/v1` + `adb reverse tcp:8000 tcp:8000`。
  两个 job 均 SUCCESS；workflow 使用 `apksigner verify` + `aapt dump badging` 检查 debug 签名和实际 package。
- ARM64 真机 Preview：`PetAccess-preview-usb-device-aarch64-682ba46-debug.apk`，SHA256 `89dee9719dfcb80791dccd4fd4d582cfd797d2e72ca23427289e7bde4b174a01`；x86_64 模拟器 Preview SHA256 `4be2a81afd30fe570f83f6380430fd802c554bf03dc7ffdcd335e0d0dd660417`。
- 从 `682ba462…` 到本段写入前 HEAD 的后续提交只涉及 docs / acceptance tooling / report，不修改 Consumer/Tauri runtime，因此上述 APK 与当前 Consumer 源在运行时内容上等价；但它们**不替代当前最终 HEAD 的真机/AVD runtime screenshot 证据**。
- Android acceptance 已加强：FAST 对核心页面逐页做 `data-ui-page` 语义确认、横向 overflow gate、即时截图，并要求 Evidence → Android 系统 Back → Reality；任一 `ERROR` 必须让命令非零退出。13-route CDP journey 全 PASS 才允许 Routes = COVERED。
- 真机 Preview 可用 `scripts/android_acceptance/preview_usb_smoke.py` 一键完成 APK package 预检、安装、`adb reverse` 与 FAST；默认正式包 acceptance 语义不变。
- Web 最新 Human Review 中，Contribution mobile 的历史横向裁切已修复并重新目视核验；Home / Search / Map / Place / Reality / Evidence / Mine / Settings 未发现新的布局破坏。机器/助手复核仍**不等于用户 Human Visual Acceptance**。
- `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` 继续成立。最终停止线不变：同一最终 HEAD 的 Web HUMAN_REVIEW + Windows WebView2 + Android AVD/真机运行证据由用户真人确认前，不得 baseline promotion、master 集成、PR ready、tag 或 Release。

## Current phase（2026-10-09 — direct-v8 Consumer Source Closure / Final Runtime Evidence Pending）

- 分支仍为 `feat/ui-direct-craft-v8`；PR #1 保持 **draft**；master / tag / Release 不动。
- `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED / PENDING_REVIEW`：最新机器 Validation/Visual 只证明契约与截图任务可运行，不代表真人已经认可最终视觉。
- Search 已收口消费者结论词汇：列表主结论只允许“可以进入 / 不可进入 / 有条件进入 / 信息不足 / 来源不一致待复核”；技术 resolver summary 不再直接进入主标题。768–1099px 按响应式契约使用 compact list-detail，禁止横向溢出。
- Map 坚持真实空间语义：无坐标不画点；Place→Map 按精确 UUID 读取公开 PlaceSummary；缩放与 nearby 查询半径使用同一覆盖模型；fallback / real renderer 共用 Lens glyph 语义。数据库代表点仅称“已收录位置坐标”，**不等于位置经过实地核验**。
- Place / Why / Contribution / Operator Claim 都采用 route-scoped request generation，迟到的旧场所响应不得覆盖当前场所；Zone 决策按 zone_id 单独请求，不复制场所级答案。
- Reality / Evidence / Facility 保持 published reviewed facts SSOT；publication-only 设施线索不冒充当前设施事实；工作人员处理不自动生成 Operator Policy。
- 最终停止线不变：同一最终 HEAD 的 Web HUMAN_REVIEW + Windows WebView2 + Android AVD 真实运行证据由用户人工确认前，不得 baseline promotion、master 集成、PR ready、tag 或 Release。
- 每次判断机器状态必须重新读取当前 HEAD 的 Actions；历史 PASS、cancelled/action_required run 或旧 screenshot pack 都不能代表当前版本。

## Current phase（2026-10-07 — direct-v8 Source Closure / Final Runtime Evidence Pending）

- 分支：`feat/ui-direct-craft-v8`；PR #1 继续 **draft**；base = `feat/ui-product-craft-v7-human-review-final`；master / tag / Release 不动。
- `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED / PENDING_REVIEW`。用户对旧 runtime 的视觉否决继续有效，任何机器 Gate 都不能替代新的真人审图。
- 本轮继续关闭“UI 文案正确、实际链路错误”的问题：Rule lead → RuleCandidate review；Place correction → moderator correction queue；Reality/Evidence → published v0.9 event stream；Map → PostGIS 真实点位 + 可选 Tencent GL；Search/Home 空态不再跳入无法新增 Place 的 Contribution 死循环。
- Map provider 现在显式区分 `real` 与 `simplified`：无 Key / provider error 时必须展示“简化空间底图”说明，同时点位仍取已收录位置坐标（不等于位置经过实地核验）；Human Review manifest 记录实际 renderer，禁止把 fallback 截图冒充真实地图。
- Consumer SSOT：Home / Search / Map / Place 使用同一 `CoexistenceSnapshot`；Rule、Presence、StaffResponse、Facility、Evidence、Dispute 的语义边界保持不变。
- 当前 GitHub Actions 对此前 bot-authored PR runs 返回 `action_required` 且无 jobs；这不是 PASS。最新 source 需要本地 Agent 或获准的 Actions 对最终 HEAD 重跑 lint/typecheck/build/oracle/human-review。
- authoritative Web 人审包仍应来自 `tests/ui-oracle/human-review-direct-v8.spec.ts` → `artifacts/ui-direct-v8/HUMAN_REVIEW/{desktop,mobile}/`；历史 `artifacts/ui-direct-craft-v8-local-acceptance/` 不得用于当前视觉签字。
- 最终停止线：Web 新截图 + Windows WebView2 + Android AVD 都必须对应同一最终 HEAD。完成并由用户真人确认前：禁止 baseline promotion、禁止 master 集成、禁止把 PR 转 ready、禁止 tag / Release。
## Current phase（2026-10-07 — direct-v8 Canonical Fidelity + Dispute Closure）

- 分支：`feat/ui-direct-craft-v8`；PR #1 保持 **draft**；base = `feat/ui-product-craft-v7-human-review-final`；master / tag / Release 不动。
- `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED / PENDING_REVIEW` 继续有效。机器 Gate、DOM contract、旧 screenshot 均不得替代用户对当前最终 runtime 的真人视觉验收。
- 本轮继续按 Canonical Master §61 / §65–§72 与 `UI_RECONSTRUCTION_DESIGN_FREEZE.md` 反查 source，而不是为了旧 Oracle 数字删设计。
- 已关闭的高价值语义缺口：Home 中性推荐标题恢复为“近期值得先看”；Published Reality dispute 在 Evidence / Event Log / Reality summary 中可见；StaffResponse / AnimalFacility 的 open dispute count 进入 Place Overview / Space / Map Facility Lens，异议不会删除事实、不会修改 Rule。
- Consumer 仍严格保持：Rule != Reality；Observation != Rule；StaffResponse != OperatorPolicy；Facility != EntryPolicy；No Observation != No Animal Presence；Access != Friendly。
- 当前唯一剩余 UI 停止线不是“再做一个版本”，而是：**对同一最终 HEAD 重新生成 authoritative Web HUMAN_REVIEW desktop+mobile，并由本地 Agent 对 Windows WebView2 / Android AVD 当前 HEAD 重新取证；配置真实地图 provider 时补 real-map 证据，否则明确 BLOCKED_EXTERNAL。**
- 在上述真人视觉验收完成前：禁止 baseline promotion、禁止 master 集成、禁止 tag / Release、禁止把 PR 转 ready。

## Current phase（2026-10-06 — direct-v8 Canonical Visual Recovery）

- 分支：`feat/ui-direct-craft-v8`；PR #1 保持 **draft**；`master` / tag / Release 不动。
- `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED` 继续有效：旧机器 Gate/旧 screenshot pack 不能替代真人视觉验收。
- **旧包已降级为历史证据**：`artifacts/ui-direct-craft-v8-local-acceptance/HUMAN_REVIEW/` 对应的是此前 UI/Reality/Map/Contribution 状态，已不能作为当前 direct-v8 的视觉验收依据。
- **新的唯一 Web 人审入口**：`tests/ui-oracle/human-review-direct-v8.spec.ts` → `artifacts/ui-direct-v8/HUMAN_REVIEW/{desktop,mobile}/`。每张 PNG 只有在对应 frozen archetype 的真实 DOM 状态/关键内容存在后才允许写出；manifest 明确标记 `humanVisualAcceptance=PENDING`。
- 新人审包强制覆盖：Home 四任务入口与 Coexistence Digest；Search List–Detail；Place Rule/Reality/Staff/Facility/Evidence；Map 四 Lens；v0.9 Reality event log；Evidence provenance；登录后的 Contribution 五入口/Rule lead/Place correction/Reality flow；Mine/Settings/Privacy/Notifications/Pets/Boundary/Why/About/Onboarding/404。
- 当前继续做的是 **canonical fidelity + semantic integrity**，不是新增 IA：Home/Search/Map/Place 的 Reality headline 已统一到完整 CoexistenceSnapshot（Presence + StaffResponse + Facility），Evidence 元数据也统一统计完整 Reality layer。
- 停止线不变：新 Web 人审包 + Windows WebView2 + Android AVD 对当前最终 HEAD 重新取证并由用户真人审图前，禁止 baseline promotion、禁止 master 集成、禁止 tag、禁止 Release、禁止把 PR 转 ready。


# PROJECT_STATE.md


> ## CANONICAL CURRENT TRUTH — 2026-10-14
>
> **这一节是当前状态唯一入口。下方所有旧 `Current phase` 段落均为按时间追加的历史日志，
> 不得覆盖本节，也不得把其中固定 SHA / PASS / NOT_PERFORMED 直接当成当前事实。**
>
> - 工作线：`feat/ui-direct-craft-v8`，PR #1 = **OPEN / DRAFT**。
> - 判断当前代码必须重新读取远端 branch tip；不要从本文复制固定 HEAD。
> - Canonical Consumer：`apps/client-h5`；Windows / Android = `apps/client-h5/src-tauri`。
> - `apps/client` uni-app x = **LEGACY_REFERENCE_ONLY**，禁止用于当前 build / Human Review / Release。
> - Consumer Discovery v9 核心页面已完成大轮重构；机器视觉门禁不等于真人审美签字。
> - `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`。
> - Android Preview：隔离 debug package `com.petaccess.map.preview`；x86_64 emulator + ARM64 USB
>   build；packaged runtime 以 API35/API36 Actions artifact 为证。
> - standalone Android Phone Preview 需要手机可达 HTTPS `PETACCESS_PHONE_PREVIEW_API_BASE`；
>   未配置时状态为 `BLOCKED_BY_API_BASE`，不影响 emulator / USB Preview。
> - GOV-01 仍需具名人类做规则候选最终裁决；Agent 不代签。
> - 腾讯真实地图仍需真实 client/server Key；无 Key 时只允许声明 provider-neutral fallback。
> - signed 下一版 Release 仍需真实 `PETACCESS_PUBLIC_API_BASE=https://.../api/v1` 及相应
>   legal/platform/governance gate。
> - **v0.1.0 已于 2026-09-24 发布**；当前 draft PR 是其后的候选，不得把
>   `PUBLIC_RELEASE = NOT_PERFORMED` 理解成 v0.1.0 从未发布，只能理解为对应历史阶段
>   “当时没有创建新的 Release”。
> - Android/runtime 证据优先同 HEAD；如果 artifact commit 早于当前 tip，只能在 commit compare
>   明确证明 workflow runtime input 范围内 **0 relevant delta** 时复用。
> - promotion 停止线不变：Human Visual Acceptance 未由用户明确确认前，不把 PR 转 ready，
>   不 promotion baseline，不 merge master，不创建下一版本 tag / Release。
>
> 更结构化的当前事实：见 `PRODUCTION_STATE.md`。
> 发布事实与下一次发布门禁：见 `RELEASE.md`。
> 外部依赖：见 `BLOCKERS.md`。

## Current phase（2026-10-05 — Canonical Visual Recovery implementation complete / CI pending）

- 状态：`DIRECT_V8_CANONICAL_VISUAL_RECOVERY = CODE_COMPLETE` · `MACHINE_ACCEPTANCE = PENDING` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED` · `PR #1 = DRAFT` ·
  `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`。
- 权威恢复冻结：`docs/ui/DIRECT_V8_CANONICAL_VISUAL_RECOVERY_2026-10-05.md`。
  Canonical Master v0.10-R1 决定产品内容；Executable Blueprint 只负责可测几何，不再允许旧 Gate
  删除 Home recommendations/divergence、Map 四 Lens 或 Place Coexistence Passport 首屏事实。
- 本轮 GitHub 实施：Home 恢复四任务 Lens → 按关注推荐 → Rule/Reality 速览 → divergence → recent；
  Search 每行恢复 Rule + Reality + Evidence/Freshness；Map 恢复 Rule / Reality / Facility /
  Divergence 四 Lens 且全部投影同一 CoexistenceSnapshot；Place 首屏恢复 Rule + Reality +
  Staff Response + Animal Facility + Divergence，以及 Evidence / Why / Correction actions。
- 数据边界：`RowFacts` 仅保留服务端 `CoexistenceSnapshot` 作为 Consumer projection SSOT；
  UI 不新增第二 Rule/Reality resolver，不把 Reality / Facility tone 解释为 access verdict。
- 工程收口：已修复上一轮 CI 暴露的 RowFacts fallback type gap；Home digest 与 Map lens projection
  已拆分，避免新增 `vue>200` / `ts>300` quality-gate FAIL；Oracle JSON 已同步 Canonical。
- 停止线：等待本 HEAD 的 PR CI / UI Direct Validation / UI Direct Visual 真实结果。
  即使机器全绿，也只进入 `HUMAN_REVIEW_READY`；在真实 Web / Windows / Android 截图人工确认前，
  禁止 baseline promotion、禁止 master 集成、禁止 tag / Release。


## Current phase（2026-10-05 — direct-v8 Human Visual Reopen）

- 分支：`feat/ui-direct-craft-v8`；PR #1 保持 **draft**；`master` / tag / Release 不动。
- 人工视觉结论：`UI_HUMAN_VISUAL_ACCEPTANCE = REJECTED_REOPENED`。用户在真实本地运行软件中确认：整体产品观感与冻结设计存在明显偏差。
- 机器状态不等于视觉通过：`UI Direct Validation` / `UI Direct Visual` 与 Oracle 全绿仅证明已编码的结构、几何、语言和状态契约通过，**不得再据此写作 Human Visual PASS / UI COMPLETE**。
- 当前唯一 UI 主线：`DIRECT_V8_VISUAL_FIDELITY_RECOVERY = IN_PROGRESS`。依据顺序：Canonical Master → `UI_RECONSTRUCTION_DESIGN_FREEZE.md` → `UI_HUMAN_CLOSURE_V5.md` / 已批准参考 → 当前真实 runtime screenshot → 当前 source。
- 冻结不变量继续有效：Rule / Reality / Evidence-Governance 分离；Observation != Rule；StaffResponse != OperatorPolicy；Facility != EntryPolicy；No Observation != No Animal Presence；Access != Friendly。
- 冻结 archetype 不重做：Home=Task Launcher；Search=List–Detail；Place=Dossier；Map=Spatial Workspace；Reality=Event Log；Evidence=Provenance Record；Contribution=Structured Transaction Flow。
- 停止线：在新的真实 Web / Windows / Android 人工截图明确通过之前，**禁止 baseline promotion、禁止 master 集成、禁止 tag、禁止 Release、禁止把 PR 转 ready**。

### 为什么重开

direct-v8 在若干页面达到了机器契约，但出现了「结构正确、产品视觉不对」的问题：语义状态层级被削弱、Rule/Reality 共处信息没有在首屏形成足够强的产品识别、部分核心 surface 过度稀疏并呈现 prototype / functional-page 感。当前工作是恢复设计 fidelity，不是再发明 IA 或换 Design System。

## Current phase（2026-10-03 本轮实测 — v0.2.7-R1.1.1 Human Review Truth Closure）
- 状态：`V0207_R1_1_1_HUMAN_REVIEW_TRUTH_CLOSURE = MACHINE_PASS` · `HUMAN_REVIEW_PACK = COMPLETE` ·
  `HUMAN_REVIEW_CARDS = 7/7` · `HUMAN_REVIEW_PNGS = 7/7` · `HUMAN_REVIEW_IMG_REFS = 9/9` ·
  `HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS` · `HUMAN_REVIEW_INDEX_EXACT_SET = PASS` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` · `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7-human-review-final`（基点 = origin/feat/ui-product-craft-v7-runtime-final `a83f64f`；
  已 push；BASE_HEAD `42ed4e3` / V7_HEAD `346abbd` / R1_IMPLEMENTATION_HEAD `f8c1227` /
  R1_1_CODE_HEAD `2010775` / R1_1_EVIDENCE_HEAD `647ecd5` / R1_1_DOCS_HEAD `a83f64f`；
  FINAL_BRANCH_HEAD 以最终验证时刻 `git rev-parse HEAD` / `git rev-parse origin/feat/ui-product-craft-v7-human-review-final`
  实测为准（避免自引用死锁）；origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：P0-3 单一最终 writer 修复——`tests/ui-oracle/human-review-r1.spec.ts` 非 oracle-desktop project
  在 pack 组装前 early return，只有 `oracle-desktop` 允许 assemble + 写最终 Index + 跑完结 gates
  （ONE FINAL WRITER，deterministic）；P0-1/P0-2 显式 `HUMAN_REVIEW_EXPECTED_CARD_SET`（固定顺序 7 个）+ exact-set /
  数量(7) / img-ref(9) / orphan / missing / `.png.png` 门禁全部 assert 化。
- 人审包：`artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/`（目录不变，无 v8/v9 噪音）重新生成：
  **7 cards、7 PNG、9 `<img src>`、0 missing、0 orphan、0 `.png.png`**，Index 标题 `7 VALID / 7 total`；
  01–05 = windows-smoke 真实 WebView2 证据逐字节复制（SHA256 一致），06/07 = generator 自然重截
  （state integrity page/state/fixture/h1 全 PASS，`valid=true` 全部来自真实 DOM，零伪造）。
- 机器 Gate（本轮实测）：prettier --check（spec）exit 0；eslint（spec）0 issues；
  human-review-r1 spec（两个 project，`--workers=1`）**2 passed / 0 failed**
  （desktop：7 shots、7 VALID、0 INVALID；mobile：skip assembly 日志 + 不再写 Index）。
- 复用（未重跑，产品代码零改动，`apps/` 0 变更）：ui-oracle 427/0/0、ui-reconstruction 180/180、
  e2e 189/189、visual 59/59（均来自 R1.1）；`WINDOWS_RUNTIME_RERUN = NOT_REQUIRED`（R1.1 targeted 5/5），
  `ANDROID_RERUN = NOT_REQUIRED`，`FULL_PRODUCT_REGRESSION_RERUN = NOT_REQUIRED`，`BACKEND_CODE_CHANGED = NO`。
- 停止线：exact-set 全绿 + Git truth PASS + HUMAN_REVIEW READY，**等待用户人工视觉签字**
  （Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；签字并授权后才执行 Stage B：
  force recapture 批准快照 → canonical baseline = 批准外观 → visual compare ×2 → docs truth →
  verify master ancestor → fast-forward master（仅 FF，无 force/merge/rebase）。

### 历史记录 — v0.2.7-R1.1 Final Micro Closure（2026-10-03，HISTORICAL）

## Current phase（2026-10-03 本轮实测 — v0.2.7-R1.1 Final Micro Closure）
- 状态：`V0207_R1_1_MICRO_CLOSURE = MACHINE_PASS` · `HUMAN_REVIEW = READY` ·
  `WINDOWS_RAIL_OVERFLOW = PASS` · `WINDOWS_RAIL_TOOLTIP = PASS` ·
  `WINDOWS_RAIL_FOOTER = PASS` · `HUMAN_REVIEW_INDEX = PASS` ·
  `WINDOWS_CONTRIBUTION_COMPOSITION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` ·
  `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7-runtime-final`（基点 = origin/feat/ui-product-craft-v7-runtime-closure `7d4772e`；
  BASE_HEAD `42ed4e3` / V7_HEAD `346abbd` / R1_IMPLEMENTATION_HEAD `f8c1227`；
  最终 HEAD 见 `docs/reports/V0207_R1_1_FINAL_MICRO_CLOSURE_REPORT.md` GIT_TRUTH，以 `git rev-parse HEAD` 实测为准；
  origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：P0-1 Human Review Index `.png.png` 修复（生成器 logicalName 模型 + beforePairs 修正 +
  referential-integrity gate：全部 `<img src>` 必须 resolve，`expect(missingImages).toHaveLength(0)`）；
  P0-2 DesktopRail 移除被 overflow-x:hidden 裁掉的自定义 tooltip（span/CSS/rail-tip-in 动画），
  6 个导航 RouterLink 改 `aria-label` + 原生 `:title`，rail 横向 overflow 硬 Gate 保持（scrollWidth ≤ clientWidth + 1）；
  P0-3 rail footer 可见文本改 compact version only = `v0.2`，完整版本/环境保留于 title/data-attribute；
  P0-4 Git/Docs truth：FINAL_BRANCH_HEAD 与 ahead/behind 全部按重新 fetch/rev-list 实测重写。
- 机器 Gate（本轮实测）：prettier PASS、eslint 0、client-h5 vue-tsc+build PASS、admin build PASS；
  ui-oracle **427/0/0**；ui-reconstruction **180/180**；e2e **189/189**；
  visual regression **59/59**（Stage A 不更新 snapshot）；backend `BACKEND_CODE_CHANGED = NO`
  （`git diff origin/feat/ui-product-craft-v7-runtime-closure...HEAD -- services/` 为空）→
  `BACKEND_FULL_RERUN = NOT_REQUIRED`；Android（未改 Contribution layout）`ANDROID_RERUN = NOT_REQUIRED`。
- 真实 Windows runtime（Tauri v2 + WebView2，CDP :9223，沿用 `D:\pa-fix-target-win\debug\petaccess.exe`，
  1120×760）：targeted 5/5 PASS（Map / Contribution choose / step1 / step2 / Rail closeup）——
  rail 67/67 无横向滚动条、Contribution 三页 layoutMode=wide + sameRow=true、
  footer 可见 `v0.2`、6 项 title+aria-label 原生 tooltip 齐备、document 无横向溢出。
- 人审包：`artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/` 7 张
  （01–05 真实 WebView2 targeted refresh + 06 web 1440 WIDE + 07 web 1000 COMPACT）+ BEFORE/AFTER
  （Map / Contribution）+ HUMAN_REVIEW_INDEX.html；
  `HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS`（7/7、0 `.png.png`）。
- 停止线：机器 gate 全绿 + HUMAN_REVIEW READY，**等待用户人工视觉签字**
  （Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；签字并授权后才执行
  canonical baseline promotion → fast-forward master（仅 FF，无 force/merge/rebase）。

### 历史记录 — v0.2.7-R1 Final Runtime Closure（2026-10-03，HISTORICAL）

## Current phase（2026-10-03 本轮实测 — v0.2.7-R1 Final Runtime Craft Closure）
- 状态：`V0207_R1_RUNTIME_CLOSURE = MACHINE_PASS` · `WINDOWS_RAIL_OVERFLOW = PASS` ·
  `WINDOWS_CONTRIBUTION_COMPOSITION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` ·
  `PRODUCT_STRUCTURE = FROZEN` · `MASTER = UNCHANGED` · `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7-runtime-closure`（基点 = origin/feat/ui-product-craft-v7
  `346abbd`，R1_HEAD = `f8c1227`；origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：P0-1 DesktopRail 横向 scrollbar 修复（footer ellipsis + 隐藏 tooltip display:none +
  overflow-x hidden；rail.scrollWidth 104→67）；P0-2 Contribution 双栏 breakpoint 契约
  （COMPACT 768–1119 / WIDE ≥1120，默认窗口 width 1000→1120，默认 Windows runtime 真并排）；
  新增 DESKTOP_RAIL_NO_HORIZONTAL_OVERFLOW + nested contribution gates（oracle 427/0/0）。
- 机器 Gate（本轮实测）：vue-tsc / h5 build / admin build / eslint 0 / prettier PASS；
  ui-oracle **427/0/0**；ui-language 29 FAIL=0；ui-density 28 FAIL=0；
  ui-reconstruction **180/180**；e2e **189/189**；visual regression **59/59**（Stage A 不更新 snapshot）；
  backend `BACKEND_CODE_CHANGED = NO`（git diff 无 services 变更）→ `BACKEND_FULL_RERUN = NOT_REQUIRED`。
- 真实 Windows runtime（Tauri v2 + WebView2，CDP :9223）：9 路由 smoke 全 PASS
  （rail 67/68 无横向滚动条；contribution choose/step1/step2 layoutMode=wide；
  完整 metrics 见 `artifacts/ui-product-craft-v7-runtime-closure/windows-runtime-metrics.json`）。
- Android：贡献 targeted smoke（choose + step1，emulator-5554 / AVD main）PASS + 无 overflow；
  浏览器 responsive 360/390/430 无 Contribution regression（reconstruction/e2e 覆盖）。
- 人审包：`artifacts/ui-product-craft-v7-runtime-closure/HUMAN_REVIEW/` 7 张
  （01–05 真实 WebView2 + 06 web 1440 WIDE + 07 web compact）+ BEFORE/AFTER（Map / Contribution）
  + HUMAN_REVIEW_INDEX.html；metadata actual 全部来自真实 DOM。
- 停止线：机器 gate 全绿 + HUMAN_REVIEW READY，**等待用户人工视觉签字**
  （Agent 不代替 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；签字并授权后才做
  canonical baseline promotion → `git push origin HEAD:master`（仅 fast-forward）。

### 历史记录 — v0.2.7 Product Craft（2026-10-03，HISTORICAL）


## Current phase（2026-10-03 本轮实测 — v0.2.7 Final Product Craft / Spatial Map / Desktop Composition Closure）
- 状态：`V0207_PRODUCT_CRAFT = MACHINE_PASS` · `PRODUCT_STRUCTURE = FROZEN` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW` · `V020_RC_READY = PRESERVED` ·
  `PUBLIC_RELEASE = NOT_PERFORMED`
- 分支：`feat/ui-product-craft-v7`（基点 = origin/master `42ed4e34`，已 push；
  origin/master 未动；v0.1.0 tag 未动；无 v0.2.0 tag / Release / store）。
- 内容：Map Spatial Craft（抽象城市画布 + marker 系统 + selected scale/halo）、
  Contribution Desktop 双栏 composition（main 680 + context 280）、
  Reality/Evidence/Search 阅读节奏收口、§40 十个 craft gates 全绿。
- 机器 Gate（本轮实测）：vue-tsc / h5 build / admin build / eslint 0 / prettier PASS；
  ui-oracle **423/0/0**（398 → +25，WHY_TEST_COUNT_CHANGED=新增 craft gates 与
  map-mobile-expanded 页）；language 29 FAIL=0；density 28 FAIL=0；
  ui-reconstruction **180/180**；e2e **189/189**；backend pytest
  **961 passed / 2 skipped / 0 failed**；visual regression **59/59**（craft diff 全部
  低于 2% 容差 → EXPECTED_CRAFT_DIFF sub-threshold，snapshot 零变更；admin 0）。
- 人审包：`artifacts/ui-product-craft-v7/HUMAN_REVIEW/` 13/13 VALID（O6 全部
  VALID=true）+ HUMAN_REVIEW_INDEX.html + before/after 对照。
- 跨运行时：Android targeted FAST 7/7（emulator-5554 / AVD main；NO_HORIZONTAL_
  OVERFLOW / NO_CRASH / NO_ANR / NO_RENDERER_CRASH 全 PASS）；Windows targeted
  Smoke 7/7（Tauri v2 + WebView2；rail / keyboard / overflow 全 PASS）。
- 环境注记：Docker Desktop 无法稳定启动，DB 栈改用会话级 Windows pg16+PostGIS、
  Windows Redis、moto S3（scratch 内 `pg_up.ps1`/`redis_up.ps1`），仓库代码零依赖。
- 停止线：机器全绿 + 人审包 READY，**等待用户人工视觉签字**（Agent 不代替
  `UI_HUMAN_VISUAL_ACCEPTANCE = PASS`）；未 merge master / 未 tag / 未发布。
### 历史记录 — v0.2.6 RC Integration（2026-10-02，HISTORICAL）
## Current phase（2026-10-02 本轮实测 — v0.2.6 RC Integration / Cross-Runtime Final Acceptance）
- 状态：`V020_RC_INTEGRATION = PASS` · `UI_HUMAN_VISUAL_ACCEPTANCE = PASS_FOR_RC` ·
  `UI_VISUAL_CLOSURE = FROZEN_FOR_RC` · `CANONICAL_VISUAL_BASELINE_PROMOTION = PASS` ·
  `VISUAL_REGRESSION = PASS` · `WEB_FULL_REGRESSION = PASS` · `ANDROID_FAST = PASS` ·
  `WINDOWS_SMOKE = PASS` · `MASTER_FF_INTEGRATION = PASS` · `V020_RC_READY = YES` ·
  `PUBLIC_RELEASE = NOT_PERFORMED` · `AWAITING_RELEASE_AUTHORIZATION = YES`
- 分支：`feat/v020-rc-integration-v6`（基点 = v5 head `70d670c`）；origin/master 以 Git
  查询为准（本轮 fast-forward 集成，仅 FF，无 force/merge/rebase）；`v0.1.0` tag 未动。
- 基线提升：G2 将人工冻结的 v5 Consumer UI 提升为 canonical visual baseline
  （`docs/reports/V020_RC_VISUAL_BASELINE_MANIFEST.md`，24 张 consumer PNG + 断言对齐
  冻结 v5 DOM；Admin 零改动；视觉确定性 59/59 ×2 PASS）。
- 跨运行时：Android FAST（复用 emulator-5554 / AVD main，API 36）12 张截图全 PASS；
  Windows Smoke（真实 Tauri v2 + WebView2 154）9 张截图全 PASS；release-like H5 /
  Windows NSIS / Android APK+AAB 产物记录于 `artifacts/rc-v020/RC_ARTIFACT_MANIFEST.json`
  与 `docs/reports/V020_RC_ARTIFACT_REPORT.md`（signing 受限如实记录，不假签）。
- 机器 Gate（本轮实测）：vue-tsc PASS；client-h5 build PASS；admin build PASS；
  eslint 0；prettier PASS；ui-oracle compare 398/0/0 + 捕获套件 PASS（serial 稳定）；
  语言扫描 28 页 FAIL=0；density 21 FAIL=0；ui-reconstruction 180/180；
  Playwright e2e **189/189**；visual regression **59/59**；backend pytest
  **961 passed / 2 skipped / 0 failed**（含 Celery worker，petaccess_test DB）；
  secret scan 0 findings；dependency audit 0 known vulnerabilities；
  engineering gate **PASS（0 FAIL）**——v5 遗留 15 个 vue>200 冻结 Consumer 组件
  按仓库机制登记 TD-030（RC 轮禁止重构冻结 UI，拆分排 release 后）。
- G4 收口：Consumer 复制终扫 15 路由 0 命中；修复 2 处用户可见工程痕迹
  （地图覆盖提示 `信息不足 ≠ 允许` → `不等于允许`；设置页 `with_pet` 裸 key →
  `带宠出行`），并回归重建受影响 baseline。
- 本轮不创建 tag / 不发布 Release / 不上商店（`CREATE_V020_TAG = NO`；
  最终状态 `V020_RC_READY = YES`，发布动作等待用户授权）。

### 历史记录 — v0.2.5 Human Visual Closure（2026-10-01，HISTORICAL）
## Current phase（2026-10-01 本轮实测 — v0.2.5 Human Visual Closure / Interaction & Brand Polish 全量机器管道）
- 状态：`UI_HUMAN_CLOSURE_V5 = MACHINE_PASS` · 七页 `*_CANDIDATE = READY_FOR_HUMAN` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN` ·
  `VISUAL_BASELINE_PROMOTED = NO` · `MASTER_MERGED = NO`
  （不得写作 `UI_HUMAN_VISUAL_ACCEPTANCE = PASS` / `UI_VISUAL_CLOSURE = PASS`）
- 分支：`feat/ui-human-closure-v5`（基点 = v4 head `e5a9949`）；feature branch pushed；
  最终分支 HEAD 以 Git 查询为准（文档不自我引用 HEAD）。
  origin/master = `842c030` **未动**（不 merge、不 fast-forward master，等人审 PASS 后另行请求）；
  `v0.1.0` tag 未动；无 force push / 无历史改写 / 未更新 `tests/visual/**-snapshots/*.png`
  （`git diff <v4-base>..HEAD --stat tests/visual/` 为空）。
- 方法：Human Visual Closure v5 —— 不使用任何视觉模型/OCR/截图理解；依据 v0.2.5 规格
  （§1–61 文字化人工反馈）做交互与品牌打磨；Oracle 只新增 §46 的 8 个 FAIL 级 gate
  （PLACE_NO_STRAY_GLYPH / PLACE_NO_ENGINEERING_INVARIANT_COPY / PLACE_RULE_GROUP_HAS_CONTEXT /
  PLACE_MOBILE_OVERVIEW_SUMMARY_PRESENT / MAP_MOBILE_SHEET_OVERLAY / MAP_MOBILE_SHEET_ABOVE_TABBAR /
  CONTRIBUTION_STEP_CONTEXT_PRESENT / CONTRIBUTION_OPTION_ROWS_NOT_PILLS），O1–O6 保留。
- 机器 Gate（final）：11 契约 **TOTAL PASS=398 WARN=0 FAIL=0**（含新增 map.mobile 契约 +
  8 个新 gate；v4 的 3 个 WARN 项本轮已清零）；语言扫描 28 页 FAIL=0（含 §48 禁词
  ≠/UNKNOWN/ALLOWED/PROHIBITED/CONDITIONAL/source_id/rule_id/zone_type 用户可见 DOM 0 命中）；
  density 诊断 21 行 FAIL=0（与 compare gate 对齐）。
- 页面实施：Place P0 收口（Rule Groups 带回文章节、Unknown Overview 最小化、mobile
  Space/Evidence summary row、Inspector 去重）/ Map Mobile overlay bottom sheet（half/
  expanded/peek 三态、segmented 地图|列表）/ Contribution Step Shell（place context +
  3-segment progress + radio option rows + reality cluster 表单 + Done copy）/ Search/Home/
  Reality/Evidence 打磨 / 全局一致性（Top Context Bar h60、rail blue-tint、reduced-motion）。
- 人审包：`artifacts/ui-human-closure-v5/HUMAN_REVIEW/`（§42 清单 **27 张全部 VALID** +
  HUMAN_REVIEW_INDEX.html；metadata actual 全部来自真实 DOM，O6 延续；metadata 只证明
  真实状态，不宣称视觉通过）。**等待用户人工视觉签字，Agent 不替代视觉 PASS。**
- 回归（本轮实测）：vue-tsc PASS；client-h5 build PASS；admin build PASS；eslint 0；
  prettier check PASS；ui-oracle probe + human-review v4/v5 全绿（final）；
  ui-reconstruction 180/180（responsive 8 断点 360/390/430/768/1024/1280/1440/1920 +
  a11y + phase gates + leakage）；Playwright e2e **189/189 ×2 全绿**（含 v5 §15 断言对齐、
  wizard 确定性 token boot、UUID 幂等键修复并行 409、reality 提交错误显式化）；
  backend pytest **961 passed / 2 skipped / 0 failed**（含 Celery worker，petaccess_test DB）。
- 本轮不产生 Android FAST / Windows Smoke 报告（人审门通过后的后续轮次；
  ANDROID_FAST = NOT_REQUIRED · WINDOWS_SMOKE = NOT_REQUIRED）。

### 历史记录 — v0.2.4 Blind UI Productization（2026-10-01，HISTORICAL）
## Current phase（2026-10-01 本轮实测 — v0.2.4 Blind UI Productization 全量机器管道）
- 状态：`BLIND_UI_PRODUCTIZATION_V4 = PASS` · `UI_MACHINE_PRODUCTIZATION = PASS` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN`
  （不得写作 `UI_VISUAL_CLOSURE = PASS`）
- 分支：`feat/blind-ui-productization-v4`（基点 `feat/blind-ui-compiler-v2 @ 90d57e6`，
  先行 28 / 落后 0）；实现基准 `IMPLEMENTATION_BASE = e1c5ca7`（代码与测试完成后的实现 commit）；
  feature branch pushed；最终分支 HEAD 以 Git 查询为准。
  origin/master = `842c030` **未动**（不 merge、不 fast-forward master，等人审 PASS 后另行请求）；
  `v0.1.0` tag 未动；无 force push / 无历史改写 / 未更新 `tests/visual/**-snapshots/*.png`。
- 方法：Blind UI Productization v4 —— 不使用任何视觉模型/OCR/截图理解；依据 v0.2.4 规格
  （§1–64 文字化人工反馈 + 可执行 UI contract）改代码；Oracle 仅最小修正
  （阈值/作用域修正 + 当前反馈所需少量 contract + minVisibleInViewport 探针；O1–O6 保留）。
- 机器 Gate（final）：10 契约 **TOTAL PASS=368 WARN=0 FAIL=0**（原 3 个 WARN 升级项
  PLACE_HISTORY_COLLAPSED_MOBILE / PLACE_SECTION_GAP / PLACE_MOBILE_FIRST_VIEWPORT_LINES
  按新阈值执行，违反一律 FAIL）；语言扫描 26 页 FAIL=0。
- 页面实施：Search / Place / Home / Map / Reality / Evidence / Contribution 七页按
  v0.2.4 产品化规格落地（Place = Dossier with Views：`?view=` 本地导航、Overview 五块、
  长度门 desktop<=1500/mobile<=2000、mobile 首屏<=22 行、section gap<=40、去重、Unknown 收口）。
- 人审包：`artifacts/blind-ui-productization-v4/HUMAN_REVIEW/`（phase-a-search 4 /
  phase-b-place 5 / phase-c-home-map 5 / phase-d-rest 10 = **24 张全部 VALID** +
  HUMAN_REVIEW_INDEX.html；metadata actual 全部来自真实 DOM，O6 延续）。
  **等待用户人工视觉签字，Agent 不替代视觉 PASS。**
- 回归（本轮实测）：vue-tsc PASS；client-h5 build PASS；admin build PASS；eslint 0；
  prettier check PASS；ui-oracle probe + human-review 全绿（final）；
  ui-reconstruction 180/180（responsive 1440×900 / 430×932 + a11y + phase gates + leakage）；
  Playwright e2e **189/189**（含修复 mode-switch 重算、lens headline、并行 hash goto 加固）；
  backend pytest **961 passed / 2 skipped / 0 failed**（含 Celery worker，petaccess_test DB）。
- 本轮修复（WIP 阶段发现）：presence lens `row-lens-headline` 应为 reality 行（非 decision）；
  PlaceView 恢复 session mode watch（模式切换重算）；Contribution 步骤指示 5/3 → 2/3。
- 本轮不产生 Android FAST / Windows Smoke 报告（人审门通过后的后续轮次）。

### 历史记录 — v0.2.3 Blind UI Compiler v2（2026-10-01，HISTORICAL）
# PROJECT_STATE.md

## Current phase（2026-10-01 本轮实测 — v0.2.3 Blind UI Compiler v2 全量机器管道）
- 状态：`BLIND_UI_COMPILER_V2 = PASS` · `UI_MACHINE_CONTRACT_ACCEPTANCE = PASS` ·
  `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING` · `UI_VISUAL_CLOSURE = PENDING_HUMAN`
- 分支：`feat/blind-ui-compiler-v2`；HEAD = `03ec482`（自 `e724f1c`，16 commits，已 push）；
  origin/master = `842c030` **未动**（不 merge、不 fast-forward，等人工视觉确认后另行请求）；
  v0.1.0 tag 未动；无 force push / 无历史改写 / 未删除既有 worktree。
- 方法：Blind UI Compiler v2 —— 不使用任何视觉模型/OCR/截图理解；六层 Oracle
  （O1 语义 / O2 几何 / O3 相对层级 / O4 内容预算 / O5 构图 / O6 状态完整性）+ Capture
  State Integrity + Executable Blueprint。见 `docs/ui/BLIND_UI_COMPILER_V2_METHOD.md`。
- 机器 Gate（final）：10 契约 **TOTAL PASS=332 WARN=3 FAIL=0**（3 WARN 均为既有
  place.mobile 容忍项：PLACE_HISTORY_COLLAPSED_MOBILE / PLACE_SECTION_GAP /
  PLACE_MOBILE_FIRST_VIEWPORT_LINES）；语言扫描 24 页 FAIL=0（uuid/enums/invariants/
  allcaps/refs 可见命中 0）。产物 `artifacts/blind-ui-compiler-v2/reports/*`。
- 页面实施：Search / Place / Home / Map / Reality / Evidence / Contribution 七页按
  v0.2.3 蓝图实施并全过机器门禁（phase A–D）。
- 人审包：`artifacts/blind-ui-compiler-v2/HUMAN_REVIEW/`（phase-a-search 4 /
  phase-b-place 3 / phase-c-home-map 2 / phase-d-rest 7 = **16 张全部 VALID** +
  HUMAN_REVIEW_INDEX.html，metadata actual 全部来自真实 DOM）。**等待用户人工视觉
  签字，Agent 不替代视觉 PASS。**
- 回归（本轮实测）：client-h5 vue-tsc+build PASS；eslint 0；prettier 3.9.6 PASS
  （repo-wide LF + format pass，独立 style commit，无语义变化）；Playwright e2e 串行
  189/189（并行 contribute-wizard TEST-001 懒加载 flake 既有，单跑绿）；ui-oracle
  probe+human-review 12+2 passed；ui-audit 70/70；visual 59/59（consumer 基线按蓝图
  重生成 24 张，admin 未动）；ui-reconstruction 串行 180/180；backend pytest
  **961 passed / 2 skipped / 0 failed**（含 Celery worker；adb.py 修复 ANDROID_HOME
  解析，Android 工具链 15/15）。
- 本轮不产生 Android FAST / Windows Smoke 报告（人审门通过后的后续轮次）。

### 历史记录 — v0.2.1 Visual Fidelity Recovery，Phase A（2026-09-28，HISTORICAL）

## Current phase（2026-09-28 当前会话实测 — v0.2.1 Visual Fidelity Recovery，Phase A: Search + Place）
# 状态重置（Goal §2）：UI_VISUAL_FIDELITY = FAIL · UI_CONSUMER_LANGUAGE = FAIL（Phase A 页面已清零，Reality/Evidence 属 Phase C）· UI_HUMAN_VISUAL_ACCEPTANCE = FAIL · UI_VISUAL_CLOSURE = REOPENED
# Phase A（Search/Place 桌面+移动）已完成实现与自动化门禁，真实截图见 artifacts/visual-fidelity-recovery/phase-a/ 与 VISUAL_FIDELITY_REVIEW.html；HUMAN_VISUAL_GATE_A = PENDING，见 docs/reports/VISUAL_FIDELITY_PHASE_A_REPORT.md
# 历史「UI_RECONSTRUCTION 全矩阵闭环」为 PRE-INTEGRATION / HISTORICAL 记录，不再作为当前视觉状态。
# 上游：v0.1.0 Early Preview — 已发布（2026-09-24）｜v0.2.0 M1–M8 已完成（HISTORICAL）

## UI Reconstruction 收口（2026-09-28 全实测, HISTORICAL / PRE-INTEGRATION — 当前视觉状态以顶部 v0.2.2 章节为准）
- 定位：M3.1 Consumer Contract 关闭（G1 五项全 PASS）+ Home/Search/Map/Place/Reality/Evidence/Contribution 七页按 v0.10-R1 Canonical Master + Approved Reference 重构为 Spatial Dossier（空间档案式）成熟工具。
- Canonical master 与 Approved Reference PNG 已随分支提交（commit 5af0020），非 untracked。
- G1（M3.1）消费契约 5 项 PASS（COEXISTENCE_SNAPSHOT_SSOT / TRANSPORT_ERROR_CACHE / SNAPSHOT_CACHE_KEY / OFFLINE_STALE_WIRING / LENS_SEMANTICS），回归测试 tests/e2e/consumer-contract-closure.spec.ts 全绿。
- 工程门禁（本轮实测）：backend pytest **961 passed / 2 skipped**；vue-tsc / client-h5 build / admin build / eslint / prettier 全 PASS；Playwright e2e **189 passed**（响应式矩阵扩至 8 页 × 9 viewport）；ui-reconstruction capture（final stage）**90/90**；phase1+phase3 gate 45/45；a11y gate **30/30**；responsive 72/72。
- 文件体积遗留已处理：HomeView 199 行 / MapView 203 行 / EvidenceView 263 行（composable + 子组件拆分，prettier 幂等）。
- Android FAST（真实模拟器 pdig36，端口 5556）：Install/launch/Home/Search(7 条真实结果)/Map/Place/navigation/offline/recovery/short-lifecycle **全 PASS**（WebView CDP DOM + 设备层截图证据；修复了 C: 盘 1.3GB 可用不足；从未 adb kill-server）。见 docs/reports/UI_RECONSTRUCTION_ANDROID_FAST.md。
- Windows smoke（真实 Tauri WebView2 runtime）：build 2m52s → petaccess.exe；launch/Home/Search/Map/Place/navigation/offline/recovery 全 PASS（CDP + UI Automation 证据）；不再是 stretched H5。见 docs/reports/UI_RECONSTRUCTION_WINDOWS_SMOKE.md。
- 视觉审计：结构断言 + 像素级证据全过；90 张 final 截图 + UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html（90 格）可直接打开。当时 `UI_VISUAL_CLOSURE = PASS（自动化证据）` 已按本轮 v0.2.2 契约修正为 **HISTORICAL**；人工目视复核见本轮 `artifacts/blind-ui-recovery/HUMAN_REVIEW/`（等待用户签字，`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`）。
- 遗留（tracked）：TEST-001 contribution-wizard 并行 flake（既有冻结语义，单跑/重跑均 PASS）；Android WebView uiautomator 文本可见性 PLATFORM_LIMITED（既有，非缺陷）；artifacts/ 目录 gitignored（工作区证据）。
- LOCAL git：分支 `feat/ui-reconstruction-spatial-dossier`（commit：5af0020→567e42e→8b7e245→fa2b368→ec8af2c→2fcf241→4fc21ba→af25ee6→7404155）；origin/master `434efd3` 未变（0 divergence，纯 fast-forward descendant，按 AC-G1 四条件 FF 集成并 push）。v0.1.0 tag 未动。

## M3 深化收口基线（历史记录 — 2026-09-27，保留作 provenance）

## M3 深化收口基线（2026-09-27 全实测, CURRENT VERIFIED — 见 docs/reports/V020_M3_FINAL_REPORT.md）
- 定位（用户确认）：M3 深化收口——基于现有实现做 UI/UX 全量设计收口，不吞并 M4/M5/M7；Canonical Master = v0.10-R1（2026-09-27）。
- 方向 FREEZE：Structured Utility（Calm/Neutral/Urban/Evidence-first）；DESIGN.md + docs/ui/V020_M3_UI_DIRECTION_DECISION.md；候选 A/C 归档 artifacts/ui-audit/concepts/。
- Consumer 架构：新增 consumer/{cache,repository,rowView}.ts — bounded concurrency（Search 原 N×无界 Promise.all → 4 worker）+ ConsumerCache（TTL/stale/offline/coalesce）+ request epoch（race 保护）+ transport error ≠ domain fact（answerError/realityError 显式）。
- CoexistenceSnapshot SSOT：Search/Home 行级 Reality+Freshness+Evidence（PlaceResultRow）；无页面级第二套 Rule/Reality truth。
- Home/Search/AppShell：移除旧 AppShell 双层 chrome（Home/Search 直接 ConsumerAppShell 框架）；行级信息 = identity→Rule→Reality→Freshness/Evidence；桌面 wide/split 分层。
- 测试（本轮实测）：backend pytest **961 passed / 2 skipped**；vue-tsc/build/eslint/prettier 全 PASS；Playwright e2e **157/158**（1 = 既有 TEST-001 flake，stash 到基线 HEAD 复现同样失败、单独跑 3/3 绿，与 M3 无关）；visual **59/59**（12 张 consumer 基线按 M3 视觉重生成）；新增 m3-consumer-core.spec（5 tests）全绿。
- 截图取证：current（BEFORE）70 张 + m3-final（AFTER）70 张 + UI_CURRENT_STATE_GALLERY / UI_M3_FINAL_GALLERY / UI_M3_BEFORE_AFTER_GALLERY（140 图 0 broken）；根目录 artifacts/ui-audit/。
- Android FAST：PASS（launch/home/search 21 results/nav/offline/recovery/short lifecycle，debug APK CDP DOM 证据；见 docs/reports/V020_M3_ANDROID_FAST_REPORT.md）。
- Windows smoke：PASS（NSIS install/launch/home/search/split-preview/navigation/offline/recovery，截图 + accessibility 树；见 docs/reports/V020_M3_WINDOWS_SMOKE_REPORT.md）。
- 遗留（tracked）：TEST-001 contribution wizard 并行 flake（既有冻结；基线复现）；Home/Search 文件体积 >300 行（既有大型页面，数据逻辑已抽 repository，M4 可继续拆）；Android WebView uiautomator 文本可见性 PLATFORM_LIMITED（既有）。
- LOCAL git：baseline 049fc39；M3 分支 feat/v020-m3-consumer-core（8 commits）；origin/master 5b1dd05 未变（纯 fast-forward descendant，待最终 FF 集成与 push）。

## Current phase（历史记录 — 2026-09-25 M8 基线，保留作 provenance）

## 取证审计基线（2026-09-26 全实测, CURRENT VERIFIED — 见 docs/forensics/）
- 结论：PETACCESS_GLOBAL_FORENSIC_AUDIT = PASS（FINAL_ROOT_CAUSE_REPORT.md / GLOBAL_CODE_AUDIT_FINAL_REPORT.md；F00–F13 全量落盘）
- 三矩阵（F03）：A=GitHub Release v0.1.0（SHA256 e236f193…）／B=v0.1.0 重建／C=HEAD，同机同 SDK 同 emulator 统一 adb 全链 PASS；情况 4 判定（A/B/C 全 PASS）→ 原始异常归因为环境/自动化（ADB churn REG-001、PS 截图编码 REG-002、并发会话 REG-005、ASCII 路径 REG-007），非 boot/渲染代码回归
- 产品缺陷修复（REG-003，commit 1d93942）：packaged API base 按运行形态解析（endpoints.ts），不再依赖 Vite proxy；CSP 最小 +10.0.2.2（Android 模拟器 dev）
- Backend pytest：**945 passed / 2 skipped / 0 failed**（修复后重跑与传统基线 938/944 均为历史值）
- Engineering gate：0 FAIL / 60 REVIEW / 34 WARN；ruff / format PASS（299 文件）；mypy 96 files / 0 errors；secret scan 0 findings；alembic 单头 e9f2c1d4a5b6（downgrade→upgrade 链实测通过）
- H5+Admin build PASS；Playwright e2e **149 passed**（全量重跑确认；contribute-wizard B2 并行抖动已加固）
- Windows 运行时 PASS（NSIS install/launch/窗口/relaunch/uninstall 全清）；Android 终态门禁 PASS（A→修复版同签名升级、PETACCESS_BOOT 5 阶段链 logcat 实证、uninstall 后设备干净）
- 遗留（tracked）：FF-003/FF-004/FF-006/FF-007（维护性债务，见 FORENSIC_FINDINGS_REGISTER.md）；M3_RESUME_ALLOWED = YES（恢复条件已满足，恢复动作由用户决定）

## v0.1.0 状态
- **V0_1_0_RELEASED = YES（2026-09-24 已发布 https://github.com/huangdi97/petaccess/releases/tag/v0.1.0）**
- **HUMAN_ACTION_REQUIRED = 无**（RELEASE_V0_1_0_AUTHORIZATION 已由 huangdi97 于 2026-09-24 授权并完成发布）
- GitHub 阶段 DONE：remote=origin（huangdi97/petaccess）；tag v0.1.0；GitHub Release 已发布（Early Preview，非 Public Beta）；双产物已重下载并通过 SHA256/签名/安装校验（Phase AH）
- 发布就绪门槛全部实测 PASS（见 docs/release/V010_RELEASE_READINESS_REPORT.md）
## 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- pytest 938 passed / 2 skipped（TEST DB + Celery worker）
- ruff / format PASS；mypy services/api/app 93 files / 0 errors
- Engineering gate：0 FAIL / 60 REVIEW / 26 WARN；§40 四新项（silent-catch / magic-status / dead-code / duplicate-config）已接入 collect()，修复后 RESULT: PASS
- Secret scan（worktree + history）：0 findings
- VERSION_DRIFT = 0（scripts/check_version_drift.py，含 design-tokens 0.6.0-beta.1→0.1.0 修正）
- H5 + Admin vue-tsc + build PASS；Playwright E2E 21 passed（18 + 3 empty-state）
- Visual 47 PASS（17 基线家族 × viewports；Empty-First 文案改动后基线重生成一次，compare 全绿）
- A11y：0 issues（consumer + admin 全页, 键盘焦点走查 0 invisible）
- 依赖扫描：pip-audit / pnpm audit 均 0 known vulnerabilities（Critical=0 / High=0）


## v0.2.0 M3 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Route/query foundation：404 catch-all + NotFoundView、route meta.title（afterEach）、scrollBehavior；Search 深链 ?q=/?lens= 回填、back/forward 同步（e2e A1/A3/B1/B2 全绿）
- CoexistenceSnapshot 统一消费兑现（ADR-029）：Search 桌面 split-view（PlacePreview 第一轮，client.coexistenceSnapshot），行级 rule 摘要收敛为共享 ruleSummaryLabel；PlacePreview 纯 props 呈现、无第二套模型
- 统一错误呈现收口：新增 presentDescription（errors.ts）；Home/MatchExplain/Mine 接线 StateMessage；e2e E2 断言页面不泄漏 SQLAlchemy/FastAPI/psycopg2 等内部字样
- E1 视图状态守卫扩展：REQUIRED_PER_VIEW 覆盖全部数据驱动视图 + DECLARED_STATIC（@ui-static/@ui-form 显式声明），断言每个路由视图必须落入其一（unit 8 passed）
- A11y：M3 新增/变更面 axe 0 critical / 0 serious（顺带修复桌面 rail 版本标签对比度）；移动端 6 家族复扫 0/0
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 29 WARN；ruff / format PASS；mypy 96·0；backend 回归 DISCOVERED 946 = 944 passed / 2 skipped / 0 failed；e2e 75 passed；visual 42 passed；eslint / prettier PASS；H5 + Admin build PASS
- 后端零改动；性能无退化（SearchView 10.0 kB，+0.1 kB split 逻辑）

## v0.2.0 M4 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Map 桌面 split-view（DesktopContentContainer split：地图 + PlacePreview 详情面板）+ `/map?place=` 深链与 back/forward 同步（e2e A1/A4 全绿；visual map-split 家族）
- Map 状态收口：empty（EMPTY_STATE_COPY.MAP + 返回首页）、error 走 presentError（修复原始泄漏）、offline 由 shell GlobalOfflineBanner 单一承担（移除本地 banner）
- Place Passport 收口（10 段骨架未重建）：桌面阅读列（single-column）、Section 7 证据视觉语言（EvidenceStatus/EvidenceMeta/FreshnessStatus，无原始枚举上屏）、统一错误呈现（4 处 quickMsg + 主错误）；e2e B1/B2/B3/B5 全绿
- A11y：map / place 表面 axe 0 critical / 0 serious（顺带修复 ALLOWED 徽章对比度 #2e7d52→#277348，tint 上 4.38→5.06:1）；移动端 6 家族复扫 0/0
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 29 WARN；ruff / format PASS；mypy 96·0；backend 回归重跑 944 passed / 2 skipped / 0 failed；e2e 82 passed；visual 42 passed；eslint / prettier PASS
- 后端零改动；真实腾讯地图无 Key → 如实记录 BLOCKED_EXTERNAL（MockMap 交付，不假接线）

## v0.2.0 M5 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Reality Trace 独立路由 `/#/place/:id/reality`（meta.title「现场轨迹」+ 深链 + Passport RealityPanel「查看现场轨迹」CTA）；fact/review 分区渲染（sunken 表面区分，非仅颜色），note 保留
- 观察时间线（client.observations：时效/动物范围/动作/工作人员/note/争议）+ 空态 REALITY copy；状态完备（SkeletonList/StateMessage/presentError/shell offline）
- 统一 Evidence 呈现：EvidenceStatus（dispute 映射 verified/pending/disputed/historical）+ EvidenceMeta + freshness，无原始枚举上屏（顺带修复 RealityPanel 原 verification 枚举泄漏）；规则 provenance 留 Passport §7 未复制
- A11y：trace 页（桌面+移动）axe 0 critical / 0 serious
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 30 WARN；ruff / format（470 文件）PASS；mypy 96·0；backend 回归重跑 944 passed / 2 skipped / 0 failed；e2e 87 passed；visual 45 passed；eslint / prettier PASS
- 后端零改动；无新架构决策
## v0.2.0 M7 质量基线（2026-09-25 全实测, CURRENT VERIFIED）
- 贡献向导重建（769 行旧单体 → 171 行编排器 + 8 个步骤组件，全部 vue ≤200）：entry/quick/signage/rule/experience/reality/done 7 步状态机；placeId+signedIn 门禁（未选场所/未登录双 CTA）；TD-015 豁免关闭
- 现实贡献走父流 createRealityReport（candidates + effort + privacy private，ADR-029）；规则/拍照/快速确认保持旧端点不迁移
- 贡献历史：新端点 GET /api/v1/me/reality-contributions（仅本人数据 50 上限，匿名 401，复用 RealityReport/RealityCandidate 无新模型）+ MineView「我的贡献」区块（CANDIDATE_TYPE_LABELS/CONTRIBUTION_STATUS_LABELS 字典，无原始枚举上屏）
- A11y：contribute 全态（signed-out/entry/reality-form 桌面+移动）+ mine axe 0 critical / 0 serious（顺带修复全部表单 label/select 程序化关联）
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 34 WARN；ruff / format PASS；mypy 96·0；backend 回归重跑 945 passed / 2 skipped / 0 failed（+1 贡献历史集成测试）；e2e 90 passed（+3 contribute-wizard）；visual 59 passed（contribute-h5-390 重生成）；eslint / prettier PASS；client-h5 build PASS
- 后端改动仅 1 新端点（UI 所需 contract gap）+ 集成测试；死代码豁免新增仅 TD-028 decorator-registered 类别
## v0.2.0 M8 质量基线（2026-09-25 全实测, CURRENT VERIFIED）
- Windows DPI 矩阵收口（M2 §7 延期项）：新增 tests/e2e/desktop-dpi.spec.ts，3 物理分辨率 × DPI 100/125/150% = 9 组（逻辑 CSS 视口 = physical/scale + deviceScaleFactor 模拟），×6 主页面 54 条：渲染非空/无横向溢出/desktop-rail 可见/DSF 实际生效
- 真实壳冒烟：tauri build（vcvars+MSVC）1m25s → petaccess.exe + NSIS 安装包；install/launch（WebView2 子进程渲染确认）/relaunch/uninstall 全 PASS；产物 artifacts/v0.2/PetAccess_v0.2-desktop_x64-setup.exe（SHA256 be1e8c6a…）
- Android 模拟器冒烟并入 M8（用户拍板）：worktree reset 至 master → tauri android build（补装 platform-36/build-tools-36）→ apksigner release 签名 → emulator API35 install/launch（截屏 2743 色真实渲染）/force-stop/relaunch（2753 色）/uninstall 全 PASS；PetAccess_v0.2-android-universal.apk（SHA256 c1600cc9…）
- 门禁全绿：eng gate 0 FAIL / 60 REVIEW / 34 WARN；ruff / format PASS；mypy 96·0；backend 回归重跑 945 passed / 2 skipped / 0 failed；e2e 144 passed（+54 DPI 矩阵）；visual 59 passed；eslint / prettier PASS（eslint.config.js projectService 上限 20→25，非豁免）
- 壳配置审计无变更（窗口 1000×760 / min 640×480 / CSP deny-by-default / capabilities 仅 core:default）；tauri.conf 版本号沿用 0.1.0，v0.2.0 发布轮再升
## v0.2.0 M2 质量基线（2026-09-24 全实测, CURRENT VERIFIED）
- Engineering gate：0 FAIL / 60 REVIEW / 28 WARN（PASS）；ruff / format PASS；mypy 96 files / 0 errors
- Backend pytest 全量重跑：DISCOVERED 946 = PASSED 944 / SKIPPED 2 / FAILED 0（TEST DB + Celery + MinIO）
- H5 + Admin vue-tsc + build PASS；ESLint / Prettier PASS（29 个 M2 文件补 prettier，见工程报告 §6）
- Playwright e2e 70 passed；Visual 42 passed（14 基线家族 × 390/768/1440，a11y 修复后重生成）
- A11y（axe-core 4.10 六家族机器扫描）：0 critical / 0 serious
- 性能基线（§50）：main 134.39 kB（gzip 51.94）；HomeView 10.19 kB；SearchView 9.99 kB；记录于 V020_M2_ENGINEERING_REPORT.md
- Windows Tauri / Android 真机 DPI QA：PARTIAL（推迟 M8/M9），见工程报告 §7
- 8 份 §56 交付文档齐备（docs/v0.2/）；DECISIONS.md 记录 ADR-031（DEV_FIXTURE_MODE fail-closed）

## v0.1.0 产品（Early Preview, Empty-First）
- 允许数据为空：Places/Rules/RealityClaims/StaffResponses/AnimalFacilities = 0 也完整可用
- Home「当前还没有已发布的场所数据」+ 探索地图/贡献线索；Search「没有找到已收录场所」
- 不变量：UNKNOWN ≠ ALLOWED；Observation ≠ Rule；AI ≠ final judge；无 fake 数据入 release

## 平台产物（实测构建并冒烟）
- Windows：`artifacts/v0.1.0/PetAccess_0.1.0_x64-setup.exe`（NSIS, 未签名→SmartScreen 提示）
  install→launch→relaunch→uninstall 冒烟 PASS（WebView2 渲染确认）
- Android：`artifacts/v0.1.0/PetAccess_0.1.0-android-universal.apk`（release keystore 签名 v2/v3,
  com.petaccess.map, versionName 0.1.0, versionCode 1000, minSdk 24, 仅 INTERNET）
  模拟器 API 35 冒烟 PASS（install→launch 实拍渲染→relaunch→uninstall）
- SHA256SUMS.txt 双产物逐项校验一致

## 架构
- UI（Vue3+H5/Admin, design-tokens）→ App（client-core）→ Domain（FastAPI app/）→ Ports
- Infrastructure implements Ports；dependency cycles = 0（gate 检测）
- Tauri 2 壳（src-tauri, additive）：仅 window/lifecycle/IPC/security；Domain 不写入 Rust
- Provider 全部 interface + adapter（map/ai/ocr/storage/notification, 默认 mock）

## CI
- .github/workflows/pr-ci.yml（M1, committed）+ release-ci.yml（M9/M10, committed）
- 远程 CI 未执行：BLOCKED（无 remote, 发布未授权）— 不得伪造 PASS

## 环境备注
- Docker Desktop 29.2.1（WMI 持久启动）；postgis 17 + redis + minio healthy
- Celery worker（Redis db 1, queue petaccess_test）供 test_media/test_v05_e2e 消费
- Rust 1.97.1 + 便携 VS2022 MSVC（D:）经 vcvars 环境构建
- Android 构建需 ASCII 路径：仓库路径含 CJK 触发 AGP 拒绝 → 使用 git worktree
  C:\petaccess-worktree（记录于 V010_ANDROID_REPORT.md）

## Blocker / 下一步
- **v0.1.0 已发布（2026-09-24）**；RELEASE_V0_1_0_AUTHORIZATION 已授权并完成：remote + tag + Release CI 全绿 + GitHub Release + 重下载 SHA256/签名/安装校验全 PASS
- 远期（非 v0.1.0）：真实地图 key / AI key / 数据扩充 / 商店上架 / Public Beta 数据版

## Truth rule
Never infer PASS。
