# WAVE02 DATA PIPELINE & REVIEW PACKET — 执行报告

轮次：`30_50_PLACE_EXPANSION_R1 — WAVE_02`
基线：HEAD `aee7bb8`（含 AccessAnswer 迁移）· 生产库 `petaccess`（PRODUCTION）· alembic `f2a1c7d9e034`
本轮生产写入：**10 个真实 Place + 配套 Source/Artifact/EvidenceBundle/Zone/SourceMonitor 元数据 + 20 条 REVIEW_PENDING RuleCandidate**
本轮未写：**任何 Rule / Exception / supersede / publish 记录；无任何 Human 字段**

---

## 0. 结论指标

```
REAL_PLACE_COUNT                = 20 → 30
WAVE02_NEW_REAL_PLACES          = 10
REAL_COORDINATE_COVERAGE        = 30 / 30
WAVE02_CANDIDATES               = 20
WAVE02_REVIEW_PENDING           = 20
WAVE02_HUMAN_FIELDS_SET         = 0
SOURCE_MONITOR_REQUIRED         = 9（9 个独立来源，和平/昆山共享虹口 pilot）
SOURCE_MONITOR_CREATED          = 9
ACCESS_RULE_CREATED             = 0     （26 不变）
RULE_EXCEPTION_CREATED          = 0     （9 不变）
§29 GATE PROBE                  = 全 PASS（13 项 × 20 候选）
PRODUCTION_INTEGRITY_CRITICAL   = 0
PRODUCTION_INTEGRITY_HIGH       = 0
REAL_PUBLISH_WAVE02             = NO
HUMAN_ACTION_REQUIRED           = WAVE02_FINAL_DECISIONS
```

## 1. 新增 10 个真实场所（OSM 真实坐标，含 provenance）

| 场所 | district | place_type | 来源 | 说明 |
|---|---|---|---|---|
| 上海植物园 | 徐汇区 | park | 园方《游园守则》+ 市级守则 | 动物→dog/cat/other 拆分 |
| 共青森林公园 | 杨浦区 | park | 官网《文明游园守则》 | 动物→拆分 |
| 上海世博文化公园 | 浦东 | park | 官网《游园须知》 | 动物→拆分；后滩滨江例外待核验 |
| 豫园 | 黄浦区 | scenic_area | 官网《游园须知》 | 宠物禁 + 导盲犬例外（保留单角色） |
| 上海自然博物馆 | 静安区 | museum | 官网《参观须知》 | 宠物 exact 禁 |
| 上海野生动物园 | 浦东 | scenic_area | 官网《游园指南》 | 宠物 exact 禁（区别于上海动物园） |
| 上海辰山植物园 | 松江区 | park | 官网《游园指南》 | 宠物 exact 禁 |
| 和平公园（虹口试点） | 虹口区 | park | 区政府携宠试点公告 | 犬/猫 conditional（限时/嘴套/牵引） |
| 昆山公园（虹口试点） | 虹口区 | park | 区政府携宠试点公告 | 犬 conditional（限时/嘴套/牵引） |
| 顾村公园 | 宝山区 | park | 本地宝（二级→lead） | 动物→拆分；needs_verification |

坐标全部来自 OpenStreetMap Nominatim（ODbL）：每个 Place 保留 `geo.osm_type/osm_id/
display_name/licence/query/fetched_at/manual_verified=false`，杜绝随机坐标、
UUID 派生坐标、LLM 猜测、MockMap 冒充。

## 2. 证据链与审计闭环

`scripts/expansion_w02_ingest.py` 走生产 API（DataSourceJob → Source → SourceArtifact →
EvidenceBundle → RuleCandidate），每写带 `expansion_run_id=EXP-R1-W02-20260919` 且
`dedup_key` 幂等；DataSourceJob `finish` 记录 `result_counts`。共：
11 sources（10 place + 1 shared 市级守则）、11 artifacts、10 bundles、10 zones。

期间发生过一次 scope 编码修正：第一批 15 条的 `动物/other/…` 等不合法编码被
`scripts/wave02_candidate_correction.py` 清理并重灌为正确的
`compound_term_split`（dog/cat/other）与已声明阅读；`rulespec/source_scope_semantics.py`
补充 `犬类`→dog、`猫类`→cat 阅读并 pin 测试。重复 monitor 由
`scripts/wave02_monitor_dedup.py` 清理（保留每 source 最早一条）。

## 3. §29 全门禁（只读 probe）

`scripts/wave02_section29_gates.py`：对 20 条候选逐条评估 13 项 §29 gate，
全部 PASS、零 NOT_RUN、零 DB 突变：

```
SOURCE_SCOPE_SEMANTICS  PASS 20   LEGAL_OPERATOR_LAYERING PASS 20
ZONE_SCOPE              PASS 20   EXCEPTION_REACHABILITY  PASS 20
ADR030                  PASS 20   ADR031                  PASS 20
EVIDENCE                PASS 20   FRESHNESS               PASS 20
LICENSE                 PASS 20   CONFLICT                PASS 20
SUPERSESSION            PASS 20   GUIDE_DOG_SAFETY        PASS 20
CONDITION_SCHEMA        PASS 20
```

语义红线全部保持：`动物` 仅作当前 ontology 可表达拆分（未建模动物保持 UNKNOWN）、
导盲犬例外只落 guide_dog 单角色不泛化、`other` 不做「全部动物」等价声明、
政府/二级来源不静默升级、UNKNOWN 不自动 ALLOWED。

## 4. 人工复核包

`scripts/wave02_review_packet.py` 从生产库派生（只读）生成：

- `docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md`（按场所分组逐条；来源用词/归一化
  主体/scope/effect/layer/条件/说明）
- `docs/expansion/WAVE02_HUMAN_REVIEW_QUICK_TABLE.md`（速查表，决策列空白）
- `docs/expansion/review_decisions_expansion_r1_wave02.json`（20 行；所有 Human 字段
  `final_decision=null / reviewer="" / decided_at=null`）

复核人须知明确：`final_decision`（APPROVED/HOLD/REJECTED）须与 `reviewer`、`decided_at`
同时填写；`动物` 拆分行应成组审阅。

## 5. 未做（刻意）

- 未发布任何 Wave02 Rule/Exception（`REAL_PUBLISH_WAVE02 = NO`）。
- 未填任何 Human 决策字段；未代 Kaiser/huangdi97 签字。
- 未改写任何 Wave01 / 历史 Human Decision / 已发布对象。
- 未做 50 个场所；不做 Reality Audit（含门牌级核验）——留在 Wave02 人工决定后。
- 未越过 Wave02 人工检查点。

---

## 6. 下一步（需人工授权）

```
HUMAN_ACTION_REQUIRED = WAVE02_FINAL_DECISIONS
```

人类审阅 `docs/expansion/WAVE02_HUMAN_REVIEW_PACKET.md` 后逐条决定；
批准项才进入独立发布批次流程（届时另跑 pre-publish gate + 演练，本 Goal 不自动执行）。