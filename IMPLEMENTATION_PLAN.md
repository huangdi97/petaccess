# IMPLEMENTATION_PLAN.md

> **Historical scaffold / not a live completion ledger.**
>
> 这份 Phase 清单来自早期工程启动阶段，未随实际完成状态逐项回填，因此所有 `[ ]`
> 不能解释为“当前未实现”。执行 Agent 必须以 `PROJECT_STATE.md`、PR/CI、当前代码和
> v0.10-R1 母版作为事实源。
>
> Runtime convergence：当前 Consumer 为 `apps/client-h5`；Windows / Android 使用
> Tauri 2。早期 `apps/client` uni-app x 仅保留为 legacy reference。Phase 12 中
> WeChat / iOS / HarmonyOS 属未来渠道重新决策项，不得据此恢复旧客户端作为当前实现。


## Current execution board — 2026-10-13

> 这一节是当前执行入口；下面的 Phase 0–13 仅保留历史结构，不作为完成度判断。

| Area | Current truth |
| --- | --- |
| Canonical Consumer | **IMPLEMENTED** — `apps/client-h5` |
| Windows runtime | **IMPLEMENTED / CI RUNTIME PASS** — Tauri 2 WebView2 Preview workflow |
| Android runtime | **IMPLEMENTED / CI RUNTIME PASS** — isolated Tauri Preview APK, API 35 + 36 packaged-WebView evidence |
| Android ARM64 preview | **IMPLEMENTED** — isolated `com.petaccess.map.preview`, USB + `adb reverse` path |
| Android standalone phone preview | **IMPLEMENTED WORKFLOW / EXTERNAL API REQUIRED** — requires a real public HTTPS PetAccess API |
| Home / Search / Map / Place | **IMPLEMENTED** — Consumer Discovery visual line, responsive gates, packaged runtime screenshots |
| Reality / Evidence | **IMPLEMENTED** — separate fact/provenance surfaces; packaged runtime semantic + screenshot evidence |
| Contribution | **IMPLEMENTED** — five governed fact types + review boundary + authenticated Android runtime coverage |
| Mine / Boundary / Notifications | **IMPLEMENTED** — current personal-center flow; Android authenticated-state coverage |
| Operator claim | **IMPLEMENTED** — identity verification flow; claim does not mutate rule truth |
| Watch / change tracking | **IMPLEMENTED** — rule and reality subscriptions remain separate |
| Real map provider | **BLOCKED_EXTERNAL when key/provider absent** — simplified spatial fallback must stay explicit |
| Public/staging backend | **BLOCKED_EXTERNAL** — required before a phone APK can work standalone without USB reverse |
| Human visual acceptance | **PENDING USER REVIEW** — machine PASS does not authorize baseline promotion |
| PR / master / tag / Release | **HOLD** — PR #1 remains draft until Human Visual Acceptance |

### Remaining executable work

1. Continue visual/product polish only where current Web / Windows / Android runtime evidence shows a real defect or clear product-quality gap.
2. Keep Preview / Release runtime boundaries and evidence truthful; no legacy `apps/client` resurrection.
3. Regenerate authoritative Web / Windows / Android evidence for the **same final HEAD** after source changes.
4. Do not mark the PR ready, merge, tag, promote visual baselines, or publish a Release until the user explicitly accepts the current visuals.
5. When a real public HTTPS API and real-map credentials exist, run the standalone phone-preview workflow and record those as external runtime evidence rather than simulated PASS.



## Phase 0 Foundation
- [ ] repo/toolchains
- [ ] Docker
- [ ] lint/typecheck/test
- [ ] env/health

## Phase 1 Database
- [ ] PostGIS
- [ ] models
- [ ] migrations
- [ ] seed
- [ ] indexes

## Phase 2 Rule Spec
- [ ] schemas
- [ ] evaluator
- [ ] fixtures
- [ ] unit tests

## Phase 3 API
- [ ] auth/session
- [ ] pets
- [ ] places/zones/geometry
- [ ] rules/evaluate
- [ ] sources
- [ ] observations
- [ ] verification
- [ ] operator
- [ ] regulations
- [ ] dispute
- [ ] watch
- [ ] admin
- [ ] TS client

## Phase 4 Admin
- [ ] CRUD
- [ ] moderation
- [ ] geometry
- [ ] operator
- [ ] dispute
- [ ] conflicts
- [ ] data quality
- [ ] audit

## Phase 5 Client Core
- [ ] onboarding
- [ ] pet
- [ ] map
- [ ] modes
- [ ] search/filter
- [ ] place
- [ ] zone
- [ ] rule result
- [ ] contribution
- [ ] watch

## Phase 6 AI
- [ ] provider
- [ ] pet vision
- [ ] OCR
- [ ] NL query

## Phase 7 Verification
- [ ] quick confirm
- [ ] proximity
- [ ] upload
- [ ] moderation
- [ ] anti-abuse

## Phase 8 Operator
- [ ] claim
- [ ] verify
- [ ] questionnaire
- [ ] versioning
- [ ] E2E

## Phase 9 Jurisdiction
- [ ] regulation
- [ ] resolver
- [ ] lifecycle

## Phase 10 Dispute
- [ ] notice
- [ ] counter
- [ ] review
- [ ] audit
- [ ] E2E

## Phase 11 Watch
- [ ] subscription
- [ ] event
- [ ] worker
- [ ] notification

## Phase 12 Cross-platform
- [ ] H5
- [ ] WeChat
- [ ] Android
- [ ] iOS
- [ ] HarmonyOS

## Phase 13 QA / RC
- [ ] full tests
- [ ] security
- [ ] rollback
- [ ] backup/restore
- [ ] release docs
- [ ] final report
