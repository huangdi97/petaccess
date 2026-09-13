# WORKBUDDY_PRODUCTION_START_PROMPT.md

你现在继续当前同一个“宠物准入与公共空间共处规则平台”仓库。

不要新建项目，不要从头重做，不要 reset/clean。

完整读取：
- `WORKBUDDY_PRODUCTION_MASTER_GOAL.md`
- `UI_UX_IMPLEMENTATION_SPEC.md`
- `PRODUCTION_ACCEPTANCE_MATRIX.md`
- `LAUNCH_READINESS_CHECKLIST.md`
- 当前 `REAL_DATA_PILOT_10_R2_REPORT.md`
- 当前状态/报告/DECISIONS/BLOCKERS

然后：

1. 先做 git status/diff/log；
2. 创建 `PRODUCTION_TAKEOVER_REPORT.md`；
3. 从 P0 开始：完成 33 RuleCandidate Review + 第一批真实 Publish；
4. Gate PASS 后自动进入 30–50 Place 扩量；
5. 数据 Gate PASS 后进入产品 UX Freeze；
6. 按 `UI_UX_IMPLEMENTATION_SPEC.md` 完整重做/完善前端 UI；
7. 完成 Admin/Data Ops；
8. 完成真实地图/AI provider；
9. 完成 production hardening/security/privacy/performance/backup/observability；
10. 完成 H5/微信/Android/HarmonyOS/iOS 可完成构建；
11. 完成 Staging；
12. 完成 UAT；
13. 完成 Production Release；
14. 生成 `FINAL_PRODUCTION_READINESS_REPORT.md`。

如果遇到真实外部 blocker：
- 精确写出需要的 Key/账号/证书/法律确认；
- 只阻塞对应 Gate；
- 继续其他所有工作。

不要只给计划。
不要问我是否继续。
持续执行直到：
`READY_FOR_PUBLIC_BETA = YES`
或诚实输出明确阻塞项。
