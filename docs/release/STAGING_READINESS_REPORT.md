# STAGING_READINESS_REPORT — 2026-09-23

> 母版 Phase 31（Staging）。独立 staging 环境需要：独立 DB / Redis / worker / 对象存储 / HTTPS。
> 当前本机只有 dev 容器栈（petaccess-*）与一次性测试库（petaccess_test / petaccess_e2e），
> 无独立 staging 域与公网入口 → 主体判定 BLOCKED_EXTERNAL。

## 0. 判定

```
STAGING = BLOCKED_EXTERNAL（无独立 staging 环境；部署项，Phase 30 前置）
```

## 1. 可在本机预演的部分（真实执行）

| 项 | 结果 |
|---|---|
| migration（fresh DB 升级） | PASS（isolated_db --reset 多次真实执行，e9f2c1d4a5b6） |
| rollback rehearsal（downgrade → re-upgrade） | PASS（2026-09-23 实测：d4e7b2a8c9f1→c3a9e5f7d1b2→2c7ea6ca8e30→re-upgrade head→探针重复） |
| Rule API smoke | PASS（全量 pytest 889 含 API 契约与 publish 回归） |
| Reality API smoke | PASS（coexistence / contribution / admin 决策端点测试全绿） |
| Map smoke | PASS（Mock provider 视口/搜索/zone 渲染；真实 Key 缺失 → BLOCKED_EXTERNAL） |
| Consumer smoke | PASS（Playwright 18 passed + visual 17 基线） |
| Admin smoke | PASS（30+ 视图 build + E2E） |
| SourceMonitor smoke | PASS（sweep 任务测试覆盖；beat 未常驻） |
| media smoke | PASS（上传/OCR/删除/TTL/EXIF 剥离测试全绿） |
| backup smoke | PASS（BACKUP_RESTORE_DRILL_REPORT：pg_dump→restore→integrity compare） |

## 2. 缺失（BLOCKED_EXTERNAL）

1. 独立 staging DB/Redis/worker/对象存储（当前与 dev 同栈，仅库名隔离）；
2. staging HTTPS 域与真实 Map/媒体/通知 provider（Key 未接，B-04/B-05）；
3. 生产角色 DB 与真实域名（B-07）。

## 3. 结论

STAGING_READINESS 的**所有本机可执行项已真实预演通过**；独立 staging 环境的搭建是
Phase 30 生产部署前置项，本机无法自建（无公网域名/证书），如实标 BLOCKED_EXTERNAL。
