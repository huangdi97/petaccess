# ADR-031 — 但书的持有人是规范的一部分：holder scope 生效 + 禁止存在性语义

- Date: 2026-09-18
- Status: accepted
- 关联：ADR-025（本体父关系不得扩张法律效力）、ADR-028（过宽术语拆分）、
  ADR-030（辖区级法定但书）

## Context

1. **P0-01**：`holder_scope` 列存在于 `rule_exception` / `jurisdiction_exception` /
   `access_rule` / `rule_candidate`，但 resolver 从不读取。`app.rulespec.holder_scope_allows`
   在 `app/rulespec/` 之外没有任何调用点。结果是《上海市养犬管理条例》第二十三条但书
   「盲人携带导盲犬的，不受本条规定的限制」被当成「导盲犬可以进入」——对**任何**携犬人
   无条件放行。这比它引用的法律更宽，且带法条引用，比什么都不说更糟。
2. **P0-02**：未点名角色的 `service_dog` 查询会展开为 4 个协助角色，只要其中一个命中
   导盲犬但书，父查询就整体 `allowed`。这是用**存在性语义**（"某个子角色命中"）冒充法律
   结论——与 ADR-025 禁止的本体扩张是同一类错误，只是发生在查询侧。

两者都由 BATCH_02 预授权审计（2026-09-18）实测发现，不是推测。

## Decision

1. **holder 条件进入判定式。** 例外只有在
   `subject matches AND holder matches AND jurisdiction matches AND provision matches
   AND time valid` 时才应用。任一条不满足即不应用。
2. **四态，不是布尔。** `HolderMatch = NOT_REQUIRED | MATCHES | DOES_NOT_MATCH | UNKNOWN`。
   "未提供上下文"（`UNKNOWN`）与"明确不满足"（`DOES_NOT_MATCH`）是两种不同的状态：
   把前者当后者会拿"缺输入"冒充法律结论，把前者当 `MATCHES` 会无条件放宽。
3. **未知 ⇒ conditional，不是 allowed 也不是 prohibited。** 答案降为 `conditional`
   并在 `missing_inputs` 里写 `holder_scope`；答 `prohibited` 会把法定权利藏在缺失输入后面。
   降级只在被扣留的例外**确实指向当前产生该禁令的基底**时发生，否则运营方层的扣留例外
   会看起来像放宽了法定禁令。
4. **carve-out 必须完整覆盖查询。** `carve_out_covers(query, …)` 要求 `query ⊆ carve-out`，
   与基础规则的 `rule_governs`（存在性）刻意不同：禁令写「犬」可以管住一个没说清的
   服务犬问题；豁免写「导盲犬」不能回答这个组查询。未点名角色 ⇒ `conditional` +
   `missing_inputs=['service_role']`。
5. **holder 条件来自例外自己的行。** 只有声明了 `holder_scope` 的 carve-out 才被约束；
   OPERATOR_POLICY 若来源本身没有持有人限定，不被法条用语污染。分层继续独立。
6. **隐私边界。** `HolderContext` 是临时、查询期的 dataclass：不落库、不进
   `PetProfile`、没有默认"否"。残障状态若未来要持久化，是独立的隐私设计 + 用户授权。
7. **不双重生效。** 同一 base 上效果只算一次，第二条以 `duplicate_exceptions` 保留
   provenance。冲突仍然优先于扣留：两条例外相互矛盾时先记 `REVIEW_REQUIRED`。
8. **历史行不迁、不删。** 已发布的 5 条 LEGAL 导盲犬例外保留；迁移计划另出
   （`docs/governance/LEGACY_EXCEPTION_MIGRATION_PLAN.md`），执行需新 revision + 新人工审查。

## Consequences

- 线上答案变化（修复本身）：generic `service_dog` 与"导盲犬但未声明持有人"两类查询
  由 `allowed` 变为 `conditional`。消费者须靠 `missing_inputs` 触发追问（渐进式提问的
  UI 未做，后端契约已提供 `holder_scope` / `service_role` 两个 token）。
- 既有测试有 7 处（单元）+ 2 处（集成）+ 3 处（真实世界回归夹具）按新语义更新；
  夹具期望值由人工修改并写明理由——`gen_regression_fixture.py` 是用 resolver 输出反推
  期望值的，重跑会把新语义固化成 tautology，因此不能用来"重新生成"。
- `access_rule` 无法条引用列，法条级区分仍只能用（法律文件, layer, effect, scope）近似。

## Evidence

- `scripts/adr030_holder_scope_probe.py`：生产库 11 个 LEGAL 基底 × 8 类查询 × 2 模式，
  全部安全计数为 0；`JURISDICTION_EXCEPTION_MATCHED = 11/11`。
- `tests/unit/test_adr030_holder_scope.py`（20 项，含 §22 的 13 项与安全计数矩阵）。
- `pytest` 单元 600 passed / 集成 124 passed 2 skipped；`ruff check/format` PASS；
  `mypy` 86 文件 Success。
- 报告：`docs/governance/ADR030_HOLDER_SCOPE_CLOSURE_R1.md`。
