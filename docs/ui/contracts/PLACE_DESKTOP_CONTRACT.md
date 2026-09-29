# Place Desktop Contract

> 目标 viewport：1440 × 900。JSON：`docs/ui/contracts/json/place.desktop.json`。
> 结构：Rail → Top context → Main dossier（65–72%）→ Sticky decision inspector（300–360px）。

## 1. Layout 比例

| region | 约束 |
|---|---|
| app-rail | width 64–72px |
| place-main-dossier | 占可用宽 65–72% |
| place-inspector | width 300–360px（token `--pa-layout-inspector` = 320）；sticky，top = context bar + 20–24px |

Inspector 不得只有几行文本漂在右上角；不得复制整个 dossier。

## 2. Identity block（首屏）

- Place name 28–30px（`--pa-font-size-30`，weight 600–700）；
- type · address 等 metadata 13–14px；
- 1–2 个 secondary action（禁止一排 4–6 CTA）。

## 3. Current Decision（Main dossier 第一核心 section）

- Current context（查询）
- Decision（primary，26–32px）
- 1–3 个 key conditions
- source / freshness
不折叠。普通消费者不用看完整 domain schema。

## 4. Progressive Disclosure

首屏/主流程优先：Current Decision → Recent Reality → Space / Zones → Rule Summary → Evidence Summary。
折叠/二级：Historical versions、superseded rule history、debug provenance、internal identifiers、长原始 boundary details。

## 5. Section gap

section ↔ section：24–32px。

## 6. Zone row（消费者显示）

- `一层公共区域` / `餐饮堂食区` / `户外区域`（层语义可以前缀数字）；
- 禁止裸显 `1F / floor / pet_area / dining_area`（仅允许在不可见 data attribute）。
- zones = divider rows，不是卡片。

## 7. Sticky Inspector 内容（最多 5–6 group）

Current Query / Primary Status / Required Conditions / Major Exception / Primary Source / Freshness。
不显示：长历史、raw fields、UUID、占位空。

## 8. 语言 / 密度 / A11y

- UUID / snake_case / internal enum / engineering invariant visible = 0；
- 页面首屏信息块 ≥ 4；最大语义间隔 ≤ 180px；
- 单一 h1；status 非纯色。