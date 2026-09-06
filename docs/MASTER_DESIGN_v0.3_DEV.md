# 宠物准入信息平台 v0.3 · DEV MASTER
## Place Animal Access Map / 现实场所动物准入地图

> **Canonical Design Master / 开发唯一设计母版**
>
> 版本：v0.3-DEV-MASTER  
> 日期：2026-09-06  
> 状态：设计冻结，可进入工程实现  
>
> **一句话定位：让每个人在到达一个地方之前，知道这里关于动物的规则。**

---

# 0. 文档定位与冻结说明

本文件在原《宠物准入信息平台 · 设计文档 v0.1》的基础上，整合后续全部讨论并重构：

- 不只覆盖餐厅和店铺，而覆盖公园、商场、小区公共空间、景区、酒店、公共服务设施等现实场所；
- 将 DogMap、Dog Free Zone Map、BringFido、DogPack、GoDoggo、遛探、上海官方公园服务、Spokin、AccessNow 等产品中已经被验证的能力拆分后重新组合；
- 从“宠物友好/避宠地图”升级为中性的“动物准入规则地图”；
- 支持用户建立自己的宠物档案，AI 辅助识别动物种类/疑似品种并由用户确认；
- 支持“带宠出行”“普通宠物限制”“服务犬通行”“规则地图”四种查询模式；
- 从 `POI → pet_policy` 升级为 `Place → Zone → AccessRule`；
- 从单轴 L0-L4 证据等级升级为多维 Provenance；
- 从单纯 UGC 升级为官方来源、管理方认证、可信核验员、现场告示、普通用户并存的数据治理体系；
- 明确地图数据、个人定位、图片、管理方申诉和住宅区隐私边界；
- 将 AI 限定为识别、抽取、标准化、变更检测和搜索理解工具，不允许成为法律或事实裁判。

除非后续形成明确 ADR 并更新本文，否则工程实现必须以本文作为产品、数据和架构的最高优先级规范。

---

# 1. 最终产品是什么

## 1.1 对用户的产品

这不是法规数据库，也不是用户打开后看到一堆规则字段。

用户最终看到的是一个**地图型场所准入查询工具**：

1. 选择“我带谁”或“我要查什么”；
2. 在地图上搜索附近地点；
3. 直接看到对于当前查询对象：
   - 可以；
   - 有条件；
   - 明确限制；
   - 信息不足；
4. 点进地点后看到：
   - 哪个区域允许/限制；
   - 需要满足什么条件；
   - 适用时间；
   - 规则来源；
   - 最近核验；
   - 历史现场观察；
   - 相关法规；
5. 到达现场后可以一键确认规则仍有效、报告变化或上传告示；
6. 管理方可以认领地点并维护自己的正式声明；
7. 用户可以关注地点，在规则变化时收到提醒。

## 1.2 对数据层的产品

后台真正建设的是：

> **现实世界“动物 × 空间 × 区域 × 行为 × 条件 × 时间 × 规则来源 × 实际观察”的结构化数据层。**

核心链路：

```text
Pet / Query Profile
        ↓
Place
        ↓
Zone
        ↓
AccessRule
        ↓
Rule Evaluator
        ↓
Applicable Result
        ↓
Source / Verification / Observation
```

## 1.3 不是什么

明确禁止产品滑向以下方向：

- 不是“宠物雷区曝光平台”；
- 不是“宠物友好商家排行榜”；
- 不是“无狗安全保证平台”；
- 不是评论/骂战社区；
- 不是居民养宠监视或邻里举报平台；
- 不是基于 UGC 计算“遇狗率/安全率”的统计产品；
- 不是由大模型直接判断某场所违法、卫生或安全；
- 不是直接复制第三方地图/点评数据库；
- 不是只有养宠用户才能使用的单边产品。

---

# 2. 竞品能力如何合并

| 来源 | 吸收的能力 | 不照搬的部分 |
|---|---|---|
| DogMap | 低门槛快速标记、地图即入口 | 规则太粗 |
| Dog Free | “限制普通宠物”反向查询 | 不承诺“绝对无动物” |
| BringFido | 多场景、详细 Pet Policy、未来交易 | 不只服务携宠者 |
| DogPack | Check-in、商家 Claim、用户持续更新 | 不做重社交 |
| GoDoggo | indoor/patio/off-leash/设施等结构字段 | 不只做 dog-friendly |
| 遛探 | 中国本地地图、附近发现、限制标记 | 不以遛宠轨迹/社区为核心 |
| 上海官方公园服务 | 官方数据、Zone、开放时间、体型/区域条件 | 不限单城市单部门 |
| Spokin | 管理方结构化认证问卷 | 不接受一句广告式“友好”声明 |
| AccessNow | 可信/专业现场核验 | 不把核验变成高成本唯一数据源 |
| 原 v0.1 | 中性、状态/证言分离、不猜、时效、申诉、历史 | 升级底层模型 |

最终不是功能堆叠，而是统一为：

```text
我的宠物/我的需求
        ↓
地图发现
        ↓
场所规则卡
        ↓
空间分区
        ↓
规则来源/核验
        ↓
现场确认/纠错
```

---

# 3. 产品原则

## 3.1 中性

中性定义：

> 同一事实库、对称采集、来源透明、不做道德评分、不做编辑型红黑榜、不利用算法隐藏某一侧信息，查询结果由用户主动选择的条件决定。

允许用户主动筛：
- 明确允许普通犬；
- 明确限制普通犬；
- 仅户外；
- 需推车；
- 有服务犬信息；
- 最近核验。

禁止：
- “最恶心的十家店”；
- “宠物雷区指数”；
- “卫生风险评分”；
- 按证言数量做红黑榜。

## 3.2 规则与观察分离

`AccessRule` 表示：某来源规定应该怎样。  
`ObservationClaim` 表示：某人在某时报告实际观察到什么。

禁止从“带狗进去没人拦”自动推断“允许宠物”。

## 3.3 不猜

地点不确定，不自动挂具体商户。
AI 可给候选，不可自动升级模糊归属。

## 3.4 不承诺无动物

“普通宠物明示禁止”不等于“现场绝对没有动物”。

固定提示：

> 本页展示已收录的法律/管理规则和历史现场记录，不构成场所实际无动物的保证。服务犬、规则执行差异、临时变化或违规进入可能导致现场情况不同。

## 3.5 最小必要个人信息

- 定位只用于附近查询/现场核验；
- 不默认连续记录轨迹；
- 小区不记录具体住户养宠；
- 宠物档案只收规则匹配真正需要的信息。

## 3.6 渐进采集

后台可以复杂，用户第一次贡献必须简单：先问一个问题，再按回答继续展开。

---

# 4. 用户模式

## 4.1 带宠出行

回答：
- 我的宠物能不能进？
- 哪里能进？
- 需要什么条件？
- 哪个入口/电梯？
- 当前时间适用吗？

## 4.2 普通宠物限制

面向怕犬、过敏、家长、卫生顾虑等用户。

回答：
- 哪些空间明确限制普通宠物？
- 哪些限制有近期、可追溯来源？

此模式不叫“Dog Free”，因为规则禁止不等于现场绝对无动物。

## 4.3 服务犬通行

独立查询服务犬规则，不与普通宠物混用。

## 4.4 规则地图

不建立宠物档案也能直接查看某地点的完整准入规则。

---

# 5. 我的宠物 Pet Profile

## 5.1 目的

不是社交档案，是规则匹配输入。

```text
pet_id
user_id
display_name
species
breed_text
breed_id_optional
weight_kg_optional
shoulder_height_cm_optional
service_role
registration_status_optional
vaccination_status_optional
avatar_optional
created_at
updated_at
```

## 5.2 AI 识别

流程：

```text
拍照/选图
→ Vision Provider
→ species suggestion
→ breed suggestion
→ 用户确认/修改
→ Pet Profile
```

AI 可以建议动物种类和疑似品种。

AI 不可以：
- 自动认定服务犬；
- 自动确认犬证；
- 用图像估算肩高/体重作为最终法律条件；
- 识别人主人身份。

如果规则依赖体重、肩高、犬证、疫苗、服务犬身份，必须要求用户明确确认。

## 5.3 多宠物

允许建立多个宠物。
用户出行时选择“这次带谁”。

长期支持同行组合：
- 多只宠物；
- 推车/宠物包；
- 目标时间；
- 目标场景。

---

# 6. 首页与地图

## 6.1 底部导航

1. 地图
2. 搜索
3. 贡献
4. 我的

## 6.2 地图顶部

模式：
- 带宠出行
- 普通宠物限制
- 服务犬通行
- 规则地图

对象：
> 本次：豆豆 · 柴犬 · 9.5kg

## 6.3 查询结果状态

- `MATCH`：适用于当前查询；
- `CONDITIONAL`：有条件；
- `RESTRICTED`：明确限制；
- `UNKNOWN`：信息不足；
- `CONFLICT`：存在需要处理的规范来源冲突。

视觉不能只靠红绿，必须有图标、形状和文字。

## 6.4 筛选

通用：
- 场所类型；
- 距离；
- 最近核验；
- 管理方确认；
- 官方来源；
- 有 Zone；
- 有服务犬信息。

带宠：
- 室内可进；
- 户外可进；
- 可落地；
- 需推车/包；
- 不限体型；
- 宠物活动区；
- off-leash；
- 宠物设施。

限制：
- 普通宠物明示限制；
- 室内限制；
- 儿童区域限制；
- 最近核验；
- 官方/管理方来源。

---

# 7. 场所详情最终呈现

顺序：

1. 当前查询结果；
2. 适用区域；
3. 条件；
4. 来源与核验时间；
5. 现场观察；
6. 法规；
7. 纠错/异议；
8. 历史版本。

## 7.1 餐饮

```text
XX咖啡

对于：豆豆 · 柴犬 · 9.5kg
结果：有条件进入

室内：普通犬明确限制
户外座位：可进入 · 需牵引

规则来源：
门口告示 · 2026-08-21 现场核验

最近现场：
2026-09-02 某用户报告：携犬进入户外区域
```

## 7.2 公园

必须支持 Zone：

```text
XX公园
整体：部分区域可进入

A草坪       牵引可进入
儿童活动区   普通犬限制
宠物活动区   可进入
夜间草坪     21:00 后开放
```

地图画 Polygon / Line，不只放一个图钉。

## 7.3 商场

支持楼层/Zone：

```text
6F 餐饮       普通宠物限制
4F 商铺       需推车/宠物包
3F 宠物区     可进入
1F 公共区     需推车/宠物包
B1 超市       普通宠物限制

宠物入口：南门
宠物电梯：2号梯
```

长期支持携宠路线。

## 7.4 小区

只做公共空间：

```text
公共道路      犬只需牵引
儿童活动区    普通犬限制
中心草坪      暂未检索到明确规则
宠物活动区    有
```

禁止：
- 某楼某户养狗；
- 居民名单；
- 楼栋养宠统计；
- 邻里举报榜。

## 7.5 酒店

参考 BringFido：
- 动物类型；
- 体型；
- 数量；
- 宠物费；
- 房型；
- 是否允许单独留宠；
- 提前告知；
- 设施；
- 来源。

---

# 8. 核心领域模型

```text
User
 └─ PetProfile

Place
 ├─ Geometry
 ├─ Zone
 │   ├─ Geometry
 │   └─ AccessRule
 ├─ Operator
 ├─ ObservationClaim
 ├─ VerificationEvent
 └─ ExternalPlaceRef

AccessRule
 ├─ Source
 ├─ Conditions
 ├─ EffectiveTime
 └─ Applicability

JurisdictionRule
 └─ Source

DisputeCase
 ├─ Target
 ├─ Evidence
 ├─ CounterStatement
 └─ Resolution
```

---

# 9. Place / Zone / Geometry

## 9.1 Place

```text
place
  id UUID PK
  canonical_name
  place_type
  parent_place_id nullable
  operator_id nullable
  lifecycle_status
  canonical_address nullable
  created_at
  updated_at
```

场所类型首批：
- restaurant
- cafe
- mall
- store
- hotel
- park
- square
- greenway
- beach
- scenic_area
- residential_community
- office_campus
- hospital
- school
- library
- museum
- sports_venue
- transport_hub
- other

## 9.2 Zone

```text
zone
  id UUID PK
  place_id FK
  parent_zone_id nullable
  name
  zone_type
  floor_ref nullable
  indoor_outdoor
  created_at
  updated_at
```

## 9.3 Geometry

```text
place_geometry
  id
  place_id nullable
  zone_id nullable
  geometry_type
  geometry PostGIS
  source_id
  precision
  coordinate_system_internal
  created_at
  updated_at
```

支持：
- Point
- LineString
- Polygon
- MultiPolygon

---

# 10. AccessRule

```text
access_rule
  id
  place_id
  zone_id nullable
  animal_scope
  action
  effect
  source_id
  rule_origin
  effective_from nullable
  effective_to nullable
  recorded_at
  last_verified_at
  review_due_at
  status
  supersedes_rule_id nullable
  created_at
  updated_at
```

Animal 首版：
- dog
- cat
- ordinary_pet
- service_dog
- other

Action：
- enter
- pass_through
- stay
- walk
- off_leash
- ground_contact
- ride_elevator
- ride_transport
- use_facility
- dine
- stay_overnight

Effect：
- allowed
- prohibited
- conditional

未知不是 effect，而是覆盖状态。

---

# 11. 条件 RuleCondition

首版：

- leash_required
- muzzle_required
- carrier_required
- stroller_required
- no_ground
- registration_required
- vaccination_required
- max_weight_kg
- min_weight_kg
- max_shoulder_height_cm
- max_count
- reservation_required
- advance_notice_required
- designated_entrance
- designated_elevator
- designated_route
- time_windows
- date_windows
- season
- fee
- room_restriction
- other_structured_note

自由文本只能补充，不能成为主要规则匹配依据。

---

# 12. Rule Evaluator

输入：

```text
QueryContext
  pet_profile / animal query
  target_place
  target_zone optional
  date_time
  intended_action
```

输出：

```text
ApplicabilityResult
  status:
    MATCH
    CONDITIONAL
    RESTRICTED
    UNKNOWN
    CONFLICT

  matched_rules[]
  unmet_conditions[]
  unknown_inputs[]
  reason_codes[]
  source_refs[]
```

**规则判断必须是确定性程序，不是 LLM。**

自然语言可以由 AI 解析：
> 周六晚上带 9kg 柴犬去国贸吃饭

变成结构化 QueryContext，再交给 evaluator。

若规则要求 10kg 以下、用户没填体重：
> 返回 UNKNOWN + “需要补充体重”。

不得猜。

---

# 13. Source / Provenance

不再用单轴 L0-L4 作为核心真值判断。

```text
source
  id
  source_type
  issuer
  issuer_verification
  source_url
  source_snapshot_ref optional
  collected_at
  observed_at optional
  published_at optional
  source_availability
  directness
  spatial_precision
  created_at
```

source_type：
- statute_or_regulation
- government_service
- official_operator_policy
- onsite_signage
- certified_verifier
- ordinary_user
- external_web_reference
- imported_dataset

用户端显示：
> 来源 + 日期 + 核验方式 + 是否有异议

不要显示“可信度 87 分”。

---

# 14. ObservationClaim

```text
observation_claim
  id
  place_id
  zone_id nullable
  user_id nullable
  occurred_at
  occurred_precision
  reported_at
  animal_scope
  observed_action
  staff_action
  place_confidence
  evidence_support
  dispute_status
  withdrawn_at nullable
  created_at
```

staff_action 只存可观察动作：
- explicitly_allowed
- explicitly_refused
- asked_to_remove
- no_interaction_observed
- interaction_unknown

删除“明确默许”等主观推断词。

Observation 永不自动变 Rule。

---

# 15. 快速贡献

第一次只问：

> 你知道这里对普通犬的规则吗？

- 明确允许
- 明确限制
- 有条件
- 不确定

有条件再问：
- 室内；
- 户外；
- 指定区域。

再问：
- 牵引；
- 推车；
- 包；
- 不落地；
- 体型。

现场确认：

> 页面显示“A区牵引可进入”

按钮：
- 规则仍有效
- 规则已经变化
- 不确定

位置通过后长期保存最小信息：

```text
proximity_verified
distance_bucket
accuracy_bucket
verified_at
```

不默认保存长期原始 GPS 历史。

---

# 16. 管理方认领与 Spokin 式问卷

流程：

```text
场所页
→ 申请认领
→ 主体验证
→ verified operator
→ 结构化问卷
→ operator-declared rules
```

认证可用：
- 企业邮箱；
- 官方域名；
- 官方联系方式回呼；
- 主体证明；
- 政府/机构公开账号；
- 物业/业委会证明。

首版可以人工审核。

问卷覆盖：
- 普通犬；
- 猫；
- 服务犬；
- 区域；
- 室内/户外；
- 落地；
- 推车/包；
- 体型/数量；
- 牵引/嘴套；
- 登记/免疫；
- 入口/电梯/路线；
- 时间；
- 生效日期。

管理方可修改自己的声明，但不能直接删除用户 Observation。

---

# 17. Trusted Mapper / 可信核验

长期角色：

- ordinary_contributor
- trusted_contributor
- certified_verifier
- operator
- official_source

可信核验员通过：
- 规则培训；
- 测验；
- 现场流程；
- 抽检；
- 错误率管理。

不按粉丝数授予可信度。

---

# 18. 法规 JurisdictionRule

```text
jurisdiction_rule
  id
  jurisdiction_level
  jurisdiction_id
  authority
  instrument_type
  document_name
  clause_ref
  clause_text_ref
  animal_scope
  venue_scope
  action
  effect
  conditions
  mandatory_level
  effective_from
  effective_to
  source_id
  supersedes_id
  status
  reviewed_at
```

“没规则”拆成：

- `EXPLICIT_OPERATOR_DISCRETION`
- `NO_EXPLICIT_RULE_FOUND`
- `NOT_REVIEWED`

绝不能把“没查”显示成“法律没规定”。

事实观察可并置。
规范规则需要按明确的时间、空间、授权关系做 applicability resolver。
不明确法律冲突进入人工复核，AI 不做最终解释。

---

# 19. 服务犬

Service dog 独立于 ordinary pet。

平台：
- 可以显示适用规则；
- 不从照片判断服务犬；
- 不常规收用户疾病/残疾信息；
- 不把服务犬通行等价于普通宠物友好。

---

# 20. 图片、OCR 与证据

优先采集：
1. 入口告示；
2. 规则牌；
3. 门头 + 规则牌；
4. 正式公告。

不鼓励拍他人/儿童。

流程：

```text
上传
→ 安全扫描
→ OCR
→ 规则候选
→ 人脸/车牌脱敏
→ 审核
→ 结构化
```

告示类可在明确用途和最小期限下受控保存。
人宠现场图采用短 TTL。
公众默认不展示高风险原图。
记录审核和删除日志。

具体 TTL 在上线隐私 Gate 确认。

---

# 21. AI 子系统

AI 可以：
- 宠物 species/breed 建议；
- OCR；
- 官方网页/PDF规则抽取；
- 自然语言查询解析；
- 标准化；
- 变更检测；
- 重复识别；
- 地点候选；
- 后台审核辅助。

AI 不可以：
- 认定服务犬；
- 做最终法律结论；
- 判商户违法；
- 模糊地点自动挂店；
- 从“没人阻止”推断允许；
- 自动黑榜；
- 用视觉估重作为最终准入条件。

Provider 化：

```text
AIProvider
VisionProvider
OCRProvider
MockProvider
```

开发默认 Mock，真实 Key 走环境变量。

---

# 22. 地图与外部 POI

## 22.1 自有主键

```text
place.id = UUID
```

外部：

```text
external_place_ref
  place_id
  provider
  external_id
  persistence_permission
  last_resolved_at
  metadata_hash_optional
```

第三方 POI 不能作为永久主键。

## 22.2 MapProvider

```text
MapProvider
  search_places()
  reverse_geocode()
  render_config()
  open_navigation()
```

MVP 首选腾讯地图：
- 微信适配；
- uni-app/uni-app x 对 Android/iOS/HarmonyOS/微信有统一支持路径。

必须可替换。

## 22.3 Polygon / Zone

自定义 Polygon 是核心。
上线前完成国内地图/坐标/自定义空间数据合规 Gate。

---

# 23. 搜索

MVP：
- PostgreSQL
- pg_trgm
- PostGIS nearby
- 应用层中文查询解析

不急着引入 Elasticsearch。

自然语言：
> 周六晚上国贸附近能带 9kg 柴犬吃饭的地方

AI 只解析 QueryContext，最终规则仍由 evaluator 判。

---

# 24. 关注与规则变化

用户可以关注：
- Place
- 公园
- 商场
- Zone/Rule

规则变化后推送。

用于解决低频工具的留存问题。

---

# 25. Admin

后台必须有：

1. Places
2. Zones / Geometry
3. Rules
4. Sources
5. Regulations
6. Operator Claims
7. Contributions
8. Verification Queue
9. Disputes
10. AI Extraction Queue
11. Rule Conflicts
12. Audit Log
13. Roles
14. Data Quality Dashboard

高影响操作写审计日志。

---

# 26. DisputeCase

```text
dispute_case
  id
  target_type
  target_id
  claimant
  reason_code
  notice_text
  evidence_refs
  temporary_action
  counter_statement
  status
  resolution
  reviewer_id
  created_at
  resolved_at
```

流程：
提交异议 → 主体校验 → 初步证据 → 必要临时措施 → 转送 → 反声明 → 人工复核 → 恢复/更正/归档/删除 → Audit。

---

# 27. 安全与反滥用

- 高频提交限流；
- 新账号更严格审核；
- 管理方不能用投票稀释记录；
- 不计算遇宠率；
- 地点错挂支持撤回；
- 文件上传检查；
- Admin RBAC；
- API rate limit；
- audit log；
- 高风险写接口幂等。

---

# 28. 隐私

用户位置：
- 查询时使用；
- 现场验证一次使用；
- 不默认生成轨迹。

Pet：
- 不默认公开证件类数据。

住宅：
- 只公共规则，不住户信息。

图片：
- 高风险不公开；
- 脱敏；
- 最小留存。

---

# 29. 技术架构冻结

## 客户端

**uni-app x + Vue 3 + TypeScript，优先 Vapor/蒸汽模式**

目标：
- 微信小程序
- Android
- iOS
- HarmonyOS
- Web/H5

业务规则不写进平台原生层。
平台差异通过 adapter/native-view/插件隔离。

## 地图

MVP：**腾讯地图 provider adapter**

但数据库永久身份独立于地图商。

## API

**Python + FastAPI**
- Pydantic v2
- SQLAlchemy 2
- Alembic
- psycopg3

## DB

**PostgreSQL + PostGIS**

## Cache/Jobs

**Redis + Celery**

## Object Storage

S3-compatible abstraction。
本地 MinIO。

## Admin

Vue 3 + TypeScript + Vite。

## Contract

FastAPI OpenAPI 为 SSOT。
自动生成 TS API Client。
禁止前后端分别手写 DTO。

---

# 30. Monorepo

```text
/
├─ apps/
│  ├─ client/
│  └─ admin/
├─ services/
│  ├─ api/
│  └─ worker/
├─ packages/
│  ├─ rule-spec/
│  ├─ api-client/
│  └─ design-tokens/
├─ infra/
│  ├─ docker/
│  └─ migrations/
├─ tests/
│  ├─ contract/
│  ├─ integration/
│  └─ e2e/
├─ docs/
├─ scripts/
├─ AGENTS.md
├─ GOAL.md
└─ README.md
```

---

# 31. API 模块

- `/auth`
- `/users`
- `/pets`
- `/places`
- `/zones`
- `/geometries`
- `/rules`
- `/rule-evaluate`
- `/observations`
- `/verifications`
- `/sources`
- `/regulations`
- `/operators`
- `/operator-claims`
- `/contributions`
- `/disputes`
- `/search`
- `/map`
- `/ai`
- `/notifications`
- `/admin/*`

所有写接口：
- validation
- role
- audit
- error code
- 高风险操作 idempotency

---

# 32. Rule Spec 独立包

`packages/rule-spec/`：

- animal-scope.schema.json
- access-action.schema.json
- rule-condition.schema.json
- query-context.schema.json
- applicability-result.schema.json
- fixtures/

核心规范不能只散落在 ORM。

---

# 33. 前端关键页面

必须完成：

1. Onboarding
2. 宠物创建
3. AI 识别确认
4. 地图首页
5. 模式切换
6. 搜索/筛选
7. Place 卡
8. Place 详情
9. 公园 Zone 地图
10. 商场楼层/Zone
11. Rule Source
12. Observation
13. Quick Confirm
14. 完整贡献
15. 上传告示
16. 我的宠物
17. 收藏/关注
18. 规则变化
19. Operator Claim
20. Dispute
21. 隐私/权限

---

# 34. 设计系统

原则：
- 中性；
- 地图优先；
- 信息密度高但不压迫；
- 状态用图标+文字，不只颜色；
- 暂无信息可见；
- 来源日期显式；
- 复杂规则渐进展开；
- 深浅色；
- 无障碍触控和字体。

禁用情绪词：
- 雷区
- 恶心
- 卫生差

不做“绿色=宠物友好好，红色=禁宠坏”的价值编码。

---

# 35. MVP

动物：
- 普通犬
- 猫
- 服务犬

场所：
- 餐饮/咖啡
- 商场
- 公园
- 小区公共规则（弱功能）

第二阶段：
- 酒店
- 景区
- 绿道
- 交通
- 公共服务设施

地理：
- 先一个高密度区域
- 200–500 个场所
- 做完整空间切片，而非全国铺点

MVP 必须：
- Pet Profile
- 手填
- AI Provider + Mock
- Map
- rule evaluator
- Place/Zone
- Source
- rule date
- Quick Confirm
- Operator Claim
- 结构化问卷
- Observation
- Dispute
- Admin
- Audit
- Watch 基础
- synthetic demo

MVP 不做：
- 排行榜
- 评论区
- 社交 Feed
- 遛宠轨迹
- 遇宠率
- 大规模爬虫
- AI 法律裁判
- 自训练视觉模型

---

# 36. 冷启动

优先级：

1. 官方法规；
2. 政府公共服务；
3. 场所管理方公开规则；
4. 现场告示；
5. 管理方认证问卷；
6. 可信核验；
7. 普通用户贡献；
8. 外部网络链接仅作线索。

MVP 不依赖小红书/抖音批量抓取。

---

# 37. KPI

- Rule Coverage
- Query Answer Rate
- Zone Coverage
- Median Rule Age
- Review Overdue Rate
- Official/Operator Source Ratio
- Operator Verification Rate
- Conflict Rate
- False Attribution Rate
- Dispute SLA
- Rule Change Detection Latency
- Real-world Match
- Unknown Reason Distribution

---

# 38. 长期商业化

- 免费 C 端地图；
- 管理方基础认领；
- 高级多场所管理；
- 规则二维码；
- 商场/景区/物业 SaaS；
- 酒店/旅游交易；
- API/Data；
- 政府/地图/OTA 数据合作。

付费不能换取“隐藏不利记录”。

---

# 39. 规则二维码

认证管理方可生成稳定二维码：

> 本场所动物准入规则

规则变更，二维码不变。

适合：
- 商场入口
- 公园入口
- 景区
- 酒店
- 小区公共区

---

# 40. 版本与历史

Rule 状态：
- current
- superseded
- withdrawn
- disputed
- archived

不正常 hard delete 历史。

新政策：
- 生效前 observation 可进入历史；
- 生效后的 observation 仍显示。

---

# 41. 测试

Unit：
- evaluator
- condition
- time
- privacy
- source lifecycle

Integration：
- PostGIS
- API
- Redis
- Celery
- MinIO
- auth
- audit
- OpenAPI generation

Contract：
- JSON Schema
- OpenAPI
- TS client

E2E：
H5 先完整跑：
- create pet
- search
- map
- place
- evaluate
- contribution
- operator claim
- dispute
- admin review

平台：
- 微信
- Android
- iOS
- HarmonyOS

若本机缺签名/证书/SDK：
- 不伪造通过；
- 其余继续；
- 写 BLOCKERS；
- 给精确人工步骤。

---

# 42. 安全 Gate

上线前：
- secrets scan
- dependency audit
- RBAC
- rate limit
- upload validation
- audit log
- permissions
- SDK privacy disclosure
- PII inventory
- dispute workflow
- backup/restore
- migration rollback
- error monitoring

---

# 43. 合规 Gate

必须人工确认：

1. 地图 provider 最新合同和持久化许可；
2. 自定义 Polygon/地图业务边界；
3. 微信类目和定位权限；
4. Android/iOS/HarmonyOS 权限披露；
5. 个人信息清单；
6. 图片 TTL；
7. 服务犬表述；
8. UGC 申诉；
9. 上架主体/备案；
10. 若接第三方社交数据，单独审查协议。

工程等待合规时必须用 feature flag/Mock 继续做，不得全停。

---

# 44. 发布阶段

Stage A — Local Vertical Slice  
DB/API/evaluator/admin/H5/synthetic seed 真跑通。

Stage B — MVP Alpha  
Map/Pet/Place/Zone/Rule/Source/Contribution/Operator/Dispute。

Stage C — Real Provider  
腾讯地图/真实登录/对象存储/AI/通知。

Stage D — Pilot  
一个区域真实采集。

Stage E — Store RC  
微信/Android/iOS/HarmonyOS + 隐私 + Crash + Release Checklist。

---

# 45. 开发冻结决策

1. 核心是 Access，不是 Friendly。
2. 地图是主入口。
3. 支持携宠、限制普通宠物、服务犬、规则地图。
4. Pet 支持 AI 建议 + 用户确认。
5. Place → Zone → Rule。
6. 自有 Place UUID。
7. 外部 POI 只 ExternalRef。
8. Observation 不自动变 Rule。
9. evaluator 为确定性程序。
10. AI 不做最终判断。
11. 多维 Provenance。
12. 管理方声明与观察共存。
13. 小区不记录住户。
14. 不做遇宠率。
15. 不做排行榜/评论区。
16. MVP 不依赖大规模爬虫。
17. 客户端 uni-app x + Vue3 + TS。
18. API FastAPI。
19. DB PostgreSQL + PostGIS。
20. 腾讯地图 MVP provider，Adapter 化。
21. Admin Vue3。
22. OpenAPI contract SSOT。
23. Rule/Source/History/Dispute 可审计。
24. 合规未确认项 feature flag，不阻止无关开发。

---

# 46. Demo 数据

默认虚构：

- 星河咖啡·测试店
- 青岚公园·演示
- 云栖中心·测试商场
- 松风社区·演示

还必须包含：
- service dog 与普通宠物不同的场所
- rule conflict
- stale rule
- operator claimed place
- dispute
- Observation 与 Rule 不一致但并存

真实场所只有在 source/verification 明确时进入生产数据。

---

# 47. 外部研究参考（截至 2026-09-06）

技术：
- uni-app x：https://uniapp.dcloud.net.cn/uni-app-x/readme
- uni-app x 定位：https://uniapp.dcloud.net.cn/uni-app-x/api/get-location.html
- uni-app map：https://uniapp.dcloud.net.cn/component/map
- 高德服务协议：https://lbs.amap.com/pages/terms/

产品：
- Dog Free Zone Map：https://dog-free.com/
- DogMap：https://map.pfotenpiloten.org/up/
- BringFido：https://www.bringfido.com/
- DogPack：https://www.dogpackapp.com/
- GoDoggo：https://www.godoggo.app/
- Spokin：https://www.spokin.com/verified-restaurants
- AccessNow：https://accessnow.com/verified/

另核验过：
- 上海公园宠物友好查询/分区
- 上海金山宠物友好地图
- 苏州工业园区宠物友好地图
- 广州公共宠物友好空间政府信息
- 深圳/上海等养犬管理条例
- 个人信息保护法
- 无障碍环境建设法
- 民法典
- 地图管理条例

这些是设计参考，不代表有权批量复制其数据。

---

# 48. 最终定义

> **宠物准入信息平台是一个以具体动物/用户需求为查询上下文、以现实空间地图为载体、以结构化准入规则为核心，同时支持携宠、普通宠物限制和服务犬通行，并融合官方规则、管理方声明、现场核验和用户观察的动物准入信息系统。**

用户最终看到的不是数据库，而是一句可行动的答案：

> **“豆豆可以去这里，但只能进入户外区域，需要牵引；该规则由管理方确认，最近一次现场核验为 2026-09-04。”**
