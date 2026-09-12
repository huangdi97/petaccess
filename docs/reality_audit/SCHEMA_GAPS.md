# SCHEMA_GAPS.md

- Generated: 2026-09-12T19:36:51.248386+00:00
- Source: reality-audit run over synthetic samples. Each entry is a schema-gap **candidate** observed by the audit engine, not a decision.

| kind | detail | samples |
|---|---|---|
| boundary_attribute_unknown | boundary preference `pet_swimming_pool` resolves UNKNOWN (no structured source) | syn-market-005 |
| note_only_condition | condition_type `use_pet_elevator` is recorded but never enforced | syn-mall-002 |
| unmodelled_coexistence_attribute | attribute `pet_swimming_pool` has no structured home | syn-market-005 |

