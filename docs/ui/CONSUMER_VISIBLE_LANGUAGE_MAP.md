# Consumer Visible Language Map（消费者可见语言 SSOT）

> Goal §30：禁止页面各自 `if enum === ...` 到处翻译；内部 enum 存在于 API/model，Consumer 层只输出用户语言。
> 本表是本轮视觉保真恢复的可见文本映射单一来源；实现位于 `apps/client-h5/src/consumer/labels.ts`（新增统一 mapper，组合 client-core 既有 `placeTypeLabel/conditionLabel/freshnessLabel` 与 H5 `answer.ts/reality.ts` 词汇）。

## 1. Animal scope（动物范围）

| 原始值 | 消费者显示 |
|---|---|
| `dog` | 犬 |
| `cat` | 猫 |
| `ordinary_pet` | 普通宠物 |
| `service_dog` | 服务犬 |
| `other` | 其他动物 |

## 2. Rule action（动作）

| 原始值 | 消费者显示 |
|---|---|
| `enter` | 进入 |
| `pass_through` | 通行 |
| `stay` | 停留 |
| `walk` | 散步 |
| `off_leash` | 放开牵引 |
| `ground_contact` | 落地 |
| `ride_elevator` | 乘坐电梯 |
| `ride_transport` | 乘坐交通工具 |
| `use_facility` | 使用设施 |
| `dine` | 用餐 |
| `stay_overnight` | 过夜 |

## 3. Zone type（空间/区域）

| 原始值 | 消费者显示 |
|---|---|
| `area` | 公共区域 |
| `floor` | 楼层 |
| `children_area` | 儿童区 |
| `pet_area` | 携宠区 |
| `lawn` | 草坪 |
| `plaza` | 广场 |
| `road` | 道路 |
| `supermarket` | 超市 |
| `dining_area` | 堂食区 |
| `entrance` | 入口 |
| `elevator` | 电梯 |
| `other` | 其他区域 |

## 4. Rule status（规则状态）

| 原始值 | 消费者显示 |
|---|---|
| `current` | 当前生效 |
| `superseded` | 已被取代（历史） |
| `withdrawn` | 已撤回 |
| `disputed` | 存在争议 |
| `archived` | 已归档 |
| `pending_review` | 待复核 |

## 5. Rule layer / mandatory level（规则分层与效力）

| 原始值 | 消费者显示 |
|---|---|
| `LEGAL` | 法规 |
| `REGULATORY_GUIDANCE` | 监管指引 |
| `OPERATOR_POLICY` | 运营方政策 |
| `TEMPORARY_POLICY` | 临时/事件政策 |
| `mandatory` | 强制 |
| `advisory` | 建议 |
| `operator_discretion` | 运营方裁量 |

## 6. Observed action（现场观察动作）

| 原始值 | 消费者显示 |
|---|---|
| `entered` | 进入 |
| `present` | 在场 |
| `stayed` | 停留 |
| `dined_near_table` | 在餐桌附近用餐 |
| `on_customer_seat` | 在顾客座椅上 |
| `on_table_surface` | 在桌面上 |
| `near_food_service` | 在食品服务区附近 |
| `in_self_service_food_area` | 在自助食品区 |
| `leashed` | 牵引中 |
| `off_leash` | 未牵引 |
| `in_carrier` | 装载中 |
| `in_stroller` | 推车中 |

## 7. Staff action（工作人员处理）

| 原始值 | 消费者显示 |
|---|---|
| `explicitly_allowed` | 明确允许 |
| `explicitly_refused` | 明确拒绝 |
| `asked_to_remove` | 要求带离 |
| `no_interaction_observed` | 未观察到干预 |
| `interaction_unknown` | 干预情况未知 |

## 8. Facility（设施与状态）

| 原始值 | 消费者显示 |
|---|---|
| `active` | 正常使用中 |
| `temporarily_unavailable` | 暂时不可用 |
| `removed` | 已移除 |
| `unknown` | 状态未知 |
| AMENITY enums | 宠物饮水 / 拾便袋 / 宠物厕所 / 宠物清洗 / 推车租借 / 拴宠点 / 宠物寄存 / 宠物电梯 / 宠物入口 / 宠物活动区 |

## 9. Coexistence（共处边界）

| 原始值 | 消费者显示 |
|---|---|
| `ordinary_pet_indoor_dining` | 室内堂食 |
| `ordinary_pet_outdoor_dining` | 户外堂食 |
| `animal_on_customer_seat` | 顾客座椅 |
| `animal_on_table_surface` | 桌面 |
| `animal_near_food_service_area` | 食品服务区附近 |
| `animal_in_self_service_food_area` | 食品自助区 |
| `animal_use_customer_tableware` | 使用顾客餐具 |
| `dedicated_pet_tableware` | 专用宠物餐具 |
| `dedicated_pet_zone` | 独立携宠区 |
| `zone_separation` | 区域分隔 |
| value `allowed` | 允许 |
| value `prohibited` | 禁止 |
| value `conditional` | 有条件 |

## 10. Entrance（入口）

| 原始值 | 消费者显示 |
|---|---|
| `GENERAL` | 通用入口 |
| `PET_DESIGNATED` | 指定携宠入口 |
| `SERVICE` | 服务通道 |
| `PARKING_CONNECTION` | 车库连接 |
| `OTHER` | 其他 |

## 11. 不可见原值（absolute ban）

- UUID / 数据库 PK / internal object id（含 `id.slice(0,8)` 片段）→ `场所信息暂不可用` / `来源信息暂不可用`
- `NO_RECENT_RECORD` 等 invariant → `暂无近期现场记录。这并不代表现场没有动物。`
- `superseded` / `pending_review` / `candidate` / `reality_report` / `floor` 等 workflow/zone 词 → 上表消费者语言

## 12. 使用纪律

- Search/Place 页面只 import `apps/client-h5/src/consumer/labels.ts` 暴露的函数；禁止页面内再写 `if (x === "pet_area")`。
- fallback 一律为消费者安全词（如「其他区域」「来源信息暂不可用」），绝不把 raw value 原样输出。
