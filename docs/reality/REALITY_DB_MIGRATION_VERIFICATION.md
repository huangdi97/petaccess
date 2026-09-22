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

---

## 附言 A — 2026-09-22 实际 DB 验证记录（Docker 短暂恢复窗口内实测）

> 本会话中 Docker daemon 曾短暂恢复（约 17 分钟窗口），期间执行了真实 DB
> 验证；随后 daemon 再次崩溃（npipe 消失）。以下输出均为真实执行记录。
> 状态升级为 **PARTIAL**（结构验证 PASS / 持久化核心 PASS / drill 未全部完成）。

### A.1 环境与 alembic（2026-09-22 实测）

```
docker compose ps
petaccess-db-1    postgis/postgis:17-3.5   Up (healthy)      0.0.0.0:5432->5432
petaccess-redis-1 redis:7-alpine           Up (healthy)      0.0.0.0:6379->6379
petaccess-minio-1 minio/minio:latest       Up                0.0.0.0:9000-9001

uv run alembic current  -> 2c7ea6ca8e30 (head)
uv run alembic heads    -> 2c7ea6ca8e30 (head)
```

`REALITY_DB_MIGRATION = PARTIAL`（此前 NOT_VERIFIED）。

### A.2 表结构验证（`scripts/reality_db_structure_probe.py`，真实输出摘要）

- 4 张 Reality 表全部存在：`reality_candidate` / `observed_presence` /
  `staff_response_observation` / `animal_facility`
- 列数：21 / 17 / 18 / 24，与 ORM 模型一一对应
- FK 13 个：place→CASCADE、zone/source/evidence_bundle→SET NULL、
  candidate_id→RESTRICT —— 全部符合模型声明
- 索引全部存在：`ix_reality_candidate_place_status` /
  `ix_reality_candidate_type_status` / `ix_observed_presence_place_time` /
  `ix_observed_presence_freshness` / `ix_staff_response_place_time` /
  `ix_staff_response_freshness` / `ix_animal_facility_place_type` /
  `ix_animal_facility_state` + PK 索引
- CHECK constraint：0（枚举以 String + 应用层校验实现，符合现状）

### A.3 持久化 drill（`scripts/reality_db_persistence_drill.py`，真实输出摘要，事务回滚）

```
CANDIDATE_CREATED   = id=4fb6b16c… status=REVIEW_PENDING verif=derived_ai_only decision=None
CLAIM_CREATED       = id=a91fb59a… scope=dog action=walking verif=human_verified freshness=RECENT
CLAIM_UPDATED       = freshness=FRESH last_verified=True
CONSUMER_VISIBLE    = 1 human-verified rows（AI-derived 行不计入消费聚合）
AI_DERIVED_ROWS     = 0
PLACE_FK            = PASS（伪造 place 被 FK 拒绝）
```

已完成：candidate create / claim create（observed_presence）/ update /
consumer query（仅 human-verified）/ Place FK。**未完成**（daemon 崩溃中断）：
candidate→claim RESTRICT 删除保护、zone FK SET NULL 行为 —— 待 Docker 稳定后
重跑同一脚本补全（脚本已修复 savepoint，可直接重跑）。

### A.4 真实缺陷：FK 约束名超长被 PostgreSQL 截断

```
声明名: fk_staff_response_observation_evidence_bundle_id_evidence_bundle (65 字符)
实际名: fk_staff_response_observation_evidence_bundle_id_eviden_d504
```

- 超过 PostgreSQL 63 字符标识符上限 → 自动截断加后缀，**约束语义不受影响**
  （仍是 evidence_bundle_id→evidence_bundle.id ON DELETE SET NULL）。
- 影响：alembic autogenerate 会看到名称漂移；与 ADR-024/ADR-026 历史同类。
- 处置建议：新增幂等修复迁移（rename constraint 至 63 字符内合法名），
  遵循 ADR-026（不修改已应用迁移）。列为 ENGINEERING OPEN，待 Docker 稳定后
  落修复迁移 + 回归。

### A.5 下次 Docker 恢复后的执行清单（增量）

1. 重跑 `scripts/reality_db_persistence_drill.py`（savepoint 版）补全
   RESTRICT / SET NULL 两项；
2. `alembic downgrade -1` → `alembic upgrade head`（AC4 drill，TEST 或
   isolated DB 上执行，不碰 production 数据）；
3. 处理 A.4 FK 名截断（新增修复迁移）；
4. `scripts/isolated_db.py --role TEST --reset` → 全量 pytest；
5. Playwright；
6. 本文件结论最终更新为 `REALITY_DB_MIGRATION = PASS`。