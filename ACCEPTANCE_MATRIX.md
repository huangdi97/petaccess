# ACCEPTANCE_MATRIX.md

| Gate | Acceptance | Status |
|---|---|---|
| G00 Repo | documented setup works | PASS |
| G01 Infra | PostGIS/Redis/MinIO health green | PASS |
| G02 Migration | upgrade + downgrade | PASS |
| G03 Rule Engine | unit matrix passes | NOT_RUN |
| G04 API | OpenAPI + integration | NOT_RUN |
| G05 Contract | generated TS client matches | NOT_RUN |
| G06 Admin | real CRUD/moderation/dispute | NOT_RUN |
| G07 Client H5 | pet→search→place→evaluate | NOT_RUN |
| G08 Map Mock | viewport/search/zone | NOT_RUN |
| G09 Pet AI Mock | suggestion + confirm | NOT_RUN |
| G10 Contribution | quick confirm + moderation | NOT_RUN |
| G11 Operator | claim→verify→questionnaire→rule | NOT_RUN |
| G12 Jurisdiction | regulation flow | NOT_RUN |
| G13 Dispute | E2E dispute | NOT_RUN |
| G14 Watch | rule change notification mock | NOT_RUN |
| G15 Privacy | no default continuous location history | NOT_RUN |
| G16 Security | secrets/RBAC/rate/upload | NOT_RUN |
| G17 E2E | Playwright core journey | NOT_RUN |
| G18 WeChat | build or precise external blocker | NOT_RUN |
| G19 Android | build or precise external blocker | NOT_RUN |
| G20 iOS | build or precise external blocker | NOT_RUN |
| G21 HarmonyOS | build or precise external blocker | NOT_RUN |
| G22 Docs | setup/architecture/release | NOT_RUN |
| G23 Final Audit | evidence-backed final report | NOT_RUN |

Statuses:
- NOT_RUN
- PASS
- PARTIAL
- BLOCKED_EXTERNAL
- FAIL

Never mark PASS without executing validation.
