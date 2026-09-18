# B5 坐标补录 + BATCH_02 生产发布报告

日期：2026-09-18 · 评审员署名：`huangdi97` · 目标库：`petaccess`（PRODUCTION）

本轮执行了两件事，顺序是**先补坐标，再发布**（发布会把更多带规则的场所暴露给
`/places/nearby`，反过来做会先制造一批搜不到的场所）。

---

## 1. B5：坐标补录（`PLACE_GEO_PENDING` → 关闭）

### 为什么补，而不是改 API

`/places/nearby` 的过滤条件是 `Place.location IS NOT NULL`。坐标缺失的场所不是"较难找到"，
而是**在附近搜索里根本不存在，且没有任何提示**。BATCH_02 一旦发布，带已发布规则却搜不到的场所
会从 2 个变成 6 个。修数据比改 API 语义安全，因此选了补坐标。

### 数据来源与精度分级

环境里没有配置地图服务凭据（`MAP_PROVIDER=mock`、`TENCENT_MAP_KEY_SERVER` 为空），
因此地理编码走 OpenStreetMap Nominatim（ODbL）。**每一条都保留了 OSM 溯源**
（`osm_type`/`osm_id`/`display_name`/查询串/抓取时间），可逐条复核，而不是"信我"。

精度分两级，**从不混写**：

| 级别 | 含义 | 命中条件 | 条数 |
|---|---|---|---|
| `AUTO_MATCHED`（名称级） | OSM 里就是这个场所 | 上海 bbox 内 + OSM `display_name` 含场所名 n-gram（≥3 字） | 8 |
| `ADDRESS_LEVEL`（地址级） | OSM 不认识这家店，用场所自带的 `canonical_address` 定位 | 上海 bbox 内 + 查询串与 `display_name` 最长公共子串 ≥4 字 | 2 |
| `NEEDS_HUMAN` | 两者都不成立 → **永不写入** | — | 0 |

### 补录结果（10/10）

| 场所 | 纬度, 经度 | 级别 | OSM 溯源 |
|---|---|---|---|
| 上海动物园 | 31.195116, 121.357905 | 名称 | `上海动物园, 2381, 虹桥路, 长宁区` |
| 上海博物馆东馆 | 31.222116, 121.534357 | 名称 | `上海博物馆东馆, 杨高南路, 浦东新区` |
| 上海新天地朗廷酒店 | 31.223726, 121.469893 | 名称 | `上海新天地朗廷酒店, 99, 马当路, 黄浦区` |
| 上海苏河湾万象天地 | 31.244370, 121.473874 | 名称 | `苏河湾万象天地, 北站街道, 静安区` |
| 上海蟠龙天地 | 31.190999, 121.271561 | 名称 | `蟠龙天地, 123, 蟠龙, 徐泾镇, 青浦区` |
| 世纪公园 | 31.218799, 121.548627 | 名称 | `世纪公园, 1001, 花木街道, 浦东新区` |
| 兴业太古汇 | 31.230982, 121.458519 | 名称 | `兴业太古汇, 南京西路街道, 静安区` |
| 西岸梦中心（Gate M） | 31.162343, 121.461593 | 名称 | `西岸梦中心, 龙华街道, 徐汇区` |
| CHARLIE'S 粉红汉堡（马当路店） | 31.213416, 121.472386 | **地址** | 查询 `中海环宇荟` → `中海环宇荟, 卢家湾, 打浦桥街道` |
| omitofee 上海首店 | 31.038389, 121.483374 | **地址** | 查询完整地址 → `浦江郊野公园滨江漫步区, 浦江镇, 闵行区` |

两条地址级的说明：CHARLIE'S 在 OSM 里没有门店条目，落点是它所在的商场「中海环宇荟」
（注意不是马当路新天地段的那个坐标，两者相距约 1.4 km）；omitofee 落点是它所在的
浦江郊野公园滨江漫步区。**这两条的位置精度是街区/园区级，不是门店级**，已在 `audit_log.detail.precision`
中标记为 `address_level`，待运营方确认门牌后可覆盖。

### 写入与留痕

```
place_geo_backfill.py --db-name petaccess --apply --reviewer huangdi97 --production-confirm
→ applied=10  already_had_coords=0  no_such_place=0
→ places=20  still_missing_geo=0
```

每个场所写一条 `audit_log`（`action=place.update`），`detail` 里带来源、匹配方法、
精度级别与署名。补录**不触碰任何规则数据**。

---

## 2. BATCH_02 生产发布

清单：`docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_02.json`
登记表：`docs/expansion/review_decisions_expansion_r1_wave01_publishable.json`

```
BATCH_SELECTED = 6   BATCH_ACCESS_RULE = 6   BATCH_RULE_EXCEPTION = 0
BATCH_DEPENDENCY_CLOSED = PASS                BATCH_VALIDATION = PASS
PREPUBLISH_APPROVED_EVALUATED = 6  PASS = 6  BLOCKED = 0
ACCESS_RULE_CREATE_COUNT = 6   failed = 0
```

| # | rule_id | 场所 | 层 | 发布的规则 |
|---|---|---|---|---|
| 1 | `w01-052d19ccba` | CHARLIE'S 粉红汉堡（马当路店） | LEGAL | `bb259b10…` |
| 2 | `w01-7de2f5d75b` | omitofee 上海首店 | LEGAL | `519e0779…` |
| 3 | `w01-df1645fe68` | 上海新天地朗廷酒店 | LEGAL | `39ee0061…` |
| 4 | `w01-8ba2b49b01` | 上海苏河湾万象天地 | LEGAL | `8f6e597c…` |
| 5 | `w01-d1aee78159` | 前滩太古里 | LEGAL | `42c9a35e…` |
| 6 | `w01-e951785d1b` | 港汇恒隆广场 | LEGAL | `6f51e8c0…` |

### 但书这一次真的改变了答案

`JPROV-001` 激活时（见 `ADR030_JPROV001_ACTIVATION_REPORT.md`）当前答案 delta = 0，
因为当时 5 条 LEGAL 基底各自都已有场所级例外。这次新发布的 6 条没有手写例外，A/B 对照
（同一批实时行跑两遍：不带 / 带但书）显示：

```
CHARLIE'S  @ 室内用餐区        导盲犬 prohibited → allowed   [CHANGED]
omitofee   @ 室内空间          导盲犬 prohibited → allowed   [CHANGED]
朗廷       @ 客房内部          导盲犬 prohibited → allowed   [CHANGED]
苏河湾万象天地 @ 室内商铺及公共区域 导盲犬 prohibited → allowed   [CHANGED]
前滩太古里 @ 商场室内空间        导盲犬 prohibited → allowed   [CHANGED]
港汇恒隆   @ 商场室内公共区域      导盲犬 prohibited → allowed   [CHANGED]
普通犬：11 条 LEGAL 基底全部 prohibited → prohibited [same]
verdict = PASS
```

也就是说：**新发布的 LEGAL 禁犬基底不再需要逐场所补一条手写 carve-out**——这是 ADR-030
的前瞻价值第一次落到真实数据上。

---

## 3. 验证

| 项 | 结果 |
|---|---|
| 幂等复跑 | `NOOP_COUNT = 6`、`CREATE = 0`、`BLOCKED = 0` |
| 排除项未被发布 | 4 条仍 `REVIEW_PENDING` 且 `published_rule_id IS NULL`；5 条是 BATCH_01A 已发布（reason 明确区分，未与"被否决"混写） |
| 指纹 A→B（补坐标） | `a4f55b14…` → `f40223e0…`：仅 `place` 摘要变化 + `audit_log` +10 |
| 指纹 B→C（发布） | `f40223e0…` → `37b4294c…`：`access_rule` 8→14（+6）、`audit_log` +12、`rule_candidate` 6 行改写 `published_rule_id`；`rule_exception`/`jurisdiction_exception`/`place` 均不变 |
| `/places/nearby` 探针 | 上海博物馆东馆、世纪公园、CHARLIE'S、omitofee、西岸梦中心 全部 `self_found=True` |
| 完整性扫描 | `PRODUCTION_INTEGRITY_SCAN = PASS`；Critical/High 全 0；唯一 MEDIUM 是历史遗留 `AUDIT_TARGET_ID_UNUSABLE` 2647 行（本轮前后不变） |

生产库当前：`access_rule = 14`、`rule_exception = 5`、`jurisdiction_exception = 1`、
`rule_candidate = 68`、`place = 20`（缺坐标 0）、`audit_log = 9640`。

---

## 4. 仍然开着的事

1. **2 条地址级坐标待确认**——CHARLIE'S（中海环宇荟）、omitofee（浦江郊野公园滨江漫步区）
   精度为街区/园区级，需运营方门牌确认后覆盖。
2. **4 条 APPROVED 候选仍不可执行**（不是被否决，登记表中决策未被改动）：
   `SOURCE_SCOPE_NORMALIZATION_NOT_SEMANTICALLY_*` ×2（迪士尼/动物园，走 B2 scope remodel）、
   `INREACHABLE_APPROVED_CARVE_OUT` ×1、`ADR021_UNVERIFIED_SEARCH_SNIPPET` ×1（世纪公园，走 B4）。
3. **B2** 新 revision 审查包已就绪（`SCOPE_REMODEL_REVISION_R2_HUMAN_REVIEW_PACKET.md`），
   等人工审查；**B4** 世纪公园一手来源仍 `STILL_MISSING`。

## 5. 环境备注

本轮开始时 PostgreSQL 容器不在运行（Docker Desktop 未启动）。Docker Desktop 无法由本会话
可靠拉起，需先手动启动，再 `docker compose up -d`。补录脚本另有一处环境坑：本机
`HTTP_PROXY=http://127.0.0.1:10808`，httpx 若用 `trust_env=False` 会全部超时——
表现是"OSM 查不到"，实际是"根本没发出请求"。
