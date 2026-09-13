# EVIDENCE_REPAIR_LOG_R1.md

> S6：对 7 条 search-snippet 候选的证据补强记录（2026-09-13，REALITY-AUDIT-10-R2 前置）。
> 每次尝试一条记录：目标 → 方式 → 结果 → 证据强度变化。**未绕过任何登录/验证码/访问控制；403/验证码即停，改走合法通道。**
> 执行脚本：`scripts/evidence_repair_r2.py`（全部变更带 audit_log 留痕）。

## 结果总览

| 任务 | 候选 | 结果 | 证据强度变化 |
|---|---|---|---|
| B1 港汇·室内禁止 | `73448553` | ✅ 修复（新华网直抓） | SEARCH_SNIPPET → SECONDARY_REPUTABLE |
| B2 港汇·户外保留 | `887f21ba` | ⚠️ 未证实（原文只覆盖室内） | 保持 SEARCH_SNIPPET（Needs Verification） |
| B3 和平饭店·宠物禁入 | `4c7aba30` | ✅ 修复（费尔蒙官网直抓） | SEARCH_SNIPPET → **PRIMARY_DIRECT** |
| B4 和平饭店·服务动物 | `7efddba6` | ✅ 修复 + 效果修正（官网原文无限制→allowed） | SEARCH_SNIPPET → **PRIMARY_DIRECT** |
| B5 Manner·凯德虹口 | `ed79071d` | ❌ **归因错误实锤**（CBNData 原文无此报道） | 维持；建议人工 REJECT |
| B6 西岸·室内取消宠物区 | `9c8b4b26` | ✅ 修复（潮新闻直抓，官方回应） | SEARCH_SNIPPET → SECONDARY_REPUTABLE |
| B7 西岸·户外宠物区 | `fb003b3a` | ✅ 修复（潮新闻 + 澎湃客服回应） | SEARCH_SNIPPET → SECONDARY_REPUTABLE |

**修复后 direct-or-strong 占比：30/33 = 90.9%**（PRIMARY_DIRECT 15 + SECONDARY_REPUTABLE 3 = 18 条候选有强证据；其余 15 条候选本就引用 PRIMARY_DIRECT 官方页）。R1 的 78.8% 门禁阻塞已解除。

## 逐次尝试记录

| # | 时间(UTC) | 任务 | 目标/通道 | 结果 |
|---|---|---|---|---|
| T1 | 06:0x | B1 港汇 | web_reader 抓 jfdaily.com/news/detail?id=1079860 | ❌ 平台内容过滤拦截（-400 contentFilter） |
| T2 | 06:0x | B1 港汇 | web_reader 重试 jfdaily（no_cache） | ❌ 同上 |
| T3 | 06:0x | B1 港汇 | WebFetch 抓新华网 food/20260529/... | ✅ **直抓成功**，逐字引文："比如港汇恒隆广场、兴业太古汇自今年2月起正式实施全新宠物管理规定，明确禁止除导盲犬等工作犬以外的其他宠物进入商场室内公共区域，全面撤除"宠物友好"相关标识"；文章《"宠物友好"餐厅，两边不讨好》2026-05-29 |
| T4 | 06:0x | B2 港汇·户外 | 引文核对 | ⚠️ 新华网原文只覆盖"室内公共区域"，未提户外 → B2 不可升级 |
| T5 | 06:0x | B5 Manner | WebFetch 抓 cbndata.com/information/255703 | ❌ **归因错误**：原文《Manner、KFC都入局》未报道凯德虹口宠物友好店（文中"凯德虹口"指宠物用品店"狗道"）；Manner 案例实为徐汇滨江店（户外宠物区、不能入店）→ B5 候选的来源支撑不成立，audit_log 记 contradiction，建议人工 REJECT |
| T6 | 06:0x | B3/B4 和平饭店 | WebFetch fairmont.com/peace-hotel/ | ❌ 404 |
| T7 | 06:0x | B3/B4 和平饭店 | 搜索定位官网正确 URL | ✅ fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel.html |
| T8 | 06:0x | B3/B4 和平饭店 | WebFetch 官网主页 | ⚠️ 主页无宠物政策 |
| T9 | 06:0x | B3/B4 和平饭店 | WebFetch guest-services.html | ✅ **官方原文**："上海和平饭店（费尔蒙旗下酒店）禁止宠物入内。导盲犬可随时进入酒店，且无需支付额外费用或受任何限制。" → B3 直挂；B4 效果由 conditional 修正为 allowed（官方无附加限制） |
| T10 | 06:0x | B6/B7 西岸 | 搜索定位原始报道 | ✅ 新浪财经 2026-08-27（澎湃）、潮新闻 tidenews 3542194、百度百科事件条目（lead） |
| T11 | 06:0x | B6/B7 西岸 | 搜索（含"回应 户外"） | ⚠️ 一次 captcha verify failed，更换措辞重试成功（未绕过验证码，未再访问该目标） |
| T12 | 06:0x | B6 西岸 | WebFetch 新浪 doc-iniptnux5511541 | ✅ 直抓：西岸梦中心客服逐字回应（户外空间和外摆区域允许宠物活动；进店看各店规定；"会按照《上海市养犬管理条例》、市规大于商场规定的原则来执行"）；注：星巴克中国官方回应不在该文（店员说法≠官方回应） |
| T13 | 06:0x | B6/B7 西岸 | WebFetch 潮新闻 tidenews 3542194 | ✅ 直抓官方回应逐字："……已向顾客本人表达了诚挚的歉意，并着手进行了改进，不在该店内继续设置宠物区域。""携宠顾客需在店外宠物友好区落座。"（2026-08-27） |
| T14 | 06:1x | B1 复核 | WebFetch jfdaily 原文 | ❌ 页面模板占位、"此文章不存在或已下线" → 解放日报 URL 标记 dead，以新华网版本为准 |

## 新增证据链（DB 实录）

| 来源 | URL | 强度 | 支撑候选 |
|---|---|---|---|
| 新华网/界面新闻 2026-05-29 | xinhuanet.com/food/20260529/7317dcff... | secondary_reputable | gh-indoor-new |
| 费尔蒙官网 guest-services | fairmont.com/zh/hotels/shanghai/fairmont-peace-hotel/guest-services.html | **primary_direct** | fp-pets-op, fp-sd-op |
| 潮新闻 2026-08-27 | tidenews.com.cn/news.html?id=3542194 | secondary_reputable | xm-indoor-new, xm-outdoor-media |
| 新浪/澎湃 2026-08-27 | finance.sina.com.cn/jjxw/2026-08-27/doc-iniptnux5511541.shtml | secondary_reputable | （西岸客服引述条例，附加证据） |

## 对 R2 的语义修正（供样本更新）

1. 港汇/兴业太古汇运营方政策**自带工作犬例外**（"除导盲犬等工作犬以外"）→ 室内禁止规则上挂 operator 级 RuleException（service_dog, allowed）。
2. 和平饭店服务动物政策为**无限制允许**（导盲犬可随时进入、免费、无限制）→ fp-sd-op effect=allowed。
3. 西岸店室内取消宠物区 + 户外落座为**星巴克中国官方回应**（潮新闻直抓），不再是模糊"媒体报道"。
4. Manner 凯德虹口候选来源不成立 → 维持 REVIEW_PENDING，附 contradiction 审计记录，建议人工 REJECT（AI 不代做决策）。
5. 西岸梦中心客服明确"市规大于商场规定"——条例第23条 LEGAL 层对该商场的适用性有官方口径支撑。
