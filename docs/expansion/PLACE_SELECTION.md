# PLACE_SELECTION — 10 个新增场所的选取与入选理由

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 选取口径

- 内部评分仅用于排序，**不作为对外友好度/排名/评分**（产品约束：Access，不是 Friendly）。
- 硬闸门：Place Match 必须成立（能指认到唯一真实场所，别名/分店需消歧）。
- 未通过 Place Match 的一律不入选，不因凑数放宽。

## 2. 入选清单

| 场所 | place_type | 行政区 | Place Match 依据 | 候选数 | 地理 |
|---|---|---|---|---|---|
| 上海动物园 | scenic_area | 长宁区 | canonical_name_and_official_domain | 1 | PLACE_GEO_PENDING |
| 上海博物馆东馆 | museum | 浦东新区 | canonical_name_and_official_domain | 3 | PLACE_GEO_PENDING |
| 世纪公园 | park | 浦东新区 | canonical_name_and_address | 2 | PLACE_GEO_PENDING |
| 兴业太古汇 | mall | 静安区 | canonical_name_and_address | 3 | PLACE_GEO_PENDING |
| 上海苏河湾万象天地 | mall | 静安区 | canonical_name_and_address | 2 | PLACE_GEO_PENDING |
| 上海蟠龙天地 | scenic_area | 青浦区 | canonical_name_and_official_domain_and_gov_source | 2 | PLACE_GEO_PENDING |
| 上海新天地朗廷酒店 | hotel | 黄浦区 | canonical_name_and_official_domain | 4 | PLACE_GEO_PENDING |
| omitofee 上海首店（浦江郊野公园滨江漫步区） | cafe | 闵行区 | canonical_name_and_address_description | 3 | PLACE_GEO_PENDING |
| CHARLIE'S 粉红汉堡（马当路店） | restaurant | 黄浦区 | canonical_name_and_address | 2 | PLACE_GEO_PENDING |
| 西岸梦中心（Gate M） | square | 徐汇区 | canonical_name_and_address_description | 2 | PLACE_GEO_PENDING |

**place_type 多样性 = 8**（要求 ≥ 6）。分布：cafe×1、hotel×1、mall×2、museum×1、park×1、restaurant×1、scenic_area×2、square×1

## 3. 建议构成对照

| 建议类别 | 建议数 | 本轮实际 |
|---|---|---|
| mall | 2 | 2 |
| F&B（cafe/restaurant） | 2 | 2 |
| hotel | 1 | 1 |
| park | 1 | 1 |
| library/museum | 1 | 1 |
| scenic | 1 | 2 |
| commercial street / square | 1 | 1 |
| temporary-event 潜力 | 1 | 见下 |

> 实际类型与建议构成在个别类别上不完全对齐：本轮以「可核验的真实公开来源」为硬约束，宁可类型分布略有偏差，也不引入无法核验的场所。

## 4. 未做的取舍

- 不纳入仅有社交平台线索、无官方/权威来源的场所。
- 不纳入无法消歧的分店/同名场所。
