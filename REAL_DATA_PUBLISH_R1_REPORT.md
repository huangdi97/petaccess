# REAL_DATA_PUBLISH_R1_REPORT.md

> P0 — PILOT-REVIEW-PUBLISH-01 执行报告
> 执行时间：2026-09-13（GMT+8）· 基准 commit `08ee60c`（本轮改动未提交）
>
> **结论：P0 的「审核工作稿 + 发布工具链 + 发布路径缺陷修复」已完成且可验证；P0 的「写库发布」被两项外部条件阻塞，未发生任何写入。**

---

## 1. 本轮实际完成（可验证）

| # | 产物 | 证据 |
|---|---|---|
| 1 | 33 条候选逐条审核工作稿 | `REAL_DATA_REVIEW_DECISIONS_R1.md`（含每条 evidence/place_match/license 摘要与建议决策） |
| 2 | 机器可读决策登记表（33 行） | `docs/reality_audit/review_decisions_r1.json`，由 `scripts/gen_review_decisions_r1.py` 从证据链+入库清单**生成**（非手抄） |
| 3 | 发布执行脚本（含人类签署门禁、弱证据拦截、批量上限、发布后校验） | `scripts/publish_reviewed_r1.py` |
| 4 | 分层回填脚本 | `scripts/backfill_candidate_rule_layer.py` |
| 5 | 新增 admin 端点 `POST /admin/candidates/{id}/rule-layer`（带审计、已发布候选冻结） | `services/api/app/api/v1/v05.py`；冒烟确认 37 条 admin 路由、端点存在 |
| 6 | **发布路径 P0 缺陷修复（BLK-LAYER-01）** | 见 §3 |
| 7 | 5 项回归测试 | `tests/unit/test_publish_layer_integrity.py`（5 passed） |

### 1.1 建议决策分布（与工作表一致，生成器实跑输出）

```json
{ "total": 33, "proposed": {
    "RECOMMEND_APPROVE": 21,
    "RECOMMEND_APPROVE_WITH_NOTE": 8,
    "RECOMMEND_HOLD": 3,
    "RECOMMEND_REJECT": 1 } }
```

### 1.2 第一批发布批次 R1-A（17 条，待人类签署）

7 条法规「犬只禁入」（`qt/lib/gh/fp/sb/mn/xm` 室内）+ 8 条法规「服务犬豁免」（同源但书）+ 2 条政府公园试点（`gc-h6-pilot`、`dj-pilot`）。理由：来源层级最高、`redistribution_allowed=true`、逐字引文可逐条比对、无 unresolved conflict。

---

## 2. 未完成项与精确阻塞（这是本轮的核心结论）

### BLOCKER-1 · ENV-01 — 数据层不可用（阻塞所有写库动作）

| 项 | 事实 |
|---|---|
| 现象 | `docker ps` → `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine` |
| 根因 | `com.docker.service` 状态 `Stopped`，`Start-Service` 返回「无法打开计算机"."上的服务」（需管理员提权）；WSL 被沙箱安全策略列为程序黑名单；本机无 PostgreSQL/Podman |
| 直接后果 | 无 PostGIS ⇒ 迁移无法建立 ⇒ `publish()` 不可执行；DB 依赖测试全部无法运行 |
| 已实测 | `psycopg` 连接 `localhost:5432` → `ConnectionTimeout`（6.6s）；全量 `pytest` 超时终止 |
| 影响的 Gate | P01（写库部分）、P02、P04–P05、P10–P12 |

**用户最小恢复动作（二选一）**
1. 以**管理员**身份启动 Docker Desktop（或 `sc start com.docker.service`），随后执行：
   ```bash
   cd "E:/AI/宠物管理" && docker compose up -d
   cd services/api && ../../.venv/Scripts/python.exe -m alembic upgrade head
   ```
2. 或提供一个可达的 PostgreSQL + PostGIS 实例，并写入 `.env` 的 `DATABASE_URL`。

**恢复后一条命令即可完成 P0 写库发布**（前提是 BLOCKER-2 已解除）：
```bash
.venv/Scripts/python.exe scripts/publish_reviewed_r1.py --execute --reviewer "<具名评审员>"
```

### BLOCKER-2 · GOV-01 — 缺少具名人类评审员（阻塞 APPROVED 决策）

Master Goal §0.9 / ADR-005 / `REVIEW_WORKLIST_R1.md` 纪律明确规定：**AI 只做 extraction/candidate，不做最终规则裁决**；`REVIEW_WORKLIST_R1.md` 第 8 行要求「任何候选的 APPROVE 前提：证据核验通过 + Pre-Publish Validation 全绿」，且由**人工 Review Gate** 执行。

因此本轮**不代签 33 条 APPROVED**（这正是项目禁止的「无审查批量 APPROVE」）。工作稿已把决策压缩到"审阅并签署"这一步。

**门禁已实测生效**（`--dry-run` 实跑输出）：
```
发布前置条件未满足（33 项）——以下为需要人类评审员处理的事项：
  - 70cc7579-... dj-pilot: final_decision 未填
  - f5a8d87f-... dl-legal-dog: final_decision 未填
  ... （33 行）
```

**用户最小恢复动作**：由具名评审员在 `docs/reality_audit/review_decisions_r1.json` 中为每行填写
`final_decision`（APPROVED/REJECTED/HOLD）、`reviewer`、`reviewed_at`；并回答工作表 §5 的两个裁定项。

---

## 3. 本轮修复的发布路径 P0 缺陷

### BLK-LAYER-01（已修复）— 分层在入库/发布时被静默拍平

**缺陷**：`RuleCandidate` 模型无 `rule_layer` 字段 → `scripts/real_pilot_ingest.py` 入库时丢弃证据登记表中的 `rule_layer` → `candidate_service.publish()` 硬编码 `AccessRule.rule_layer = "OPERATOR_POLICY"`。

**为何是 P0**：`v05_resolver._load_layered_rules()` 依据 `rule_layer` 把规则分入 `legal / guidance / events / operator` 四个池（`v05.py:829-836`），且：
- `legal` 池规则在 `v05_resolver.py:320/339` 被**排除**于 operator 特异性遮蔽之外；
- `is_temporary`（`v05_resolver.py:75`）决定临时政策是否遮蔽运营规则。

故拍平会使 **16 条《养犬管理条例》LEGAL 规则**与 **2 条公园试点 TEMPORARY_POLICY 规则**落入 operator 池，改变已发布答案。

**修复内容（全部 additive）**
| 层 | 改动 |
|---|---|
| 模型 | `RuleCandidate.rule_layer`（NOT NULL，server_default `OPERATOR_POLICY`） |
| 迁移 | `d1a4f7c93b28_rule_candidate_rule_layer.py`（`down_revision=b5e8d2c4a710`），含 CHECK 约束 |
| 服务 | `create_from_extraction(..., rule_layer=)`；`publish()` 透传 `candidate.rule_layer or "OPERATOR_POLICY"` |
| 门禁 | `publish_gate` 新增 `LAYER_VALUES` 校验（未知层 → `schema_unsupported`） |
| API | `CandidateIn.rule_layer`、`_candidate_dict`、新端点 `/candidates/{id}/rule-layer` |
| 入库 | `real_pilot_ingest.py` 携带 `rule_layer` |
| 测试 | `tests/unit/test_publish_layer_integrity.py`（5 项） |

**兼容性**：既有行的 server_default 与原硬编码值相同 ⇒ 无已发布规则改变含义。

### BLK-LAYER-02（未修复，需人类裁定）— 法定禁止可被运营方规则覆盖

**缺陷**：`AccessRule` **没有 `mandatory_level` 列**。resolver 的法定强制分支 `legal_mandatory = [r for r in scoped_legal if r.mandatory_level == "mandatory"]`（`v05_resolver.py:274`）因此**对 DB 来源规则永不可达**；且 `v05_resolver.py:409`
```python
governing = [r for r in applicable if r.rule_layer != RuleLayer.LEGAL.value] or applicable
```
会把非强制 LEGAL 规则排除在 governing 之外。

**后果（已用测试钉住）**：`tests/unit/test_publish_layer_integrity.py::test_legal_prohibition_without_mandatory_level_does_not_govern` 显示——运营方 `allowed` 规则会**胜过**《上海市养犬管理条例》第23条的法定禁止（结果 `allowed`）；补上 `mandatory_level="mandatory"` 后结果为 `prohibited`。

**为何本轮不修**：`AccessRule` 加列 + 默认值会改变已冻结 resolver 语义，属架构变更，须走 ADR + 人类裁定，且**需要数据层才能验证回归**（现有 13 项真实世界回归夹具同样不带 `mandatory_level`，故无法暴露此缺口）。

**建议处置（供评审员选择）**：
- (A) 先补 `AccessRule.mandatory_level`（LEGAL→`mandatory`，REGULATORY_GUIDANCE→`advisory`）+ ADR，再发布；
- (B) 按现状发布，但把该缺口登记为已知限制并在产品文案中不宣称"法定禁止已完整建模"。

---

## 4. 发布验证清单（待数据层恢复后逐项执行）

| 检查 | 状态 |
|---|---|
| AccessRule created | ⏸ 待 ENV-01 |
| candidate ↔ rule linkage | ⏸（脚本已含校验） |
| source / evidence 链 | ⏸ |
| version / supersession | ⏸ |
| audit log | ⏸ |
| resolver（`/effective-rules`） | ⏸ |
| client display | ⏸ |
| rollback / withdraw | ⏸ |
| watch | ⏸ |

---

## 5. P0 Gate 判定

```text
PILOT_REVIEW_PUBLISH_GATE = BLOCKED_EXTERNAL
```

| 子项 | 判定 | 依据 |
|---|---|---|
| 33 条审核工作稿 | **PASS** | 逐条 evidence/place_match/license + 建议决策 |
| 发布工具链 | **PASS** | 门禁/弱证据拦截/批量上限/发布后校验齐备并实跑 |
| 发布路径缺陷修复 | **PASS** | BLK-LAYER-01 修复 + 5 项回归测试 + mypy/ruff 全绿 |
| 33 条最终审核决策 | **BLOCKED_EXTERNAL（GOV-01）** | 需具名人类评审员签署 |
| 第一批真实 Publish | **BLOCKED_EXTERNAL（ENV-01）** | 无 PostGIS，`publish()` 不可执行 |

**因此 P1（30–50 扩量）按 Master Goal「不 PASS 不进入 P1」的要求暂不启动。**
