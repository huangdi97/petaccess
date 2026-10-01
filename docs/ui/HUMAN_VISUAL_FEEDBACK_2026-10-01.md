# Human Visual Feedback — 2026-10-01（v0.2.4 文字化人工反馈清单）

> 本文档收录规格 `PetAccess v0.2.4 Human Visual Recovery / Productization Closure（2026-10-01）`
> 中**文字化人工视觉反馈**的浓缩清单，以及本轮对应的代码处理与验收结果。
> 实现基准：`IMPLEMENTATION_BASE = e1c5ca7`。
> Agent 不评价截图；以下“反馈”全部来自文档中的文字描述，不是 Agent 的视觉判断。

## 1. 反馈 → 处理对照

| § | 文字化反馈（摘要） | 处理 | 结果 |
| --- | --- | --- | --- |
| §9/§45 | 整页米黄、暖色滥用；surface 收口 | tokens 去黄：bg-app `#F8F8F7`、surface 白；warm tint 仅限 conditional region | compare global PASS |
| §11–12 | Search 顶部 duplicate status badge；右侧结构松散 | 删除 duplicate badge；detail 严格 §12 顺序（Identity→Query→Decision→Reality→Evidence→CTA） | search.desktop PASS=52 |
| §13 | mobile 独立 Filter button + 结果数两行 | 合并 toolbar（结果 N \| 筛选） | search.mobile PASS=38 |
| §14 | empty 用大卡 | inline empty，无 card/shadow | PASS |
| §15 | Place 3000px+ 无限长 | Dossier with Views（本地 section 导航 + `?view=`） | place PASS |
| §16 | Overview 长度不可控 | 五块 + desktop 才渲染的块 | desktop 1181px PASS |
| §22 | Space 信息平铺 | 独立 Space view（zones + extras） | PASS |
| §23 | 历史版本平铺 | 折叠（progressive disclosure） | PLACE_MOBILE_HISTORY_COLLAPSED PASS |
| §24 | 第二套 Reality UI | 复用 RealityEventLog | PASS |
| §25 | 复制来源表 | 复用 Evidence Record/Provenance | PASS |
| §26 | Inspector 内容散 | 内容固定（当前查询/Decision/…/CTA） | PASS |
| §27 | Unknown 空 section 全家福 | 只渲染有数据部分 | place-unknown VALID |
| §28 | mobile 首屏 38 行 | 首屏 = Place+tabs+Decision+Reality teaser，`<=22`（>24 FAIL） | 22 PASS |
| §29–31 | Home 大白 card、pending card rows、为什么？ pill | max 960；divider rows；4 lenses | home PASS |
| §32 | desktop 地图/列表顶部 pill | desktop 恒为 List+Map，删除 pill | map PASS |
| §33 | mobile bottom sheet 与 tabbar 重叠 | 位于 tabbar 上方、3–4 行 | PASS |
| §34 | Reality timeline 被推到首屏以下 | Timeline-First；页顶只允许 title+说明+筛选 | reality ready first event top 275.5px PASS |
| §36 | Reality empty 大卡 | inline empty（暂无近期现场记录） | PASS |
| §37–40 | Evidence 记录存在时标题显示“0 条依据”；场所信息暂不可用 | 解析 place/zones/time；存在记录不显示 0 条 | evidence PASS |
| §41 | Contribution choice 不足首屏 / 每行要素不全 | 5 行（icon+title+desc+chevron）64–72px，>=4 首屏 | 5/5 visible PASS |
| §42 | 隐私文案高权重整段显示 | 降权为「隐私与审核说明 →」 | PASS |
| §43 | 步骤指示不真实 | 真实 3 步（legacy=1/3，reality=2/3） | PASS（修复 5/3 问题） |
| §51 | Reality 首屏 gate | 截图从 page top capture；first event top <=360；>=1 事件可见 | PASS |
| §52 | Evidence 首屏 gate | identity + provenance 前 3 步首屏可见 | PASS |
| §53 | Contribution 首屏 gate | desktop >=4/5、mobile 932px 内 >=4 可见 | PASS |

## 2. 本轮新增修复（WIP 阶段发现，非规格新增）

- **presence lens 标题行错误**：`row-lens-headline` 在 presence/indoor/dining lens 下应显示
  reality 行而非 decision 结论；同时避免 reality 行重复渲染（§11 行预算）。
- **Place 模式切换不再重算**：PlaceView 恢复 `watch([session.mode, session.activePet]) → evaluate()`，
  普通携带 ↔ 服务犬通行切换后结论正确更新。
- **Contribution 步骤指示错误**：reality 父流程曾显示「步骤 5 / 3」，修正为「步骤 2 / 3」。
- **oracle budget 作用域**：`PLACE_MOBILE_FIRST_VIEWPORT_*` 契约只应用于 overview 页
  （首屏 = Place+tabs+Decision+Reality teaser，§28），不应用于深链 rules view。

## 3. 待人工确认项（UI_HUMAN_VISUAL_ACCEPTANCE = PENDING）

- 请打开 `artifacts/blind-ui-productization-v4/HUMAN_REVIEW/HUMAN_REVIEW_INDEX.html`（24 张）目视；
- 重点确认：Search 行高与 4 行语义、Place Dossier 五块与导航、Home 960 布局、
  Map divider rows + preview 5 项、Reality timeline 首屏、Evidence provenance rail、
  Contribution 5 choice rows 与隐私降权文案。
- 人审通过前：不更新 `tests/visual/**-snapshots/*.png`，不 merge master，不移动 `v0.1.0` tag。
