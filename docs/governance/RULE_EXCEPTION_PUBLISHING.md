# RuleException 的发布（RULE_EXCEPTION_PUBLISHING）

> P0-01 / POST_SIGNATURE_PUBLISHER_CLOSURE_R1
> 相关：`docs/governance/PUBLISH_PLAN_MODEL.md`、ADR-025、ADR-028

## 1. 为什么例外不能当普通规则发布

《上海市养犬管理条例》第二十三条禁止携犬进入商场，其但书豁免导盲犬。
这是**一条**规范陈述：广 scope 被禁，窄 scope 被豁免。

把它建模成第二条方向相反的 `AccessRule` 会在 resolver 里表现为
「两条同层规则，取最严」——豁免静默失效（`RuleException` 模型 docstring 记录了这个缺陷）。
所以 carve-out 必须写成 `rule_exception` 行，挂在**base 规则**上：

```
AccessRule(prohibit, scope=dog)
   └── RuleException(allow, scope=service_dog → guide_dog, exempt_from_prohibition)
```

## 2. 层内绑定不变量（RULE_EXCEPTION_LAYER_AND_BINDING_CLOSURE）

resolver 合成时 `rule_exception` **继承 base 的层**。因此：

| 例外层 | 只能绑 |
|---|---|
| `LEGAL` | `LEGAL` base |
| `OPERATOR_POLICY` | `OPERATOR_POLICY` base |

跨层绑定被拒绝，且**在写入边界拒绝**，不是只靠计划正确：

- 计划侧：`binding_closure_problems()` 先校验登记表绑定表自洽；
  `cross_layer_violations()` 把跨层绑定计为 `CROSS_LAYER_EXCEPTION`；
- 写入侧：`candidate_service.publish_exception()` 校验 `base.rule_layer == candidate.rule_layer`，
  否则抛 `cross_layer_exception_binding`，整个事务回滚。

理由：运营方写「允许」不得把法规层禁令放宽。运营方豁免只在自身层内替换运营方 base。

**运营方"允许"≠ 法律禁令的例外**：若无同 subject 的法律/行政依据，该行判 HOLD
（`LEGAL_BASIS_FOR_OPERATOR_EXCEPTION_NOT_EVIDENCED`）。
先例：上海图书馆写明「军警犬除外」，而第二十三条只法定例外导盲犬 ⇒ `lib-sd-op-military` /
`lib-sd-op-police` 一人类 HOLD。**即使 `lib-pets-op` 已 APPROVED，它们也不进入发布计划**。

## 3. 例外候选如何被识别（不硬编码 ID）

识别依据是登记表的 **canonical binding metadata** `exception_plan[]`
（由签署包生成器从数据库证据链推导，生成期有 `validate_exception_binding` 兜底）：

```
exception_plan[i].mode == "rule_exception"
exception_plan[i].bases[]  ← 只取 same_layer=true 的项
```

`cross_layer_dropped` 只作历史记录，**不构成依赖**。
因此未来批次新增 carve-out 会自动被识别，不需要有人记得往代码里加 ID。

## 4. 发布顺序与依赖

```
STEP n    CREATE_ACCESS_RULE      candidate = fp-legal-dog
STEP n+1  CREATE_RULE_EXCEPTION   candidate = fp-sd-legal   depends_on = fp-legal-dog
```

- 例外恒排在 base 之后（排序键 `(可写, 是否例外, rule_id)`）；
- base 不在本批 / 层不一致 / base 不可发布 ⇒ 例外转 `BLOCKED`，原因写明；
- 执行路径 `published_base_for()` 只从**本批已发布的 base** 取 `AccessRule.id`，
  不会按 place/source 去猜一个 base。

## 5. 写入模型

`candidate_service.publish_exception(db, candidate, base_rule_id=…, reviewer_id=…)`：

1. 候选必须 `APPROVED`；
2. base 必须存在、`status == current`、层一致；
3. 来源必须存在（`rule_exception.source_id` 为 NOT NULL）；
4. **仍走完整 Pre-Publish Validation**（carve-out 是正式规范陈述，不是备注）；
5. 写 `RuleException`，逐字带上 ADR-025 scope 层：
   `source_scope_exact` / `subject_scope_normalized` / `normalization_type` /
   `normative_effect` / `holder_scope`；
6. 以 CAS（`review_status == APPROVED` → `PUBLISHED`，`published_rule_id = base.id`）收尾；
   失败即整事务回滚，不留半挂载的例外。

HTTP 面：`POST /api/v1/admin/candidates/{id}/publish` 可选 body
`{"exception_of_rule_id": "<base AccessRule id>"}`。
不传 body ⇒ 行为不变（发布普通 AccessRule）；传了 ⇒ 走例外路径并写
`candidate.publish_exception` 审计记录。base 由调用方**显式**给出，API 不猜。

## 6. 本轮状态

- 11 条例外候选（`dl-sd-op`、`fp-sd-legal`、`fp-sd-op-firstparty`、`gh-sd-legal`、
  `lib-sd-legal`、`lib-sd-op-guide`、`mn-sd-legal`、`qt-sd-legal`、`qt-sd-op`、
  `sb-sd-legal`、`xm-sd-legal`）在 dry-run 中被规划为 `CREATE_RULE_EXCEPTION`，
  各自带 base 依赖，**不再是** 11 条普通 `CREATE_ACCESS_RULE`；
- 3 条例外为人类 HOLD（`dl-sd-legal`、`lib-sd-op-military`、`lib-sd-op-police`），
  不进入可发布集；
- 真实发布**未执行**（`REAL_PUBLISH_EXECUTED = NO`）。
