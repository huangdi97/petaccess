# 生产库数据完整性（PRODUCTION_DATA_INTEGRITY）

> `scripts/check_production_integrity.py`：23 项只读检查 + 不可覆盖基线。
> 轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`。

## 1. 运行

```bash
export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"

# 默认写 artifacts/production_isolation/；同文件已存在则拒绝覆盖（除非 --replace）
PYTHONPATH= .venv/Scripts/python.exe scripts/check_production_integrity.py --out <path>
```

脚本只读：`SELECT` only，不建临时表、不开事务、不 `COMMIT`。

## 2. 检查项（23）

| 严重度 | 检查 | 问题 |
|---|---|---|
| CRITICAL | `HOLD_OR_REJECTED_PUBLISHED` | 是否有 HOLD/REJECTED 的候选被发布 |
| CRITICAL | `CROSS_LAYER_EXCEPTION` | current 例外是否挂在无层级 base 上 |
| CRITICAL | `ORPHAN_RULE_EXCEPTION` | RuleException 是否指向不存在的 base |
| CRITICAL | `SELF_SUPERSEDE` | 是否有规则 supersede 自己 |
| CRITICAL | `SUPERSESSION_CYCLE` | 是否存在 supersession 环 |
| CRITICAL | `CONFLICTING_CURRENT_RULES` | 同 (place/zone/layer/scope/action) 两条 current 且 effect 不同 |
| HIGH | `DUPLICATE_CURRENT_RULE` | 同键上多条 current |
| HIGH | `ORPHAN_PLACE_RELATION` | parent_place_id / parent_zone_id 悬空 |
| HIGH | `ORPHAN_ZONE` | zone 指向不存在的 place |
| HIGH | `PUBLISHED_OBJECT_WITHOUT_CANDIDATE` | 已发布 AccessRule 无候选血缘 |
| HIGH | `PUBLISHED_WITHOUT_AUDIT` | 缺 `candidate.publish` 审计 |
| HIGH | `PUBLISHED_WITHOUT_EVIDENCE` | 缺 EvidenceBundle |
| HIGH | `PUBLISHED_WITHOUT_SOURCE` | 缺 Source |
| HIGH | `TEST_ACCOUNT_IN_PRODUCTION` | 一次性测试账号残留 |
| HIGH | `TEST_FIXTURE_PLACE_IN_PRODUCTION` | 测试夹具场所残留 |
| HIGH | `TEST_FIXTURE_SOURCE_IN_PRODUCTION` | 测试夹具 Source 残留 |
| MEDIUM | `AUDIT_TARGET_ID_UNUSABLE` | audit `target_id` 不能用于血缘追溯 |
| MEDIUM | `DUPLICATE_MONITOR` | 同一 source 重复监控 |
| MEDIUM | `INVALID_CURRENT_STATUS` | status 取值非法 |
| MEDIUM | `INVALID_FRESHNESS_METADATA` | freshness 元数据非法 |
| MEDIUM | `STALE_MONITOR` | 监控长期未刷新 |
| INFO | `ORPHAN_SOURCE` | 无人引用的 Source |
| INFO | `RULES_WITHOUT_PLACE` | 既不挂 place 也不挂 zone 的规则 |

## 3. 本轮实测

### 清理前（`production_integrity_baseline.json`）

```
CONFLICTING_CURRENT_RULES          2   CRITICAL
DUPLICATE_CURRENT_RULE             2   HIGH
TEST_FIXTURE_PLACE_IN_PRODUCTION   1231 HIGH
TEST_FIXTURE_SOURCE_IN_PRODUCTION  1423 HIGH
TEST_ACCOUNT_IN_PRODUCTION         1636 HIGH
PUBLISHED_WITHOUT_EVIDENCE         64   HIGH
AUDIT_TARGET_ID_UNUSABLE           4    MEDIUM
```

### 第一批清理后（`production_integrity_after_cleanup.json`）

```
TEST_FIXTURE_PLACE_IN_PRODUCTION      0
TEST_ACCOUNT_IN_PRODUCTION            0
PUBLISHED_WITHOUT_EVIDENCE            0
PUBLISHED_WITHOUT_AUDIT               0
PUBLISHED_WITHOUT_SOURCE              0
TEST_FIXTURE_SOURCE_IN_PRODUCTION    68   <-- 仍然 68，见下
```

### 第二批清理后（`production_integrity_after_batch02.json`）

| 项 | 严重度 | 值 | 说明 |
|---|---|---|---|
| `CONFLICTING_CURRENT_RULES` | CRITICAL | **2** | 青岚公园·演示 Zone「A 草坪」的双 current，已分类 `MANUAL_REVIEW_REQUIRED` |
| `DUPLICATE_CURRENT_RULE` | HIGH | **2** | 同一对象的另一指标 |
| `AUDIT_TARGET_ID_UNUSABLE` | MEDIUM | 4 | audit_log 追加式，历史字符串 `'None'`，不可修 |
| `ORPHAN_SOURCE` | INFO | 1 | 无引用来源 |
| `RULES_WITHOUT_PLACE` | INFO | 17 | zone 级规则（设计如此） |
| 其余 18 项 | | 0 | 含全部 `TEST_FIXTURE_*` 与 `PUBLISHED_WITHOUT_*` |

## 4. 为什么第一批之后还剩 68

`jurisdiction_rule` 没有 `place_id`，第一批完全没覆盖它；而
`jurisdiction_rule.source_id` 是 **RESTRICT**，于是 68 条
`jurisdiction_id='test-city'` / `authority='测试机关'`（两个字符串都是
`tests/integration/test_operator_contribution.py:236,246,247` 的字面量）把
68 条 `测试法规来源` 一起钉在库里。**"某张表没被外键连到"不等于"它干净"。**
第二批补上后归零。

## 5. 已知不可自动消除项

| 项 | 值 | 为什么不能归零 |
|---|---|---|
| `CONFLICTING_CURRENT_RULES` / `DUPLICATE_CURRENT_RULE` | 2 / 2 | 发布**之前**就存在的 demo 语义问题（2026-05-15 与 2026-08-13 各一条，互斥）。修它等于改 demo 数据语义，属人类决策。见 `PRODUCTION_DUPLICATE_CURRENT_AUDIT.md` |
| `AUDIT_TARGET_ID_UNUSABLE` | 4 | `audit_log` 是追加式历史（`source` 1379 行、`place` 1185 行、`jurisdiction_rule` 68 行…），删除审计行本身破坏审计性 |
| `ORPHAN_SOURCE` / `RULES_WITHOUT_PLACE` | 1 / 17 | INFO 级，设计如此（zone 级规则本来就不挂 place） |

## 6. 生产只读冒烟（`verify_publish_r3.py --skip-drills`）

`--skip-drills` 只跑 linkage / resolver / engine 一致性，不改造库状态。
本轮对 `petaccess` 的实测（`PRODUCTION_READONLY_SMOKE.json`）：

```
SOURCE_LINKAGE             = PASS
EVIDENCE_LINKAGE           = PASS
AUDIT_LINKAGE              = FAIL
RESOLVER_POST_PUBLISH      = PASS
EFFECTIVE_RULES_API        = PASS
ENGINE_CONSISTENCY         = PASS
CARVE_OUT_REACHABILITY     = PASS
ZERO_INERT_RULES           = PASS
  [carve_out] 已发布 carve-out 3 条，可达 3 条，UNREACHABLE = 0，UNEVALUABLE = 0
```

### `AUDIT_LINKAGE = FAIL` 的定性：**契约不一致，不是审计缺失**

细节：`审计不足：candidate.publish_exception 只有 0 条，应为 3`。
但三条 carve-out 各有审计记录，只是动作名不同：

```
b8cffbee… / caa28a93… / e94d2259…
  candidate.create / candidate.transition / candidate.set_rule_layer /
  candidate.set_mandatory_level / candidate.set_scope
  candidate.transition  2026-09-17 07:19:01   <- 发布那一刻
```

原因：`candidate.publish_exception` 这个动作名只在 **HTTP 路由**
（`services/api/app/api/v1/v05.py:560`）里写；CLI 发布器调用的
`candidate_service.publish_exception()` **不写审计行**（只写 `candidate.transition`）。
所以事件被记录了、粒度与演练脚本的期望不同。

- 不是数据缺陷：3 条 carve-out 存在、`current`、base 与层级正确，
  `CARVE_OUT_REACHABILITY = PASS`、`ZERO_INERT_RULES = PASS`、`RESOLVER_POST_PUBLISH = PASS`。
- **没有**回补审计行：那是对已发布对象追加写入，违反 §1/§2 冻结。
- 待办（下一轮，需人类授权）：让 `candidate_service.publish_exception()`
  自己写 `candidate.publish_exception` 审计，使两条发布路径的审计粒度一致。
