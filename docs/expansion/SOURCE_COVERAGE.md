# SOURCE_COVERAGE — 来源覆盖与优先级分布

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 来源优先级（§12）

政府/法规 > 官方运营方 > 场所告示 > 现场标识 > 平台 > 外部 > 社交（仅线索）

## 2. 覆盖情况

| source_type | 数量 | 已监控 |
|---|---|---|
| external_web_reference | 12 | 0 |
| government_service | 2 | 2 |
| official_operator_policy | 9 | 9 |
| ordinary_user | 1 | 0 |
| statute_or_regulation | 2 | 2 |

来源总数 **26**。

## 3. 逐来源清单

| source_type | issuer | URL | 监控 | 复核周期(天) |
|---|---|---|---|---|
| external_web_reference | Booking/Hotels.com/Expedia 聚合展示的运营方宠物政策 | 有 | 否 | 180 |
| external_web_reference | CBNData（Manner 首家宠物友好店报道） | 有 | 否 | 180 |
| external_web_reference | 上观新闻（解放日报）《5000㎡乐园，人放松、宠撒欢，上海首家人宠共生江边咖啡营 | 有 | 否 | 180 |
| external_web_reference | 新华网/界面新闻《“宠物友好”餐厅，两边不讨好》（运营方规定报道，原文已直抓） | 有 | 否 | 180 |
| external_web_reference | 新浪财经/澎湃《网友称在星巴克被要求给带宠物的让座，记者现场实探》（西岸梦中心客 | 有 | 否 | 180 |
| external_web_reference | 新闻媒体（2026-08 星巴克宠物专区调整报道） | 无 | 否 | 180 |
| external_web_reference | 潮新闻《星巴克回应宠物专区“让座”争议：已致歉并着手改进》（星巴克中国官方回应） | 有 | 否 | 180 |
| external_web_reference | 澎湃新闻/九派新闻/劳动报《上海一星巴克要求「给带宠物的让座」》（记者现场实探， | 有 | 否 | 180 |
| external_web_reference | 腾讯新闻《不是退步而是更规范！上海部分商场取消或缩小宠物友好范围》（记者实地探访 | 有 | 否 | 180 |
| external_web_reference | 西五街《宠物友好第27站｜CHARLIE'S 粉红汉堡》（第三方平台内容，lea | 有 | 否 | 180 |
| external_web_reference | 解放日报（运营方室内宠物禁令报道） | 有 | 否 | 180 |
| external_web_reference | 青年报《上海部分商场撤除「宠物友好」标识》（记者实地采访，含运营方表态） | 有 | 否 | 180 |
| government_service | 上海市文化和旅游事业发展中心《又一新地标！这个周末，带「毛孩子」来放飞》（转述世 | 有 | 是 | 180 |
| government_service | 黄浦区人民政府官网《9月1日起，上海这些公园试点宠物入园》（来源：新闻晨报） | 有 | 是 | 180 |
| official_operator_policy | 上海动物园官网《温馨提示》 | 有 | 是 | 90 |
| official_operator_policy | 上海博物馆官网《到访·东馆》参观须知 | 有 | 是 | 90 |
| official_operator_policy | 上海图书馆官网《读者须知》 | 有 | 是 | 90 |
| official_operator_policy | 上海迪士尼度假区官网《上海迪士尼乐园游客须知》 | 有 | 是 | 90 |
| official_operator_policy | 前滩太古里（太古地产）官网《宠物友好》页 | 有 | 是 | 90 |
| official_operator_policy | 星巴克中国官网新闻中心（品牌合作计划新闻稿） | 有 | 是 | 90 |
| official_operator_policy | 朗廷酒店及度假酒店官网《宠物友好》（上海新天地朗廷酒店 Pawcation 礼遇 | 有 | 是 | 90 |
| official_operator_policy | 瑞安新天地官网《蟠龙天地品牌官宣》 | 有 | 是 | 90 |
| official_operator_policy | 费尔蒙上海和平饭店官网《宾客信息·宠物政策》 | 有 | 是 | 90 |
| ordinary_user | 社交平台用户经历帖（lead-only） | 无 | 否 | 180 |
| statute_or_regulation | 上海市人大常委会《上海市养犬管理条例》第二十三条（上海公安网官方转载页） | 有 | 是 | 365 |
| statute_or_regulation | 上海市人民政府门户《上海市养犬管理条例》 | 有 | 是 | 365 |

## 4. 许可证字段（§13）

来源许可证字段（storage/display/redistribution/commercial/attribution/raw_retention/expires）落在本轮的 SourceArtifact 上：

| storage | display | redistribution | artifact 数 |
|---|---|---|---|
| 允许 | 允许 | 否 | 7 |
| 允许 | 否 | 否 | 6 |
| 否 | 否 | 否 | 1 |

未拿到明确再利用授权的外部来源默认 `display_allowed=false`、`redistribution_allowed=false`：抓得到 ≠ 可以展示，更 ≠ 可以再分发。
