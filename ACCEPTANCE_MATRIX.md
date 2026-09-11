# ACCEPTANCE_MATRIX.md

| Gate | Acceptance | Status |
|---|---|---|
| G00 Repo | documented setup works | PASS |
| G01 Infra | PostGIS/Redis/MinIO health green | PASS |
| G02 Migration | upgrade + downgrade | PASS |
| G03 Rule Engine | unit matrix passes | PASS |
| G04 API | OpenAPI + integration | PASS |
| G05 Contract | generated TS client matches | PASS |
| G06 Admin | real CRUD/moderation/dispute | PASS |
| G07 Client H5 | pet→search→place→evaluate | PASS |
| G08 Map Mock | viewport/search/zone | PASS |
| G09 Pet AI Mock | suggestion + confirm | PASS |
| G10 Contribution | quick confirm + moderation | PASS |
| G11 Operator | claim→verify→questionnaire→rule | PASS |
| G12 Jurisdiction | regulation flow | PASS |
| G13 Dispute | E2E dispute | PASS |
| G14 Watch | rule change notification mock | PASS |
| G15 Privacy | no default continuous location history | PASS |
| G16 Security | secrets/RBAC/rate/upload | PASS |
| G17 E2E | Playwright core journey | PASS |
| G18 WeChat | build or precise external blocker | BLOCKED_EXTERNAL (B-01/B-02) |
| G19 Android | build or precise external blocker | BLOCKED_EXTERNAL (B-01/B-03) |
| G20 iOS | build or precise external blocker | BLOCKED_EXTERNAL (B-01/B-03) |
| G21 HarmonyOS | build or precise external blocker | BLOCKED_EXTERNAL (B-01/B-03) |
| G22 Docs | setup/architecture/release | PASS |
| G23 Final Audit | evidence-backed final report | PASS |

Statuses:
- NOT_RUN
- PASS
- PARTIAL
- BLOCKED_EXTERNAL
- FAIL

Never mark PASS without executing validation.

## 证据索引

- G00: README 快速开始 + scripts/*.sh 实际执行记录
- G01: `docker compose ps` 全 healthy；healthcheck 输出（PostGIS 3.5 / Redis PONG / MinIO live）
- G02: alembic upgrade→19 表；downgrade base→2 表；再 upgrade 成功
- G03: pytest services/api/tests 15 passed（GOAL #7 十条矩阵全含）
- G04: OpenAPI 50 paths；tests/integration 13 passed（真实 PostGIS+Redis）
- G05: openapi-typescript 生成 schema.d.ts；tsc strict PASS；客户端 50 路径可调用
- G06: Admin 流程经 API 实测（登录/质量/认领/异议/审计/用户）；vue-tsc + pnpm build 通过
- G07: 浏览器手工 E2E + Playwright 5/5（注册→豆豆→答案→快速核验）
- G08: Mock 地图渲染 + nearby(ST_DWithin)/trgm 检索 + zone GeoJSON 真查
- G09: /ai/pet-vision Mock 确定性建议 + requires_user_confirmation=true
- G10: 观察/核验创建 + 幂等重放 + 限流 429（集成测试）
- G11: tests/integration::test_operator_claim_full_loop（认领→批准→问卷→版本化规则→观察保留）
- G12: tests/integration::test_regulation_review_flow + 四态 review_status 演示数据
- G13: tests/integration::test_dispute_lifecycle（提交→反声明→办结→审计）
- G14: Celery worker 真跑 notify_rule_changes；通知落 Redis；二次运行 0（幂等）
- G15: 无连续轨迹字段；仅 bucket 存取（model+seed+API）；mine 页隐私说明
- G16: .env 未入库；密钥模式扫描 0；pip-audit / pnpm audit 无已知漏洞；RBAC 401/403 测试
- G17: playwright test 5 passed
- G22: README / docs/ARCHITECTURE.md / docs/PLATFORMS.md / BLOCKERS.md / 本矩阵
- G23: FINAL_RELEASE_REPORT.md
