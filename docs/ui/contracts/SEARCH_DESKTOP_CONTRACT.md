# Search Desktop Contract

> 目标 viewport：1440 × 900。JSON：`docs/ui/contracts/json/search.desktop.json`。
> 结构：Rail → Top context bar → Result pane（380–420px）→ Detail pane（剩余宽度）。

## 1. Region 尺寸

| region | 约束 |
|---|---|
| app-rail | width 64–72px（token `--pa-layout-rail-width` = 68） |
| query-context（top bar） | height 56–64px |
| search-results-pane | width 380–420px（token `--pa-layout-result-pane` = 400） |
| search-detail-pane | × 由剩余宽度填充（≥ 计算值） |

## 2. Search controls

- Search input + submit 高度 44–48px；搜索行总宽 ≥ 320px。
- Clear / recent / filter 不得成为视觉主角。

## 3. Result row（每条）

- height 108–136px；border-radius 0；bottom divider 有；
- padding vertical 14–18px；
- 最多显示：1 行名称 / 1 行类型·距离·位置 / 1 行 primary decision / 1 行 primary condition 或 reality freshness / 1 行极轻元数据。
- 禁止一条内同时展示：已核验、条件、生效规则 N、现场记录、来源数、人工核验状态。

## 4. Selected row

- background subtle tint（`--pa-color-accent-weak`）；left indicator 2px accent bar；
- 不变成独立圆角卡（radius 0）。

## 5. Detail pane

- 内容最大宽 680–760px（不可拉满 900px）；
- 内容距 pane 左 32–48px；距顶部 24–32px；
- 结构固定顺序：Place Identity → Current Query → Primary Decision → Conditions → Major Exception → Recent Reality → Primary Evidence → Open Full Dossier。

## 6. Primary Decision（第一视觉锚点）

- label 12–13px；decision 28–32px（`--pa-font-size-26/30` + weight 600–700）；supporting 14–16px；
- 语义标记（左侧 accent 线 / subtle marker）。

## 7. 空间利用

- selected place 存在时，detail 内容首屏高度 ≥ 360px（不得 200px 后大片空白）。

## 8. 密度

- detail 内最大语义垂直间隔 ≤ 180px；不得出现 80–200px 无意义空洞。

## 9. 语言

- 无 UUID / snake_case / ALL_CAPS / 不变量泄漏（见 CONSUMER_LANGUAGE_CONTRACT）。
- zone 事实必须经 mapper 转译（`observed_zones` 原始值不得直接 join 上屏）。

## 10. 交互

- selected row 键盘可达；filter 为轻量 panel（桌面）或 bottom sheet（移动）；
- 旧 request 不覆盖新 context（epoch 保持）。