# MIGRATION_SPEC_v0.5.md

原则：
- additive first
- old data readable
- old API stable
- idempotent backfill
- upgrade/down/upgrade

预计新增：
- media_object
- rule_candidate
- data_source_job
- source_monitor
- freshness_policy
- boundary_profile
- boundary_preference
- amenity
- entrance
- access_path
- organization
- policy_template
- policy_template_rule
- place_policy_binding/override
- event/temporary policy
- data_license

AccessRule 增量：
- rule_layer
- origin metadata
- freshness/review metadata
- template/event refs as needed

Backfill：
- operator claim → OPERATOR_POLICY
- jurisdiction source → LEGAL/GUIDANCE 按现有语义判断
- 无法确定 → REVIEW_REQUIRED，不猜

回滚：
down migration 能回升级前 schema；若数据不可逆，先导出并在文档说明。
