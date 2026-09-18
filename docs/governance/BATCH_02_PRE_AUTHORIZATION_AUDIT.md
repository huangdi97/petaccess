# BATCH_02 预授权审计（BATCH_02_PRE_AUTHORIZATION_AUDIT）

- 时间：2026-09-18（UTC 13:15，容器时钟）
- 审计对象：`EXP-R1-W01-REVIEW-R1-BATCH-02`（6 条）
- 生产库：`petaccess`，指纹 `a4f55b14…`（审计前后未变）
- 运行时证据库：`petaccess_publish_rehearsal_b2`（生产克隆 + BATCH_02 已发布）
- **生产库未写入。本报告是发布前的证据，不是发布回执。**

---

## H. 结论指标

| 指标 | 值 |
|---|---|
| `ADR030_RUNTIME_GATE` | **PASS** |
| `JPROV001_ACTIVE` | **YES** |
| `BATCH_02_SELECTED` | **6** |
| `BATCH_02_FINAL_EXECUTABLE` | **6** |
| `JURISDICTION_EXCEPTION_MATCHED` | **11 / 11**（生产库 5/5；克隆库 11/11，其中 6 条为 BATCH_02 新基底） |
| `PLACE_LEVEL_DUPLICATE_EXCEPTION_REQUIRED` | **NO** |
| `CROSS_LAYER` | **0** |
| `INERT_EXCEPTION` | **0** |
| `GUIDE_DOG_WRONG_PROHIBITION` | **0** |
| `SERVICE_DOG_OVERGENERALIZATION` | **0** |
| `POLICE_DOG_OVERGENERALIZATION` | **0** |
| `MILITARY_DOG_OVERGENERALIZATION` | **0** |
| `DRY_RUN_ZERO_DB_MUTATION` | **PASS** |
| `REAL_PUBLISH_EXECUTED` | **NO** |

`HUMAN_ACTION_REQUIRED = BATCH_02_REAL_PUBLISH_AUTHORIZATION`

---

## A. ADR-030 真实运行时验证

判定用的是**真实 resolver**（`app.rulespec.v05_resolver.resolve`），读的是实时行，不是文档。

关键设计：三种模式跑同一批行——

| 模式 | 例外集 | 代表什么 |
|---|---|---|
| `full` | 场所级 `rule_exception` + 辖区但书 | 生产现状 |
| `no_place_exception` | **仅辖区但书** | BATCH_02 发布后的真实状态（决定性模式） |
| `no_proviso` | 仅场所级例外 | 激活前的反事实 |

### 决定性模式（`no_place_exception`，无场所级重复例外）

生产库 5 个已发布 LEGAL 基底 + 克隆库 6 个 BATCH_02 新基底，共 11 个：

| 查询 | 结果 | 要求 |
|---|---|---|
| 普通犬 | `prohibited`（11/11） | prohibited ✓ |
| 导盲犬 | `allowed`（11/11），`applied_exceptions = ['JPROV-001']` | 不得 prohibited ✓ |

```
JURISDICTION_EXCEPTION_MATCHED      = 11
APPLIED_EXCEPTION_SOURCE            = JPROV-001
PLACE_LEVEL_DUPLICATE_EXCEPTION_REQUIRED = NO
GUIDE_DOG_WRONG_PROHIBITION         = 0
```

**结论：不需要场所级重复例外。** 若必须靠它才能工作，`ADR030_RUNTIME_GATE` 会判 FAIL 并停止授权；实际为 PASS。

反事实（`no_proviso`）恰好证明但书是真在起作用：6 条 BATCH_02 基底在去掉但书后导盲犬从 `allowed` 掉回 `prohibited`
（`ADR030_EFFECT_ANSWER_CHANGED = 6`），而已有场所级例外的 5 个场所不变（=0）。

---

## B. 适用性验证（非无条件泛化）

`JPROV-001` 的绑定**只按法律文件同一性**，`instrument_source_ids = [f20bdb2c…, a11aff10…]`。
五个条件逐条实测（11 个基底全部 `all_conditions_hold = True`）：

| # | 条件 | 实测 |
|---|---|---|
| 1 | 基底 `source_id` 属于该法律文件的 source 集合 | True |
| 2 | `rule_layer == applies_to_layer`（LEGAL） | True |
| 3 | `effect ∈ applies_to_effects`（prohibited） | True |
| 4 | 基底作用域**治理**但书主体（`rule_governs({'guide_dog'}, dog, …)`） | True |
| 5 | 时效有效（`proviso.active_at(now)`） | True |

### 反向对照（证明不是「只因在上海」）

对每条基底复制一份、**只改 `source_id` 为非本法条来源**的合成基底，导盲犬查询：

```
11 / 11 → prohibited，proviso_correctly_withheld = True
NEGATIVE_CONTROL_FAILED = 0
```

即：同一场所、同一 zone、同一 LEGAL 禁犬基底，只要不源自《上海市养犬管理条例》，但书**完全不生效**。
绑定与地理位置无关——代码路径中不存在任何按辖区/坐标匹配场所的逻辑。

### 两个必须如实记录的缺口

1. **`holder_scope` 未被 resolver 强制。** `JPROV-001.holder_scope = person_with_disability`
   （但书原文「盲人携带导盲犬的」），但 `resolve()` 没有 handler 入参，
   `holder_scope_allows()` 在 `app/rulespec/` 之外**无任何调用点**——是死代码。
   实测结果：任何携犬人都享受该豁免。这是语义缺口，不是本次引入，但 BATCH_02 发布后影响面从 5 个场所扩到 11 个。
2. **时效条件为真是因为它是空的。** `JPROV-001.effective_from / effective_to` 均为 NULL，
   条件 5 以「无时间边界」通过。法规本身的生效/修订日期未建模。

---

## C. 新旧例外不双重生效

| 检查 | 结果 | 机制 |
|---|---|---|
| 双重 effect | **0** | resolver 中 `matched: dict[base_id → exception]`，一个基底最多挂一条例外 |
| 重复 `applied_exceptions` | **0** | 实测 `applied_exceptions` 长度恒为 1 |
| 冲突结果 | **0** | `full` 与 `no_place_exception` 在普通犬/导盲犬上答案完全一致（`MODE_DISAGREEMENT = 0`） |
| 冲突标记 | 无 | 两条例外 effect 同为 `allowed`，`_attach` 不触发 `REVIEW_REQUIRED` |

### 兼容性与迁移策略

- **当前状态（推荐维持）**：legacy 场所级例外与辖区但书并存，答案确定且一致。
  5 个已发布场所的例外现在**功能冗余**，但删除它会动已发布历史 → **需要新 revision + 新人工审查**，本轮不做。
- **若日后要退役 legacy 例外**：先在演练克隆上逐场所做 A/B（去掉 legacy 后答案必须不变），
  再走新 manifest 发布退役动作；不得直接 DELETE 已发布行。
- **顺序约定**：`exceptions` 列表中 legacy 在前、但书在后，因此 legacy 优先命中；
  因二者 effect 相同，顺序不改变答案（已实测 `MODE_DISAGREEMENT = 0`）。

---

## D. BATCH_02 六条逐条明细

| # | rule_id | Place | Zone | 人类决定 | Layer | Subject | Effect |
|---|---|---|---|---|---|---|---|
| 1 | `w01-052d19ccba` | CHARLIE'S 粉红汉堡（马当路店） | 室内用餐区（dining_area / indoor） | APPROVED | LEGAL | 犬只 → dog | prohibited |
| 2 | `w01-7de2f5d75b` | omitofee 上海首店（浦江郊野公园滨江漫步区） | 室内空间（含专属宠物休憩区）（dining_area / indoor） | APPROVED | LEGAL | 犬只 → dog | prohibited |
| 3 | `w01-df1645fe68` | 上海新天地朗廷酒店 | 客房内部（area / indoor） | APPROVED | LEGAL | 犬只 → dog | prohibited |
| 4 | `w01-8ba2b49b01` | 上海苏河湾万象天地 | 室内商铺及公共区域（area / indoor） | APPROVED | LEGAL | 犬只 → dog | prohibited |
| 5 | `w01-d1aee78159` | 前滩太古里 | 商场室内空间（other / indoor） | APPROVED | LEGAL | 犬只 → dog | prohibited |
| 6 | `w01-e951785d1b` | 港汇恒隆广场 | 商场室内公共区域（area / indoor） | APPROVED | LEGAL | 犬只 → dog | prohibited |

### 逐条其余字段

| # | Source | Evidence | 法条 | 法条类别 | 此前被阻断 | 现在可执行 | 发布类型 | 依赖 |
|---|---|---|---|---|---|---|---|---|
| 1 | 上海市人民政府门户《上海市养犬管理条例》`a11aff10…` | `primary_direct` / direct / available_online；artifact `04aadadf…`，content_hash `51c58e87…`，captured 2026-09-18 | 第二十三条 | 餐饮场所 | `REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE` | JPROV-001 路径 C 接线 | `CREATE_ACCESS_RULE` | 无 |
| 2 | 同上 | 同上 | 第二十三条 | 餐饮场所 | 同上 | 同上 | `CREATE_ACCESS_RULE` | 无 |
| 3 | 同上 | 同上 | 第二十三条 | 宾馆 | 同上 | 同上 | `CREATE_ACCESS_RULE` | 无 |
| 4 | 同上 | 同上 | 第二十三条 | 商场 | 同上 | 同上 | `CREATE_ACCESS_RULE` | 无 |
| 5 | 同上 | 同上 | 第二十三条 | 商场 | 同上 | 同上 | `CREATE_ACCESS_RULE` | 无 |
| 6 | 同上 | 同上 | 第二十三条 | 商场 | 同上 | 同上 | `CREATE_ACCESS_RULE` | 无 |

- 许可：`license_problems = []`，`storage/display = true`，`redistribution = false`。
- 复核人 `huangdi97`，`reviewed_at = 2026-09-18T07:31:10Z`。
- 6 条全部 `subject_scope_normalized = dog`、`normalization_type = exact`、`mandatory_level = mandatory`、`action = enter`。

---

## E. 全闸门重跑

### 语义桥接（`w01_semantic_bridge.py --report --batch-id …BATCH-02 --exclude-published`）

```
jurisdiction_provisos_active = 1
human_approved        = 15
legal_dog_bases       = 8
legal_dog_with_exception = 8
legal_dog_blocked     = 0
PREPUBLISH_POLICY_PASS  = 13
EXECUTION_CONTRACT_PASS = 14
FINAL_EXECUTABLE        = 11  (AccessRule 9 + RuleException 2)
EXCLUDED_APPROVED       = 4
```

6 条 BATCH_02 全部 `scope=PASS gdog=PASS exec=PASS`。

### 发布器 dry-run（`publish_reviewed_r1.py --dry-run`，目标 = 生产库）

```
total = 6   human_decisions = {APPROVED: 6}
prepublish_pass = 6   prepublish_blocked = 0   gate_status_counts = {PASS: 6}
access_rule_create_count = 6   rule_exception_create_count = 0
noop_count = 0   blocked_count = 0
cross_layer = 0   inert_selected_exceptions = 0
bases_missing_approved_exception = 0   unreachable_approved_carve_outs = []
dependency_closed = True
integrity: SELF_SUPERSEDE 0 / DUPLICATE_PUBLICATION_PLAN 0 / CROSS_LAYER_EXCEPTION 0 / SUPERSESSION_CYCLE 0
DRY_RUN_ZERO_DB_MUTATION = True
```

`BATCH_02_FINAL_EXECUTABLE = 6/6`。未发生任何自动缩小。

---

## F. Resolver 矩阵（BATCH_02 六个场所）

模式 = `no_place_exception`（只有辖区但书，即发布后的真实状态）：

| 场所 · zone | ordinary_dog | guide_dog | service_dog(未声明) | hearing_dog | assistance_dog | other_service_dog | police_dog | military_working_dog |
|---|---|---|---|---|---|---|---|---|
| CHARLIE'S 粉红汉堡 · 室内用餐区 | prohibited | allowed | allowed | prohibited | prohibited | prohibited | prohibited | prohibited |
| omitofee 上海首店 · 室内空间 | prohibited | allowed | allowed | prohibited | prohibited | prohibited | prohibited | prohibited |
| 上海新天地朗廷酒店 · 客房内部 | prohibited | allowed | allowed | prohibited | prohibited | prohibited | prohibited | prohibited |
| 上海苏河湾万象天地 · 室内商铺及公共区域 | prohibited | allowed | allowed | prohibited | prohibited | prohibited | prohibited | prohibited |
| 前滩太古里 · 商场室内空间 | prohibited | allowed | allowed | prohibited | prohibited | prohibited | prohibited | prohibited |
| 港汇恒隆广场 · 商场室内公共区域 | prohibited | allowed | allowed | prohibited | prohibited | prohibited | prohibited | prohibited |

**逐角色结论：**

- `police_dog` / `military_working_dog` → `prohibited`（0 泛化）✓
- `hearing_dog` / `assistance_dog` / `other_service_dog` → `prohibited`（0 泛化）✓
- `guide_dog` → `allowed`，且仅由 `JPROV-001` 提供 ✓

### 一项需要你知道的行为（非 ADR-030 引入）

**未声明角色的 `service_dog` 查询 → `allowed`。** 查询侧会把「服务犬」展开为 4 个协助角色
（guide/hearing/assistance/other_service），其中包含 `guide_dog`，于是命中但书。

- 这不是 ADR-030 带来的：在 `no_proviso` 模式下（只有 legacy 场所级例外）**同样是 `allowed`**，
  5 个已发布场所行为一致。
- 后果：一位未声明种类的助听犬使用者会拿到 `allowed`，而法律上只有导盲犬豁免。
- 属于**查询模型**的既有属性，建议单独立项，不阻断本批次。

---

## G. 生产库 dry-run 零变更证明

```
PROD_FINGERPRINT_G1 (dry-run 前) = a4f55b14283d84bf154aa8a7af82f7b6f11673310ae38ca99c5a8cddca39b9f8
PROD_FINGERPRINT_G3 (dry-run 后) = a4f55b14283d84bf154aa8a7af82f7b6f11673310ae38ca99c5a8cddca39b9f8
PRODUCTION_DB_ROW_DIFF   = 0
SEMANTIC_DIFF            = 0
FINGERPRINT_COMPARE      = IDENTICAL
DRY_RUN_ZERO_DB_MUTATION = True
```

Human register 未改（`review_decisions_expansion_r1_wave01_publishable.json` 未被写入，
dry-run 的 `--snapshot-out` 文件**未生成**）。已发布规则未改（`access_rule` 8、`rule_exception` 5 前后一致）。

---

## 发布前需你确认的三件事

1. **`holder_scope` 缺口**：但书限定「盲人携带导盲犬」，resolver 未强制携犬人身份。
   发布后影响面 5 → 11 个场所。
2. **未声明 service_dog 查询 → allowed**：既有查询模型行为，见 F 节。
3. **B5 扩大**：BATCH_02 发布后，「有已发布规则但无坐标」的场所从 2 个变成 6 个
   （CHARLIE'S / omitofee / 朗廷 / 苏河湾万象天地 无 `location`），`/places/nearby` 会继续静默漏掉。

三者均不阻断发布，但发布即扩大，需要你知道。

---

## 产物

- `artifacts/batch02_audit/runtime_matrix_production.json`（生产库 5 个基底）
- `artifacts/batch02_audit/runtime_matrix_b2clone.json`（克隆库 11 个基底，含 6 条新基底）
- `artifacts/batch02_audit/bridge_report.txt`（语义桥接）
- `artifacts/batch02_audit/dryrun_stdout.txt`（发布器 dry-run JSON）
- `artifacts/batch02_audit/PROD_FINGERPRINT_G1.json` / `_G3.json`（零变更证据）
- 脚本：`scripts/batch02_pre_authorization_audit.py`（只读；ruff check/format PASS）
