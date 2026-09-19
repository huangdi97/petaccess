# ADR-032 · LegalProvision 与法定但书血缘的 additive model

轮次：`LEGAL_PROVISION_AND_STATUTORY_PROVISO_LINEAGE_R1`
决定人：`huangdi97`（2026-09-19 四项之一 · 第 4 项 LEGAL_PROVISION_MODEL）
性质：**独立 engineering track，不阻塞当前安全规则收口**
基线：`d1a3dbe`（本 track 开启时 HEAD）

---

## 0. 结论指标（本 track 开启时的状态）

```
LEGAL_PROVISION_MODEL_STATUS            = ADR_ACCEPTED / SCHEMA_DRAFTED
MUTATE_EXISTING_PUBLISHED_ROWS          = NO
EXISTING_PUBLISHED_ROWS_TOUCHED         = 0
EXISTING_AUDIT_EVENTS_REWRITTEN         = 0
NEW_DATA_PATH_IMPLEMENTED               = NO        （本 track 的下一步，非本轮）
HISTORICAL_BACKFILL_EXECUTED            = NO
PUBLIC_BETA_BLOCKER                     = NO
SEPARATE_FROM_SAFETY_RULE_CLOSURE       = YES
```

```
HUMAN_ACTION_REQUIRED = NONE_FOR_THIS_ROUND（本 track 只需被接受为方向；无发布、无迁移）
```

---

## 1. 为什么：现在的法条引用是「字符串」，不是「关系」

平台上唯一的法定但书是 `JPROV-001`。它的实际行（生产 `petaccess`，2026-09-19 只读核对）：

| 字段 | 值 |
|---|---|
| `id` | `JPROV-001` |
| `jurisdiction_level` / `jurisdiction_id` | `municipal` / `310000` |
| `instrument_type` | `statute_or_regulation` |
| `document_name` | 上海市养犬管理条例 |
| `clause_ref` | 第二十三条 |
| `proviso_text_ref` | 盲人携带导盲犬的，不受本条规定的限制。 |
| `source_id` | `f20bdb2c…` |
| `instrument_source_ids` | `['f20bdb2c…', 'a11aff10…']` |
| `applies_to_layer` | `LEGAL` |
| `binding` / `status` | `instrument` / `current` |

它工作，但它把一件有三层结构的事压成了一行字符串：

1. **条/款/项无法精确定位。** `clause_ref = "第二十三条"` 是一个不透明字符串。同一部法律的「第二十三条第一款第（二）项」和「第二十三条」在这个模型里无法区分，也不能校验「第（二）项」是否真存在于这一条里。
2. **proviso 与 provision 的关系是隐含的。** 但书「是对哪一条的例外」只能靠「它恰好和 `clause_ref` 在同一行」推断。同一条款有多个但书时，必须把整份 instrument/provision 描述复制一遍，任何一处修改都会在两份之间产生漂移。
3. **同一 provision 被多处引用时会漂移。** 今天 5 条 LEGAL 基底各引 `f20bdb2c…` / `a11aff10…` 之一；两行都是同一部条例的不同抓取。谁是「同一份法律文件」靠人工列表维护。
4. **temporal validity 只有一个全局变量。** 现行行有 `effective_from` / `effective_to`，表达的是「该例外何时生效」；没有表达「该条款在何时版本有效」。法律修订后，旧规则的 applicability 变化无从追溯。
5. **没有 Source/Evidence → Provision 的血缘。** `source_id` 是 1:1 的外键；「这条 provision 来自哪个 instrument 的哪一次快照」「证据 Bundle 支持的是哪一段原文」没有承载体。
6. **最危险的一条：没有地方写「不许猜」。** 今天「上海 + dog」能命中店里任何一个但书，只是因为当measured前恰好只有一个。模型没有任何字段能表达「这个但书只对这个 jurisdiction 的这个文件生效」。

因此本 ADR 的目标是让平台正式表达：

```
Legal Source → Legal Provision → Statutory Proviso → Applicability
             → AccessRule / JurisdictionRule → Resolver
```

**且必须 additive。** 见 §3。

---

## 2. 硬约束（逐字来自决定人，不得放宽）

| 约束 | 含义 |
|---|---|
| `MUTATE_EXISTING_PUBLISHED_ROWS = NO` | 不给历史 published_rule 批量 UPDATE 一列 `legal_provision_id`。历史 actor 是按当时的模型出版的，改写它等于伪造当时的事实。 |
| 优先 additive model | 新增表 + 新增 link 表，而不是给旧表加列后回填。 |
| provision 精确定位条/款/项 | `article` / `paragraph` / `item` 分级，附原文 quoted span。 |
| proviso 明确指向它所例外的 provision | 外键 + link 表，不是「同行推断」。 |
| jurisdiction 匹配 | 但书只对声明的辖区生效。 |
| temporal validity | instrument 版本 + provision 有效期 + proviso 有效期，三者分层。 |
| Source/Evidence lineage | provision → instrument → source(s) → evidence bundle 可追溯。 |
| 不依赖 place-name 猜法条 | 禁止「place.canonical_name 含『上海』→ 套用上海条例」这类推断。 |
| 不允许「上海 + dog」自动套用任意但书 | 必须同时满足辖区、层、范围、持有者、生效期五个条件（见 §6），缺一不生效。 |
| 历史 backfill 必须 append-only 或版本化 migration | 不得重写原 Human Review、原 Evidence、原 published timestamp、原 Audit event。 |
| Public Beta 前若非 blocker | 完成 ADR + schema + 新数据路径即可；历史全面 backfill 可放 Beta 后。 |

---

## 3. additive model（schema 草案 · 尚未渲染为 alembic revision）

> 状态：**草案**。本轮刻意**不**生成 migration、`不`执行 DDL。它是给 engineering track 的施工图。
> 落到 `@PublicBeta` 之前的验收见 §7。

### 3.1 `legal_instrument` — 法律文件本体

```
legal_instrument
  id                  uuid pk
  jurisdiction_level  text not null          -- municipal / provincial / national
  jurisdiction_id     text not null          -- 310000，不是 place name
  instrument_type     text not null          -- statute_or_regulation / normative_document
  title               text not null          -- 上海市养犬管理条例
  title_normalized    text not null          -- 去书名号/空格后的归一化标题，用于同一性判定
  version_label       text                   -- 2011 年施行 / 2016 年修正 … 可空 = 未考据版本
  promulgated_on      date
  effective_from      timestamptz            -- instrument 版本生效
  effective_to        timestamptz            -- null = 现行
  instrument_identity_key text generated     -- hash(jurisdiction_id|title_normalized|version_label)
  source_lineage      jsonb not null         -- [{source_id, capture..}] ← **同一性由来源集合决定**
  created_at / updated_at

unique (instrument_identity_key)
```

**同一性规则继承 ADR-030 已确立的原则**：按**法律文件同一性**（source 集合）绑定，不按 `rule_id` 绑定。
`JPROV-001.instrument_source_ids = ['f20bdb2c…','a11aff10…']` 正是这一规则的实例——一部条例有两个 source 行，不是两部条例。

### 3.2 `legal_provision` — 条 / 款 / 项

```
legal_provision
  id                  uuid pk
  instrument_id       uuid fk -> legal_instrument.id not null
  article             text not null          -- 第二十三条
  paragraph           text                   -- 第一款
  item                text                   -- 第（二）项
  provision_path      text generated         -- 23 / 23.1 / 23.1.2  精确定位，可比较可排序
  text_span_start     int                    -- 在 instrument 原文 character 序列中的起点
  text_span_end       int
  quoted_text         text not null          -- 逐字原文，不 paraphrase
  subject_scope_json  jsonb                  -- 该 provision 本身的适用对象（不是 place）
  effective_from / effective_to  timestamptz
  status              text not null          -- current / superseded / repealed
  superseded_by_id    uuid fk -> legal_provision.id   -- 版本化，而不是覆盖
  created_at / updated_at

unique (instrument_id, provision_path, version_or_null)
check (article is not null)
```

`provision_path` 是机器可比较的定位符。「第二十三条第一款第（二）项」不再是一个谜语。

### 3.3 `statutory_proviso` — 法定但书

```
statutory_proviso
  id                  uuid pk
  instrument_id       uuid fk -> legal_instrument.id not null
  quoted_text         text not null          -- 盲人携带导盲犬的，不受本条规定的限制。
  applies_to_layer    text not null          -- LEGAL / OPERATOR_POLICY（沿用 ADR-030）
  animal_scope / subject_scope_normalized / normalization_type / normative_effect
  holder_scope        text                   -- person_with_disability（沿用 ADR-031）
  effective_from / effective_to
  status              text not null
  created_at / updated_at
```

### 3.4 `statutory_proviso_legal_provision_link` — 但书 → 它所例外的 provision

```
statutory_proviso_legal_provision_link
  id                  uuid pk
  proviso_id          uuid fk -> statutory_proviso.id not null
  provision_id        uuid fk -> legal_provision.id   not null
  relation            text not null default 'excepts'  -- excepts / qualifies / suspends
  source_lineage      jsonb not null
  created_at

unique (proviso_id, provision_id, relation)
```

**这张表是本 ADR 的核心。** 「这个但书是第几条第一款的例外」从一个隐含事实变成一条可查询、可校验、可审计的关系。一个但书可以 link 到多个 provision；一个 provision 可以有多个但书。

### 3.5 `rule_legal_provision_link` — 规则 → provision（append-only）

```
rule_legal_provision_link
  id                  uuid pk
  rule_kind           text not null          -- access_rule / jurisdiction_rule
  rule_id             uuid not null
  provision_id        uuid fk -> legal_provision.id not null
  linkage_origin      text not null          -- native_publish / deterministic_backfill_v1
  linkage_decided_by  text                   -- 人类署名；backfill 必须写明谁批的计划
  linkage_at          timestamptz not null
  evidence_refs       jsonb                  -- 支持这次 linkage 的 evidence bundle / source ids
  superseded_at       timestamptz            -- **作废用时间戳，不用 delete / update**
  created_at

unique (rule_kind, rule_id, provision_id) where superseded_at is null
```

`linkage_origin` 单列是关键：它让「原生建立」和「事后回填」永远可区分，审计时不会被混为一谈。

### 3.6 `provision_evidence_link` — Source/Evidence lineage

```
provision_evidence_link
  id                  uuid pk
  provision_id        uuid fk -> legal_provision.id not null
  source_id           uuid fk -> source.id          not null
  evidence_bundle_id  uuid fk -> evidence_bundle.id
  quoted_span_hash    text                          -- 原文片段 hash；防止 claim 与原文漂移
  created_at
```

---

## 4. 现有的 `jurisdiction_exception` 怎么办

**不动。** 它继续作为 runtime 生效对象存在，`JPROV-001` 继续工作。

新增的 `statutory_proviso` / `legal_provision` 与它是**并存关系**，不是替换关系：
- `jurisdiction_exception` = runtime resolution 用的扁平表达；
- `legal_provision` + `statutory_proviso_legal_provision_link` = 结构与血缘；
- 两者之间的对齐走 §5 的确定性回填计划，`jurisdiction_exception` 行本身**只增不行改**（如需修正：新增一行 + `supersedes`，而不是 UPDATE 旧行）。

---

## 5. 历史 deterministic backfill plan（合同，尚未执行）

回填计划必须**确定性**：给定同一份输入，任何人重跑得到同一份 link 集合。这才能被审阅。

```
backfill_contract_v1:
  input:
    - jurisdiction_exception rows where status = 'current'
    - their instrument_source_ids
    - source rows referenced by those ids
  mapping:
    legal_instrument: identity from (jurisdiction_id, title_normalized, instrument_source_ids)
    legal_provision:  from clause_ref parsed into (article, paragraph, item)
    statutory_proviso: from proviso_text_ref + ancestor scope fields
    link:             proviso excepts the parsed provision within the same instrument
  forbidden:
    - inference from place.canonical_name
    - inference from place address / city
    - matching a provision whose effective_to < rule.recorded_at  (temporal must hold)
    - any UPDATE to rule_candidate / access_rule / rule_exception / audit_log / evidence_bundle
  output:
    - new rows in link tables only, with linkage_origin = 'deterministic_backfill_v1'
  versioning:
    - the whole mapping is versioned; a re-run writes a NEW generation, marks the
      old generation superseded_at, never deletes it
```

**Human review / Evidence / published timestamp / Audit event：一个字节都不改写。** 这是硬性前置条件，不是最佳实践。

---

## 6. 五个必须同时满足才生效的条件（禁止「上海 + dog」式套用）

Resolver / applicability 判定要套用一个 proviso，必须同时满足全部五项，缺一即 `proviso_not_applicable`：

1. **jurisdiction**：`rule.jurisdiction_code`（或 place 的辖区归属解析结果，**来自辖区字段而非名称匹配**）等于 `instrument.jurisdiction_id`；
2. **layer**：`proviso.applies_to_layer == rule.rule_layer`（ADR-030 的边界：救不了 OPERATOR_POLICY 基底的未解决法律适用性问题）；
3. **scope**：proviso 的 animal/subject scope 覆盖查询主体（沿用 `rule_governs`，不另写一套）；
4. **holder**：`holder_scope` 与查询输入的持有人维度匹配（ADR-031 已确立的存在语义已被废止）；
5. **temporal**：查询时点落在 instrument 版本、provision、proviso 三者的有效期内。

**显式禁止的推断**（写进 repository 的原因是它们每一次都看起来很合理）：

- ❌ `place.canonical_name LIKE '%上海%'` → 套用上海市条例
- ❌ 「在某辖区 + 涉及犬」→ 套用该辖区任意导盲犬但书
- ❌ 缺 `holder_scope` 时因为「反正导盲犬」而放行（ADR-031 已废止此语义，UI 表现为 `missing_inputs`）
- ❌ 用一个 proviso 去覆盖它并未 link 的 provision（即便两者在同一份文件里）

---

## 7. 门槛与后续（明确不作为本轮）

| 项目 | 本轮 | 下一步 engineering track |
|---|---|---|
| ADR | ✅ 本文 | — |
| schema 草案 | ✅ §3 | 渲染为 alembic revision（先 `--sql` 离线渲染 + 生产指纹前后比对） |
| 新数据路径 | ❌ | 新发布规则在 publish 时原生写 `rule_legal_provision_link(linkage_origin='native_publish')` |
| 历史 backfill | ❌ | §5 合同的首个版本实现 + count-only dry-run + 人类逐批确认 |
| 运行时消费 | ❌ | resolver 按 §6 五条件判定；在此之前 resolver 行为**不变** |
| Public Beta blocker | **否** | 全面历史 backfill 可放 Beta 后 |

**边界声明**：本 track 不触碰任何既有 published rule、evidence bundle、human review、audit event。
它与 Wave-01 处置、Century Park evidence acceptance、Scope Remodel R2 三条线**互不阻塞**。

---

## 8. 已知开放项

1. `title_normalized` 的归一化规则（书名号、繁简、「实施细则」类衍生文件名）需一份可枚举规则表，否则 `instrument_identity_key` 会分裂。
2. 「修正式」版本（2016 年修正）与「施行式」版本的 `version_label` 取值没有权威来源，目前允许为空并标记为未考据。
3. `text_span_start/end` 依赖 instrument 原文的权威抓取；当前两个 source 行尚未做逐字比对。
4. 历史上 5 条 LEGAL 基底的具体引用（哪些是第二十三条、哪些不是）仍需人工逐条确认——这正是 §5 要求 `linkage_decided_by` 必须署名的原因。
