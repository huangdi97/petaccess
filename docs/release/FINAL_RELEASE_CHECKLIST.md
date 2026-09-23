# FINAL_RELEASE_CHECKLIST — v0.9 Public Beta（2026-09-23）

> 发布前逐项核验清单。所有"已就绪"为本会话真实实测；"待外部/人类"如实标记。
> 判定：READY_FOR_PUBLIC_BETA = **NO**（见 PUBLIC_BETA_RC_REPORT.md）。

## A. 冻结前（当前状态）

- [x] worktree clean @ `6a48135`
- [x] migration head 已知：`e9f2c1d4a5b6`（双环境实测），`alembic check` 无 drift
- [x] 全量 pytest：889 passed / 2 skipped
- [x] ruff / ruff format / mypy（97 files / 0 errors）
- [x] H5 + Admin vue-tsc + build
- [x] Playwright E2E：18 passed
- [x] Visual regression：17 基线 PASS；a11y 机器可判定项 0
- [x] Security：CRITICAL=0 / HIGH=0
- [x] Backup/Restore drill：PASS（2026-09-23）
- [x] Observability：应用层端点实测可用
- [x] 已知限制记录（Map Mock / Reality 0 数据 / License 0 行 / 无公网环境）

## B. 发布前必须补齐（当前缺口）

- [ ] **Reality 数据**：8 表 0 行 → 真实贡献 + 人工核验（Phase 21，不可造数）
- [ ] **License 落库**：data_license 0 行 → 人类确认 36 来源许可 + 回填（Phase 22 FAIL 项）
- [ ] **Map 真实 provider**：TENCENT_MAP_KEY（B-04，BLOCKED_EXTERNAL）
- [ ] **Staging**：独立环境 + 全 smoke（Phase 31，BLOCKED_EXTERNAL）
- [ ] **UAT**：7 类真实角色（Phase 32，BLOCKED_HUMAN）
- [ ] **Production Infrastructure**：域名/HTTPS/生产 DB/对象存储/监控（Phase 30，BLOCKED_EXTERNAL）
- [ ] **Compliance**：备案/隐私条款/地图 SDK 条款/许可确认（Phase 27，BLOCKED_HUMAN）
- [ ] **Release Authorization**：`PUBLIC_BETA_RELEASE_AUTHORIZATION`（huangdi97，Phase 35，BLOCKED_HUMAN）

## C. 授权后的执行顺序（Phase 36）

1. [ ] confirm RC commit `6a48135` + worktree clean
2. [ ] confirm migration plan `e9f2c1d4a5b6` + 最新 backup
3. [ ] 部署 backend → `alembic upgrade head` → 部署 Consumer → 部署 Admin → 启动 worker（--beat）
4. [ ] 验证 SourceMonitor / map provider / media / 全 smoke
5. [ ] T+5min / T+30min / T+2h / T+24h / T+72h 监控窗（Phase 37）

## D. 结论

```
READY_FOR_PUBLIC_BETA = NO
PUBLIC_BETA_RELEASED  = NO
```
B 组 8 项全部完成且人类授权后，方可翻转。不得在授权前声称已发布。
