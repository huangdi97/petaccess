# NEW_10_PLACE_REPORT — 10 个新增场所逐场所结果

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

本轮共 10 个新场所，逐场所记录：来源、证据、候选、可回答性。

## 上海动物园

- place_key: `zoo-shanghai`
- place_type: `scenic_area`｜行政区：长宁区
- 地址：上海市长宁区虹桥路2381号
- 别名：西郊公园（旧称）、Shanghai Zoo
- Place Match：`canonical_name_and_official_domain`（官方域 shanghaizoo.cn）
- 消歧：与上海野生动物园（浦东新区南六公路178号）为不同法人、不同园区的两个场所；本条仅指长宁区虹桥路2381号上海动物园。
- 地理：`PLACE_GEO_PENDING` — 官方页面未公布坐标；不推断
- 候选规则 1 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| other | prohibited | OPERATOR_POLICY | operator_discretion | other | exact | official_operator_policy |

## 上海博物馆东馆

- place_key: `mus-shanghai-east`
- place_type: `museum`｜行政区：浦东新区
- 地址：上海市浦东新区世纪大道1952号
- 别名：上博东馆、Shanghai Museum East
- Place Match：`canonical_name_and_official_domain`（官方域 shanghaimuseum.net）
- 消歧：与上海博物馆人民广场馆（黄浦区人民大道201号）为同一法人下的不同馆区，规则分别适用；本条仅指东馆。
- 地理：`PLACE_GEO_PENDING` — 官方页面未公布坐标；不推断
- 候选规则 3 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| dog | prohibited | LEGAL | mandatory | dog | exact | statute_or_regulation |
| service_dog | allowed | LEGAL | mandatory | guide_dog | exact | statute_or_regulation |
| ordinary_pet | prohibited | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | official_operator_policy |

## 世纪公园

- place_key: `pk-century`
- place_type: `park`｜行政区：浦东新区
- 地址：上海市浦东新区锦绣路1001号
- 别名：上海世纪公园、Century Park
- Place Match：`canonical_name_and_address`（官方域 -）
- 消歧：与杭州市萧山区「钱江世纪公园」同名不同地；本条仅指上海浦东世纪公园。
- 地理：`PLACE_GEO_PENDING` — 官方口径来源未公布坐标；不推断
- 候选规则 2 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | government_service |
| ordinary_pet | prohibited | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | government_service |

## 兴业太古汇

- place_key: `ml-hk-taikoo`
- place_type: `mall`｜行政区：静安区
- 地址：上海市静安区南京西路1266号
- 别名：HKRI Taikoo Hui、兴业太古汇广场
- Place Match：`canonical_name_and_address`（官方域 -）
- 消歧：与前滩太古里（浦东东育路500弄）、蟠龙天地、苏河湾万象天地为不同项目；本条仅指南京西路1266号兴业太古汇。
- 地理：`PLACE_GEO_PENDING` — 来源未公布坐标；不推断
- 候选规则 3 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| dog | prohibited | LEGAL | mandatory | dog | exact | statute_or_regulation |
| service_dog | allowed | LEGAL | mandatory | guide_dog | exact | statute_or_regulation |
| ordinary_pet | prohibited | OPERATOR_POLICY | operator_discretion | ordinary_pet | legal_interpretation_required | external_web_reference |

## 上海苏河湾万象天地

- place_key: `ml-suhewan-mixc`
- place_type: `mall`｜行政区：静安区
- 地址：上海市静安区福建北路100号
- 别名：苏河湾万象天地、MixC Suhewan
- Place Match：`canonical_name_and_address`（官方域 -）
- 消歧：与深圳万象天地、上海其他「万象城」系列项目区分；本条仅指静安区福建北路100号苏河湾万象天地。
- 地理：`PLACE_GEO_PENDING` — 来源未公布坐标；不推断
- 候选规则 2 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| dog | prohibited | LEGAL | mandatory | dog | exact | statute_or_regulation |
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | external_web_reference |

## 上海蟠龙天地

- place_key: `sc-panlong-tiandi`
- place_type: `scenic_area`｜行政区：青浦区
- 地址：上海市青浦区蟠鼎路123弄8号
- 别名：蟠龙天地、公园里的新天地、Panlong Tiandi
- Place Match：`canonical_name_and_official_domain_and_gov_source`（官方域 xintiandi.com）
- 消歧：与上海新天地（黄浦区）同属瑞安系但为不同项目；2025-03 获批上海郊区首个国家级旅游休闲街区。
- 地理：`PLACE_GEO_PENDING` — 来源未公布坐标；不推断
- 候选规则 2 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | legal_interpretation_required | official_operator_policy |
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | legal_interpretation_required | official_operator_policy |

## 上海新天地朗廷酒店

- place_key: `ht-langham-xintiandi`
- place_type: `hotel`｜行政区：黄浦区
- 地址：上海市黄浦区马当路99号
- 别名：The Langham, Shanghai, Xintiandi、朗廷酒店（上海新天地）
- Place Match：`canonical_name_and_official_domain`（官方域 langhamhotels.com）
- 消歧：与上海其他朗廷系酒店（如虹桥）区分；本条为新天地朗廷，宠物条款来自其官网 Pawcation 礼遇页。
- 地理：`PLACE_GEO_PENDING` — 来源未公布坐标；不推断
- 候选规则 4 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| dog | prohibited | LEGAL | mandatory | dog | exact | statute_or_regulation |
| dog | conditional | OPERATOR_POLICY | operator_discretion | dog | exact | official_operator_policy |
| dog | conditional | OPERATOR_POLICY | operator_discretion | dog | exact | official_operator_policy |
| dog | conditional | OPERATOR_POLICY | operator_discretion | dog | exact | official_operator_policy |

## omitofee 上海首店（浦江郊野公园滨江漫步区）

- place_key: `cafe-omitofee-pujiang`
- place_type: `cafe`｜行政区：闵行区
- 地址：上海市闵行区浦江郊野公园滨江漫步区（闵浦二桥下）
- 别名：omitofee 上海首店、omitofee 咖啡营
- Place Match：`canonical_name_and_address_description`（官方域 -）
- 消歧：该品牌此前深耕苏州市场，本条为上海首店（闵行浦江郊野公园滨江漫步区），与苏州门店区分。
- 地理：`PLACE_GEO_PENDING` — 来源仅描述「闵浦二桥下」「浦江郊野公园滨江漫步区」，未给出坐标；不推断
- 候选规则 3 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| dog | prohibited | LEGAL | mandatory | dog | exact | statute_or_regulation |
| dog | conditional | OPERATOR_POLICY | operator_discretion | dog | legal_interpretation_required | external_web_reference |
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | external_web_reference |

## CHARLIE'S 粉红汉堡（马当路店）

- place_key: `rest-charlies-madang`
- place_type: `restaurant`｜行政区：黄浦区
- 地址：上海市黄浦区马当路441号中海环宇荟地上一层L33室
- 别名：CHARLIE'S 粉红汉堡、Charlie's Pink Burger
- Place Match：`canonical_name_and_address`（官方域 -）
- 消歧：品牌多门店；本条仅指马当路店（中海环宇荟）。
- 地理：`PLACE_GEO_PENDING` — 来源未公布坐标；不推断
- 候选规则 2 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| dog | prohibited | LEGAL | mandatory | dog | exact | statute_or_regulation |
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | legal_interpretation_required | external_web_reference |

## 西岸梦中心（Gate M）

- place_key: `sq-west-bund-gatem`
- place_type: `square`｜行政区：徐汇区
- 地址：上海市徐汇区龙腾大道（西岸梦中心/Gate M 滨江开放区域）
- 别名：Gate M 西岸梦中心、西岸梦中心、West Bund Dream Center
- Place Match：`canonical_name_and_address_description`（官方域 -）
- 消歧：与场内租户「星巴克咖啡（徐汇西岸梦中心店）」为不同层级的实体：后者是独立 Place，本条为所在开放式综合空间。二者规则分别记录，不得相互外推。
- 地理：`PLACE_GEO_PENDING` — 来源未公布坐标；不推断
- 候选规则 2 条：

| animal_scope | effect | layer | mandatory | subject_norm | normalization | source_type |
|---|---|---|---|---|---|---|
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | external_web_reference |
| ordinary_pet | conditional | OPERATOR_POLICY | operator_discretion | ordinary_pet | exact | external_web_reference |

---

所有候选均为 `REVIEW_PENDING`，`published_rule_id` 全为 null —— 未发生任何自动发布。
