# REALITY_DB_MIGRATION_VERIFICATION

> 文件：`docs/reality/REALITY_DB_MIGRATION_VERIFICATION.md`
> 生成时间：2026-09-22（UTC+8 会话）
> 状态约定参照 `PROJECT_STATE.md`：仅真实数据库验证完成后才写 `PASS`，否则如实写 `NOT_VERIFIED` 并附原因。

## 结论

**REALITY_DB_MIGRATION = NOT_VERIFIED**

原因（BLOCKED_EXTERNAL）：

```
LOCAL_DOCKER_DESKTOP_ENGINE_UNSTABLE
```

本会话实测（2026-09-22 12:44 UTC+8，原始输出存档于会话 scratch
`ac1-docker-probe/`）：

```
docker version        -> Client 29.2.1 OK；daemon 连接失败
                         npipe:////./pipe/dockerDesktopLinuxEngine: The system
                         cannot find the file specified (exit 1)
docker ps -a          -> 同上 daemon 错误（exit 1）
named pipe 探测        -> \\.\pipe\docker_engine = False
                         \\.\pipe\dockerDesktopLinuxEngine = False
```

Docker daemon 未运行 / 不可达，因此：

- 无 PostgreSQL 实例可连（`.env` 的 `DATABASE_URL` 指向本机 5432，未监听）
- `alembic current / heads / upgrade head` 无法针对真实库执行
- Reality migration `2c7ea6ca8e30` 的真实 tables / columns / foreign keys /
  indexes / constraints / downgrade 验证无法执行
- ObservedPresence / StaffResponseObservation / AnimalFacility /
  Reality Review / publication 对象无法做真实 create/read/update/query
- Place FK / Zone FK / Source FK / EvidenceBundle FK / timestamp / freshness /
  operational state / deletion-revision semantics 无法做实库检查

按契约边界：不修改业务代码绕过环境、不修改 migration 迁就环境、
不用 SQLite / fake DB 代替 PostgreSQL proof → 本项如实维持
`NOT_VERIFIED`，待 Docker 稳定后立即执行本文件 §「执行步骤」。

## 已完成的静态侧核对（不依赖 DB）

以下内容已在无 DB 条件下完成，供真实验证时参考，不构成 DB 验证：

- Alembic migration `2c7ea6ca8e30_v09_reality_layer.py` 存在且为 head：
  `down_revision = 'f2a1c7d9e034'`，additive（仅 create_table / create_index，
  不动既有表结构；注释明确说明 pre-existing index drift 被刻意排除）。
- Migration 结构（静态）：
  - `reality_candidate`（candidate_type / place_id / zone_id / source_id /
    evidence_bundle_id / animal_scope / observed_at / captured_at /
    review_status / reality_decision / reviewer / decided_at / decision_note /
    freshness_state / verification_status / payload / published_claim_id /
    published_at + PkMixin id + created_at/updated_at）
  - FK：place_id→place.id(CASCADE)、zone_id→zone.id(SET NULL)、
    source_id→source.id(SET NULL)、evidence_bundle_id→evidence_bundle.id(SET NULL)
  - 索引：`ix_reality_candidate_place_status(place_id, review_status)`、
    `ix_reality_candidate_type_status(candidate_type, review_status)`
  - `observed_presence`（candidate_id→reality_candidate RESTRICT、
    place_id→place CASCADE、zone/source/evidence_bundle SET NULL；
    索引 `ix_observed_presence_place_time` / `ix_observed_presence_freshness`）
  - `staff_response_observation`（actor_role 只存角色；同样 FK/索引族簇）
  - `animal_facility`（operational_state 默认 active；
    索引 `ix_animal_facility_place_type` / `ix_animal_facility_state`）
  - downgrade() 完整：drop_index × 6 + drop_table × 4（顺序与 upgrade 逆序）
- ORM 模型 `app/models/reality.py` 与 migration 列名/约束一一对应（静态比对）。
- admin 决策端点 `POST /reality/candidates/{id}/decision` 只允许
  `reality_decision ∈ {VERIFIED, VERIFIED_WITH_NOTE, HOLD, REJECTED}`，
  仅 VERIFIED* 发布 claim（`REALITY_VERIFIED_DECISIONS` 测试钉死）。

## 执行步骤（Docker 恢复后立即执行）

```bash
docker compose up -d
docker compose ps            # postgres healthy / redis healthy
# 确认 DB URL、TEST DB != production DB（conftest 强制 TEST role）
alembic current
alembic heads
alembic upgrade head
alembic current              # 应停在 head 2c7ea6ca8e30

# 真实持久化验证（ObservedPresence / StaffResponseObservation / AnimalFacility
# / RealityCandidate review + publication）：
# - create candidate -> human VERIFIED -> claim 落库 -> 消费查询可见
# - HOLD/REJECTED -> 不发布
# - Place FK / Zone FK / Source FK / EvidenceBundle FK 行为
# - freshness_state / operational_state / last_verified_at / deleted_at 语义
# - 无 DB 时维护 BLOCKED_EXTERNAL，不 downgrade 验证依赖的临时会话

# Migration drill（policy 允许则 downgrade -> re-upgrade）：
alembic downgrade -1
alembic upgrade head
# 若不能安全 downgrade（如生产数据依赖），做 isolated DB drill 并记录真实输出
```

## 验证清单（真实 DB 通过后勾选）

- [ ] PostgreSQL healthy（`SELECT 1` / `/health/components`）
- [ ] Redis healthy
- [ ] DB URL 正确；TEST DB != production DB
- [ ] `alembic current` == `alembic heads` == `2c7ea6ca8e30`
- [ ] 4 张 Reality 表存在，列齐全
- [ ] FK 如模型声明（ondelete CASCADE / SET NULL / RESTRICT）
- [ ] 索引存在（6 + 候选 2）
- [ ] enum/constraint 正确（若无独立 enum 类型，则 String 约束 + 应用层校验已核对）
- [ ] downgrade 可执行（或记录不能安全 downgrade 的原因 + isolated drill 输出）
- [ ] ObservedPresence / StaffResponseObservation / AnimalFacility 真实 CRUD
- [ ] Reality Review（candidate 决策）→ publication 链路真实可用
- [ ] 本文件结论更新为 `REALITY_DB_MIGRATION = PASS`

## 记录方式

每次真实验证的执行输出（命令 + 原始 stdout/stderr）以附言形式追加到本文件，
不改写历史结论；或链接到 `docs/status/` 下带时间戳的验证报告。