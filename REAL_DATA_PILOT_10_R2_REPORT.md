# REAL_DATA_PILOT_10_R2_REPORT.md

> REALITY-AUDIT-10-R2 / PILOT-REVIEW-AND-SCHEMA-FIX-01 收尾报告（2026-09-13）。
> 前置：REAL-DATA-PILOT-10-R1（commit e299fab）。本报告覆盖目标要求的十项必报指标。
> 铁律不变：**0 条发布；33 条 RuleCandidate 全部 REVIEW_PENDING（不强行 APPROVE）；3 条 ObservationCandidate 保持 lead-only。**

## 0. TL;DR

- **SG-REAL-01 已修复**：通用 `RuleException` 机制（migration/模型/解析器/评估器/API/Admin/PetAccessJSON/Audit 引擎）落地，**服务犬解析从 3/7 正确提升到 7/7 正确**（R1 中烘焙工坊/港汇/西岸的导盲犬被错误禁止）。
- **证据补强 7 条 → 5 修复 1 矛盾 1 未证实**：direct-or-strong 证据占比 **78.8% → 93.9%**（≥90% 门槛）。
- **REALITY-AUDIT-10-R2 实跑：10/10 可表达，0 resolver 错误**；去敏回归夹具 27 查询入 CI。
- 全量测试 **238/238**（原 225 + 新 13 回归 + 例外套件），ruff/mypy 全绿。
- **R2 Gate：PASS（有条件）** —— 30–50 扩量解锁，但 Manner 归因候选须人工 REJECT、2 条残留 snippet 候选须先核验（见 §11）。

## 1. Evidence Completeness（必报①）

按每条候选当前引用 bundle 的 artifact `evidence_strength`（EvidenceStrength 枚举，DB 实测）：

| 强度 | 候选数 | 占比 |
|---|---|---|
| primary_direct | 28 | 84.8% |
| secondary_reputable | 3 | 9.1% |
| search_snippet | 2 | 6.1% |
| **direct-or-strong 合计** | **31/33** | **93.9%** ✅（R1 为 78.8%） |

R1 的 7 条 snippet 候选处置（详见 `docs/reality_audit/EVIDENCE_REPAIR_LOG_R1.md`，14 次尝试逐条留痕）：
5 条修复（新华网直抓 / 费尔蒙官网直抓 / 潮新闻官方回应直抓 ×2）、1 条**归因错误实锤**（Manner）、1 条未被原文证实（港汇户外）。

## 2. Approved / Rejected / Pending（必报②）

| 状态 | 数量 | 说明 |
|---|---|---|
| REVIEW_PENDING | **33** | 全部维持；Review 工作清单 `REVIEW_WORKLIST_R1.md`（A 组 26 直接审 + B 组 7 修复后审） |
| APPROVED / REJECTED | **0 / 0** | **不允许为达标强行审批**（目标红线）；Manner 候选已附矛盾审计记录，建议人工 REJECT |
| ObservationCandidate | 3 | lead-only，永不进入规则发布（API 层断言测试覆盖） |

## 3. Published Count（必报③）

**0**。Pre-Publish Validation（S8）六检全过才可发布；本轮无人审决策，无发布。

## 4. RuleException Result（必报④）

- 机制：`rule_exception` 表（migration a7f3c2d91e04，additive）：base rule + (animal_scope, effect, **source_id NOT NULL**, status, 有效窗口)；生效条件 = status=current ∧ 窗口内 ∧ 有 source ∧ scope 匹配查询；生效时替代 base 规则并输出解释步骤；过期/withdrawn/superseded 自动回落；多条匹配冲突 → REVIEW_REQUIRED 不猜测。**无任何写死的 service_dog 分支**（ADR-020）。
- 覆盖面：migration ✅ · 模型/枚举 ✅ · v05_resolver + v1 evaluator ✅ · API（POST/GET/transition + 审计）✅ · PetAccessJSON `exceptions` 键（严格校验）✅ · Reality Audit 引擎 ✅ · Admin 展示（列表端点 + effective-rules `applied_exceptions` + explanation_steps）✅。
- DB 现状：0 行（尚无已发布规则可挂例外；机制由 29 个自动化测试覆盖：13 单测+property、3 集成、13 回归）。

## 5. Service Dog Result（必报⑤）

R2 audit 探针（`docs/reality_audit/real_pilot_02/REALITY_AUDIT_REPORT.md`）：

| 场所 | R1（修复前） | R2（修复后） |
|---|---|---|
| 前滩太古里 室内 | allowed（靠 operator 规则） | allowed（LEGAL exception + operator 同向）✅ |
| 上海迪士尼 | conditional | conditional（exception + operator 条款）✅ |
| **港汇恒隆 室内** | **prohibited ❌** | **allowed**（LEGAL exception + 运营方政策自带"导盲犬等工作犬例外"）✅ |
| 上海图书馆 | allowed | allowed ✅ |
| **和平饭店** | conditional（OTA 猜测） | **allowed**（官网原文"导盲犬可随时进入…无任何限制"）✅ |
| **星巴克烘焙工坊** | **prohibited ❌** | **allowed**（LEGAL exception）✅ |
| **西岸梦中心 室内** | **prohibited ❌** | **allowed**（LEGAL exception）✅ |

**正确率 3/7 → 7/7**。普通犬仍被正确禁止（单测+property+回归夹具三层守护：`test_exception_never_widens_to_ordinary_pets` 等）。

## 6. Place Attribution（必报⑥）

- 33 条候选的 place_match_evidence 全部在案（bundle 级）。
- R1 报告 0 错误；**R2 修复发现 1 条真实归因错误**：Manner 凯德虹口候选的 CBNData 来源经原文核验**未报道该店**（"凯德虹口"实指宠物用品店"狗道"）→ audit_log 记 contradiction，建议人工 REJECT。
- 归因错误率：**1/33 = 3.0% < 5% 阈值** ✅（且已被修复流程捕获，未进入发布）。

## 7. Schema Gaps（必报⑦）

| Gap | R1 状态 | R2 状态 |
|---|---|---|
| SG-REAL-01 服务犬法定豁免不可表达 | ❌ | ✅ **已修复**（RuleException + ADR-020） |
| `pet_stroller_rental` 共处属性无结构归属 | gap 候选 | 保持 gap（真实样本仍在，等评审） |
| `use_pet_elevator` 仅 note_only | gap | ✅ **已按目标建模**：`designated_entrance/elevator/route` 升为强制义务条件（evaluator `_OBLIGATION_CONDITIONS`），语义连接 Entrance（`entrance_type=PET_DESIGNATED`）与 AccessPath 步骤，非布尔 |
| `pet_swimming_pool` 无结构归属 | gap | **继续记录 gap**（无新真实样本证明需要扩展 Amenity taxonomy，按目标要求不扩） |

## 8. Resolver Errors（必报⑧）

- R2 audit：10/10 样本可表达；27 查询全部产出明确 effect 或诚实 UNKNOWN；**0 解析错误**。
- 修复前发现并已修的 API 层缺陷：monitor 候选未引用 bundle（evidence-first 断链）✅；v05 `_load_layered_rules` 条件序列化错误（ORM 对象当 dict）✅；同源政策变更自动 supersession（含 supersedes_not_self 自反保护）✅。
- 回归防线：`tests/fixtures/real_world_regression.json`（27 查询 + 预期值取自 R2 实跑）+ `test_real_world_regression.py` 13 测试——resolver 未来任何改动先撞真实世界预期。

## 9. Boundary Results（必报⑨）

- 与 R1 一致：本批以 POINT + Zone 语义表达，未录 BoundaryProfile（现场测绘级数据待扩量阶段）。
- boundary-match 端点在 PART A 已有 perf 基线；R2 变更后 effective-rules 内部经 resolve(exceptions=...) 正常产出边界匹配输入。
- pet_stroller_rental 边界属性缺口保持记录（§7）。

## 10. Source / License Status（必报⑩）

- 来源总数（唯一）：15（R1 11 + 修复新增 4）；全部有 URL/发布日期/采集方式/引文/hash（解放日报原文已下线，标注 dead，以新华网版本为准）。
- 强度分布（19→23 artifacts）：primary_direct 15、secondary_reputable 3、search_snippet 4、social_lead 1（迁移回填 + 修复脚本一致映射）。
- 许可：新闻/官网政策页 redistribution=false（内部核验用）；社媒 lead display/storage=false（lead-only，Pre-Publish Validation 硬拦截 SEARCH_SNIPPET/SOCIAL_LEAD 证据的发布）；政府公告/法规可再分发。
- 无绕过登录/验证码/访问控制（14 次尝试中 403/验证码即停，改走合法通道，全记录在修复日志）。

## 11. R2 Gate 判定

| 门槛 | 实测 | 判定 |
|---|---|---|
| Evidence Completeness ≥ 90%（B15 解锁条件） | **93.9%** | ✅ |
| Place attribution error ≤ 5% | 3.0%（1/33，已捕获） | ✅ |
| AI major extraction error ≤ 5% | 0 已证实（引文逐字可比对；33 条待人审终裁） | ✅（留人审） |
| unauthorized source usage | 0 | ✅ |
| SG-REAL-01 修复 | 完成 + 7/7 服务犬正确 | ✅ |
| 全量测试 | 238/238（ruff/mypy 绿） | ✅ |
| 强行审批 | 0（33 条全 REVIEW_PENDING） | ✅ |

### **R2 Gate = PASS（有条件）→ 允许进入 30–50 Place 扩量**

扩量前置条件（不阻塞判定，但进入扩量批次前必须处理）：
1. 人工 Review Gate 处置 33 条（含 Manner 候选 REJECT 建议、港汇户外候选补证）；
2. 2 条残留 search_snippet 候选核验后才能走 Pre-Publish Validation；
3. schema 提案评审：`pet_stroller_rental` 结构化、`pet_swimming_pool` 维持 gap 记录。

## 12. 产物清单

| 类别 | 文件 |
|---|---|
| Review | `docs/reality_audit/REVIEW_WORKLIST_R1.md`、`docs/reality_audit/EVIDENCE_REPAIR_LOG_R1.md` |
| Schema | migration `a7f3c2d91e04`（rule_exception）、`b5e8d2c4a710`（evidence_strength）；ADR-020/021/022 → `DECISIONS.md` |
| 测试 | `tests/unit/test_rule_exceptions.py`（13）、`tests/integration/test_rule_exceptions.py`（3）、`tests/fixtures/real_world_regression.json` + `tests/unit/test_real_world_regression.py`（13）；全量 238 |
| Audit | `docs/reality_audit/real_pilot_samples_r2.json` → `docs/reality_audit/real_pilot_02/`（报告三件套） |
| 脚本 | `scripts/evidence_repair_r2.py`（修复入库，全程 audit_log）、`scripts/gen_regression_fixture.py`（夹具再生成） |
| 代码 | publish_gate.py（六检）、evidence_service.strength_for_artifact、v05_resolver/evaluator 例外支持、v05 API（rule-exceptions 端点 + monitor 链修复）、PetAccessJSON exceptions |
