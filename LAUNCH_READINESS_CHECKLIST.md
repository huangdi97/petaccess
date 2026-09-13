# LAUNCH_READINESS_CHECKLIST.md

> 最后更新：2026-09-13（GMT+8）· 基准 commit `a970a80`
> 图例：`[x]` 已达成（有证据）· `[~]` 部分 · `[ ]` 未达成 · `[B]` 外部阻塞

## 数据
- [ ] 30–50 real Places —— 当前 **10**，被 P0 Gate 阻塞
- [~] reviewed —— 审核工作稿完成（33 条），最终签署待具名评审员
- [ ] published rules —— **0**
- [~] evidence 100% —— direct-or-strong **93.9%**；已发布规则证据须 100%（尚无已发布规则）
- [x] source 100% —— 每条候选均有 Source + SourceArtifact + hash
- [x] attribution target —— 归因错误 3.0%（≤5%），且已被流程捕获未发布
- [x] no unresolved P0 schema gap —— SG-REAL-01 已修；`pet_stroller_rental` / `pet_swimming_pool` 记录为已知 gap
- [~] SourceMonitor active —— 机制与 API 存在；端到端未验证（需数据层）

## Consumer
- [~] map —— 静态占位（`MockMap.vue`），真实交互壳未实现 `[B]`
- [x] search
- [x] place detail —— 4 个板块（spec §2.4 要求 10 个 Section）
- [x] zones
- [~] coexistence —— 分区展示已有，共处边界 Section 未完整
- [x] pet profile
- [x] boundary profile
- [x] contribution
- [~] evidence upload —— 后端链路存在；前端 OCR 预览未接真实 provider `[B]`
- [x] correction
- [x] watch
- [~] privacy —— 设置入口存在；删除/导出流程未实现

## Admin
- [x] candidate
- [x] evidence
- [x] review
- [~] publish —— 接口与门禁齐备；端到端未验证 `[B]`
- [ ] rollback —— 手册已备，未演练 `[B]`
- [ ] supersession —— 代码存在，未端到端验证 `[B]`
- [x] source monitor
- [~] freshness
- [x] org/template
- [x] audit

## Engineering
- [~] tests —— 数据库无关 **132 passed**；全量无法执行 `[B]`
- [x] lint —— `ruff check .` All checks passed
- [x] typecheck —— `mypy services/api/app` 73 files no issues；H5 `vue-tsc` 通过
- [~] migrations —— 10 个 revision，含新增 `d1a4f7c93b28`；未在真实库升级验证 `[B]`
- [~] security —— 静态扫描已做（`SECURITY_AUDIT.md`）；渗透/IDOR/SSRF 未实测
- [~] privacy —— 清单 + 政策草案；删除/导出未实现
- [~] performance —— 基线存在；无生产压测
- [~] concurrency —— CAS 并发发布保护已实现；未做并发压测
- [~] backup —— 开发环境演练通过；生产未验证
- [~] monitoring —— 指标/健康/审计已有；**告警链路未接入**

## Providers
- [ ] map live `[B]`（B-04）
- [ ] OCR live `[B]`（B-05）
- [ ] notification `[B]`

## Platforms
- [x] H5 —— 构建通过
- [ ] WeChat `[B]`（B-02）
- [ ] Android `[B]`（B-01 + B-03）
- [ ] HarmonyOS `[B]`（B-01 + B-03）
- [ ] iOS `[B]`（B-01 + B-03）
- [x] external signing blockers documented —— 见 `BLOCKERS.md`

## Deployment
- [ ] staging `[B]`（ENV-01）
- [ ] HTTPS `[B]`
- [ ] secrets `[B]`
- [ ] prod DB `[B]`
- [ ] prod Redis `[B]`
- [ ] prod object storage `[B]`
- [ ] migration `[B]`
- [ ] health —— 端点已实现，未在生产验证
- [ ] monitoring `[B]`
- [ ] backup `[B]`
- [ ] rollback `[B]`

## Legal/Product
- [x] privacy policy draft —— `docs/legal/PRIVACY_POLICY_DRAFT.md`（`LEGAL_REVIEW_REQUIRED`）
- [x] user agreement draft —— 同上
- [x] methodology page —— `docs/legal/DATA_METHODOLOGY_DRAFT.md`
- [x] correction/appeal —— `docs/legal/CORRECTION_APPEAL_POLICY_DRAFT.md`
- [x] operator terms —— `docs/legal/OPERATOR_CLAIM_TERMS_DRAFT.md`
- [x] disclaimer —— `docs/legal/DISCLAIMER_DRAFT.md`
- [x] legal review status honest —— 全部标注 `LEGAL_REVIEW_REQUIRED`，未宣称已完成
- [x] platform review status honest —— 标注 `PLATFORM_REVIEW_REQUIRED`

## Final
- [ ] UAT `[B]`
- [ ] P0 bugs 0 —— 无 UAT
- [ ] P1 bugs 0 —— 无 UAT
- [ ] production smoke `[B]`
- [ ] release tag
- [x] final report —— `FINAL_PRODUCTION_READINESS_REPORT.md`

---

## 结论

```text
READY_FOR_PUBLIC_BETA = NO
```

关键路径 `P00 → P01 → P02` 未通过：P01 待具名人类评审员签署（GOV-01），P02 待数据层恢复（ENV-01）。
