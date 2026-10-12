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
