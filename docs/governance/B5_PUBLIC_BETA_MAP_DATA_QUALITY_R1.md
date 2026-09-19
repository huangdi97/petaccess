# B5 · 剩余坐标质量归入 PUBLIC_BETA_REAL_MAP_DATA_QUALITY_ITEM

轮次：`PUBLIC_BETA_REAL_MAP_DATA_QUALITY_ITEM_R1`
决定人：`huangdi97`（2026-09-19 四项之一 · 项目 G）
性质：**不再阻挡规则治理闭环**

---

## 0. 结论指标

```
PLACE_TOTAL                              = 20
PLACE_WITH_COORDINATES                   = 20
PLACE_MISSING_COORDINATES                = 0
GEO_PRECISION_NAME_LEVEL                 = 8
GEO_PRECISION_ADDRESS_LEVEL              = 2
GEO_NEEDS_HUMAN                          = 0
AUDIT_LOGGED_PER_PLACE                   = 1
BLOCKS_RULE_GOVERNANCE_CLOSURE           = NO
RETIRED_FROM_ACTIVE_TRACK                = YES
NEW_STATUS                               = PUBLIC_BETA_REAL_MAP_DATA_QUALITY_ITEM
```

```
HUMAN_ACTION_REQUIRED = NONE_FOR_RULES
HUMAN_ACTION_OPTIONAL = 两条地址级场所的门牌/租户单元确认（可在 Public Beta 前任意时点补充）
```

---

## 1. 当前实测（`petaccess` 生产，2026-09-19 只读）

```
place                        = 20
  location is not null       = 20
  location is null           = 0
```

20/20 已有坐标。没有任何 place 缺坐标，因此 B5 已不再携带「补坐标」这个动作。

## 2. 剩余的真实问题：两条坐标精确到「所在楼宇/园区」，不是门店本身

| 场所 | 当前落点 | 精度 | OSM 溯源 |
|---|---|---|---|
| CHARLIE'S 粉红汉堡（马当路店） | 31.213416, 121.472386 | `address_level` | 查询 `中海环宇荟` → `中海环宇荟, 卢家湾, 打浦桥街道` |
| omitofee 上海首店（浦江郊野公园滨江漫步区） | 31.038389, 121.483374 | `address_level` | 查询完整地址 → `浦江郊野公园滨江漫步区, 浦江镇, 闵行区` |

两家在 OSM 里都没有门店级条目：

- CHARLIE'S 的落点是它所在的商场建筑「中海环宇荟」。**注意不是马当路新天地段那个同名坐标**，两者相距约 1.4 km。
- omitofee 的落点是它所在的浦江郊野公园滨江漫步区，园区级而非单元级。

精度标记已经随 `audit_log.detail.precision = address_level` 入档 —— 它是当前事实的诚实记录，不是「以后再补」的欠条。

## 3. 为什么它不再阻挡规则治理

这两个点位的语义是「这个场所大概在哪里」，而规则治理链路消费的是 `place_id` / `zone_id`，不是经纬度本身：

- Resolver 按 place/zone 判定准入，坐标不参与 resolution；
- 已发布的 19 条 `access_rule` 全部挂在 place/zone 上；
- 因此这两个点是**展示层/地图层**的质量问题，不是准入答案的正确性问题。

但这不等于不重要：在 Public Beta 的真实地图上，一个偏离 1.4 km 的门店落点会把用户导航到错误的地方。所以它是 **Public Beta 之前必须处理的真实地图数据质量项**，而不是被关闭的项。

## 4. 处理路径（任一时点，不阻塞本轮之后的任何规则发布）

1. 取运营方确认的门牌 / 租户单元；
2. 用门牌重新地理编码，**或**直接用现场采集坐标；
3. 覆盖为满足 ≤ 门牌精度的坐标；
4. 写一条新的 `place.update` audit（`detail.precision = unit_level`）。
   **旧的 `address_level` audit 不改写** —— 它是这一对坐标曾经精度的历史，删掉会让事实消失。

## 5. 明确不做的事

- ❌ 用场所名猜坐标（这两家的教训：名称里的「马当路店」指向了另一个商圈）
- ❌ 用 POI 邻接关系推断门店单元
- ❌ 在缺一手运营方来源时把 `address_level` 标成 `unit_level`
- ❌ 因为是地图问题就允许它反过来重新堵塞规则发布闸门
