# PROJECT_STATE.md

## Current phase
v0.9-R1 Reality Contribution 深化 → Public Beta RC 冻结（2026-09-23）

## Reality Layer (v0.9-R1) — 已闭环
- Reality DB Final Closure: 8 表 / 29 FK / Alembic no drift（head `e9f2c1d4a5b6`）;
  persistence drill（RESTRICT/SET NULL/downgrade-re-upgrade）真实 PASS
- RealityReport 父模型 + 7 状态枚举 + ObservationEffort + Confirmation + ExternalContentReference
  （migration `d4e7b2a8c9f1`，additive）+ reality_contribution 服务（防滥用: rate limit/dup/old-video/place mismatch）
- R-01 FK 截断：确定性名 `fk_staff_response_observation_evidence_bundle` 已落库，无 drift
- 不变量固定：content_published_at ≠ observed_at；FIRST_HAND_NO_MEDIA 保持 review-pending；
  animal_observed=false 只生成 ObservationEffort；AI 永不写 reality_decision
- 前端：RealityPanel / Contribute / Home / Admin Dashboard/Queue/Claims design-token 合规
## 质量基线（2026-09-23 全实测）
- pytest 889 passed / 2 skipped（TEST DB + Celery worker；fail-closed 生效）
- ruff / format PASS；mypy 97 files / 0 errors（canonical services/api）
- H5 + Admin vue-tsc + build PASS；Playwright 18 passed；Visual 17 基线 PASS；a11y 0 缺陷
- Security CRITICAL=0 / HIGH=0（EXIF 剥离 + staff 仅 actor_role）；Backup/Restore drill PASS
- Observability: /health /metrics /health/components 实测可用（`docs/ops/OBSERVABILITY_REPORT.md`）
## 数据（DB 实测）
- 30 real places（上海中心城区）/ 42 rules（LEGAL 14 + OPERATOR_POLICY 28）/ 36 sources / 22 monitors / 44 zones
- Reality 各表 0 行（INSUFFICIENT_OBSERVATION，未造数）; data_license 0 行（FAIL 记录）
## 发布状态
- READY_FOR_PUBLIC_BETA = NO（Reality 0 / License 0 / Map Key / Staging / UAT / Production / Compliance 阻塞）
- PUBLIC_BETA_RELEASED = NO（未经 huangdi97 授权，不伪造）
- RC 冻结报告: docs/release/PUBLIC_BETA_RC_REPORT.md / FINAL_PRODUCTION_READINESS_REPORT.md / FINAL_RELEASE_CHECKLIST.md / V09_FINAL_REPORT.md
## Known environment notes
- Docker daemon 29.2.1 可用（petaccess-db/redis/minio healthy）；Celery worker 测试期按需启动
- .env 使用 127.0.0.1 避免 localhost→::1 瞬时连接问题
## Current blockers
- B-04 腾讯地图 Key（真实地图）；B-05 AI/OCR Key；B-07 域名/备案/合规
- 新增：PUBLIC_BETA_RELEASE_AUTHORIZATION（huangdi97，Phase 35）
## Next action
- Reality 真实数据采集（禁造数）→ License 回填 → 地图 Key → Staging → UAT → 生产部署（需人类授权）
## Truth rule
Never infer PASS.
