# RULE_RESOLVER_SPEC.md

## 输入
- jurisdiction
- date_time
- place
- zone
- animal profile
- action
- organization binding
- event context

## RuleLayer
- LEGAL
- REGULATORY_GUIDANCE
- OPERATOR_POLICY
- TEMPORARY_POLICY

Observation 不进入 normative resolver。

## 解析维度
- mandatory/advisory/operator discretion
- scope
- animal
- action
- place
- zone
- time
- supersedes
- exception
- inherited template
- explicit override

## 输出
- applicable_rules
- suppressed_rules
- unresolved_conflicts
- explanation_steps
- compliance_state

## Compliance
- CONSISTENT
- POTENTIAL_CONFLICT
- REVIEW_REQUIRED
- UNKNOWN

## 禁止
- 自动写“违法”
- last-write-wins
- Observation 改 normative result
- 低层 policy 自动覆盖明确 mandatory legal constraint
