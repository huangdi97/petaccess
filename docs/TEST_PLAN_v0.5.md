# TEST_PLAN_v0.5.md

原 baseline 全部保持 PASS。

## Resolver
- legal vs operator
- guidance
- template
- place override
- zone override
- event override
- time
- service dog
- conflict
- superseded

## Candidate
- extracted 不可直接发布
- rejected 不 effective
- published 才 effective
- idempotency
- audit

## Media
- real MinIO upload
- invalid MIME
- oversized
- delete
- TTL
- OCR task

## Boundary
- MATCH
- CONFLICT
- UNKNOWN
- no score

## SourceMonitor
- unchanged
- changed
- failed
- timeout
- candidate generated once

## Property-based invariants
- UNKNOWN never coerced to MATCH
- Observation never affects normative resolver
- expired event never current
- superseded never current
- unpublished candidate never effective
- service dog scope isolation

## E2E
1. pet → place → effective access
2. boundary → explainable match
3. upload sign → candidate → approve → rule
4. operator template → override
5. source changed → new rule → watch
6. access path / amenity display
