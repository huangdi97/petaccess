# BLOCKERS.md

Template per GOAL §2: 缺什么 / 为什么 / 用户要做什么 / 拿到后执行什么 / 影响哪个 Gate。

## B-01 historical uni-app x path — RETIRED / SUPERSEDED

- Status: **RETIRED（v0.10-R1 architecture convergence）**
- Current release impact: **none**
- Canonical Consumer: `apps/client-h5`
- Canonical Windows / Android runtime: `apps/client-h5/src-tauri`（Tauri 2）
- Canonical Android release: `.github/workflows/release-ci.yml`
- Historical source retained at: `apps/client`（`LEGACY_REFERENCE_ONLY`）

The previous blocker text treated HBuilderX / uni-app x as the required Android build path. That is no longer true. v0.10-R1 converged the product onto one Vue Consumer implementation with Tauri 2 shells for Windows and Android, specifically to avoid a second Consumer implementation drifting in UI and product truth.

`apps/client` therefore must not be used for current Android screenshots, runtime acceptance, Human Visual Acceptance, or release builds. Its historical pages predate the current RealityReport / Rule + Reality + Evidence model and include legacy shortcuts that are intentionally excluded from the current release path.

Current Android development / verification path:

1. build `apps/client-h5`;
2. use `apps/client-h5/src-tauri`;
3. run `tauri android init` only for generated Android project material;
4. build/sign through the Tauri Android toolchain and the release workflow;
5. verify the resulting APK against the same Consumer UI and semantic contracts as H5.

HBuilderX is not a current Android blocker.

## B-02 WeChat mini-program path — DEFERRED, not a current release gate

- Status: **DEFERRED / FUTURE CHANNEL**
- Current Windows / Android release impact: **none**
- The historical uni-app x `mp-weixin` configuration remains only as reference and must not be treated as the canonical Consumer.
- If a WeChat mini-program is reactivated as a product target, its delivery architecture must first be re-decided against the v0.10 single-Consumer principle; do not resume by publishing `apps/client` unchanged.
- External inputs would still include a WeChat AppID, category approval and privacy-interface approval.

## B-03 mobile signing / developer accounts

- Android engineering signing/build status: **RESOLVED for the current Tauri release chain**.
- Android release workflow consumes the release keystore from GitHub Secrets, builds the Tauri Android APK, signs it, and verifies it with `apksigner`.
- Android store listing remains external-account work and is not required for local APK acceptance.
- iOS / HarmonyOS distribution credentials remain future external inputs if/when those release targets are activated.
- Do **not** use HBuilderX or `apps/client` to resolve Android signing.

## B-04 腾讯地图 Key
- Type: 第三方服务凭证
- Affected gate: G08（真实地图底图）
- Missing external input: `TENCENT_MAP_KEY_CLIENT` / `TENCENT_MAP_KEY_SERVER`
- Why code cannot complete it: Key 需腾讯位置服务账号申请并配置对应 JavaScript GL / WebService 能力与授权边界。
- Work already completed:
  - Provider-neutral fallback 只使用 **PetAccess 已收录的真实代表坐标**做聚合与点位投影，不伪造场所坐标、道路、多边形或现场证据；
  - fallback 明确标注为简化空间底图，不冒充 surveyed geography；
  - Tencent JS GL renderer、WGS84 → GCJ-02 服务端转换、GCJ-02 → WGS84 交互中心归一化均已实现；
  - Android Runtime Review Board 会记录当前 packaged surface 是 `fallback` 还是 `tencent`；
  - Phone Preview 支持 `require_real_map=true`，会在打包前同时验证 `/ai/map/config` 与 `/ai/map/translate`。
- Exact user action: 申请并配置 client/server Key → API 设置 `MAP_PROVIDER=tencent`、
  `FEATURE_REAL_MAP=true` → 配置 Key 授权边界 → 运行真实地图 Phone Preview。
- Exact verification after resolution:
  1. `/api/v1/ai/map/config` → `provider=tencent`, `real_enabled=true`；
  2. `/api/v1/ai/map/translate` → `provider=tencent`, `coordinate_system=GCJ-02`；
  3. Android packaged runtime Review Board → `Map provider = tencent`；
  4. `PETACCESS_REQUIRE_REAL_MAP=1` journey PASS。
- 影响：没有 Key 时地图功能与真实地点坐标仍可用，但只允许声明 **provider-neutral fallback**；
  不得宣称“真实腾讯底图已接入”。

## B-05 真实 AI Provider Key（vision/OCR）
- Type: 第三方服务凭证
- Affected gate: G09（真实识别）
- Missing external input: AI_API_KEY + 具体 provider 选型
- Why code cannot complete it: 无 Key 无法调用真实模型。
- Work already completed: VisionProvider/OCRProvider 接口 + Mock（确定性输出）；
  /ai/* 端点含"用户确认"契约（服务犬/体重永不由图片认定）。
- Exact user action: 选型（如通义/腾讯云）→ AI_API_KEY 填 .env → FEATURE_REAL_AI=true →
  在 app/providers/factory.py 落地对应 adapter（接口已冻结）。
- Exact verification after resolution: /ai/pet-vision 返回真实建议且要求用户确认。
- 影响：G09 以 Mock PASS，真实识别 BLOCKED_EXTERNAL。

## B-06 OAuth / 短信（登录方式扩展）
- Type: 第三方凭证
- Affected gate: 无（当前账密登录已覆盖 MVP 闭环）
- Missing external input: 微信开放平台/Apple/华为 OAuth 凭证；短信签名
- Work already completed: JWT 会话体系（注册/登录/REST），token Provider 注入。
- 影响：扩展登录方式时补充。

## B-07 生产域名 / 备案 / 法务合规确认
- Type: 主体资质与法律确认
- Affected gate: G22/G23 的上线部分（不影响本地 RC）
- Missing external input: 域名、ICP 备案、隐私政策主体、地图业务边界合规确认（design #43）
- Work already completed: 合规等待项均以 feature flag / provider boundary 隔离；未配置真实 Provider 时产品显式展示 fallback，不伪造完成状态。
- 影响：上线部署时补充。

## B-08 Signed Release Public API — FAIL-CLOSED EXTERNAL GATE

- Type: 部署基础设施 / GitHub Repository Variable
- Affected gate: Windows signed/installer artifact、Android signed APK、对外可安装 Release
- Required external input: `PETACCESS_PUBLIC_API_BASE=https://<真实域名>/api/v1`
- Why code cannot invent it: 生产 API 域名与部署环境必须由真实基础设施提供，不能为了让构建变绿伪造域名。
- Work already completed:
  - `scripts/release/verify_public_api.cjs`：要求 HTTPS、`/api/v1/ping` 与 `/health` 都证明是在线 PetAccess API；
  - `scripts/release/generate_tauri_release_config.cjs`：生成 signed-build 专用严格 CSP，移除开发用 localhost / `10.0.2.2` origin；
  - `release-ci.yml`：Windows / Android 都必须显式注入生产 API base，并在打包前验证 endpoint 已编入 Consumer；
  - engineering gate + PR CI 防止回退到 packaged dev defaults。
- Exact user action:
  1. 部署真实 HTTPS PetAccess API；
  2. 在 GitHub Repository Variables 配置 `PETACCESS_PUBLIC_API_BASE`；
  3. 确认 `/health` 与 `/api/v1/ping` 可从 GitHub runner 访问；
  4. 再授权 tag/release 流程。
- Exact verification after resolution: Release CI 的 `Verify packaged runtime API` PASS，随后 Windows/Android signed jobs 才允许执行。
- 影响：变量缺失、HTTP、错误服务或后端不可达时 **Release 必须失败**；Preview APK 不受此门限制。

---

# 2026-09-13 生产推进新增阻塞

## ENV-01 执行环境无容器运行时 ⇒ 无 PostGIS / Redis / MinIO
- Type: 执行环境
- Affected gate: P01（写库部分）/ P02 / P04 / P05 / P10 / P11 / P12 / P27 / P28 / P30 / P31
- **状态：RESOLVED（2026-09-14）** — Docker Desktop 已启动，依赖栈已就绪并通过验证
- 解除后的实测（2026-09-14）:
  - `docker-compose up -d` → `petaccess-db-1`（postgis/postgis:17-3.5，healthy）、
    `petaccess-redis-1`（redis:7-alpine，healthy）、`petaccess-minio-1`（运行中）
  - 宿主端口已映射：5432 / 6379 / 9000-9001
  - PostgreSQL **17.5** + PostGIS **3.5.2** + pg_trgm 1.6；`psycopg` 连接 **0.19s**
  - Redis **7.4.11**（PING/SET/GET 通过）；MinIO bucket `petaccess-dev` 可读写
  - `/health/components` → `all_ok: true`（postgres / redis / minio / celery nodes=1）
  - 功能性冒烟：真实空间查询 13 个场所（含距离）、MinIO put/presigned/remove 往返、
    Celery 任务经 worker 往返（`{'status': 'worker_alive'}`）
  - `alembic upgrade head` → head **f4c9d2e7a831**；**up/down/up 往返通过**
  - 全量 `pytest`（**不 deselect**）→ **319 passed / 0 failed**
  - Playwright 全量 E2E → **14 passed / 0 failed**（此前 BLOCKED_EXTERNAL）
- 解除过程中发现并修复的缺陷（均由真实数据库暴露）:
  1. **迁移约束名双前缀**（7 个，跨 4 张表）：手写迁移未用 `op.f()`，被命名约定二次加前缀
     → 已修迁移源 + 新增幂等修复迁移 `f4c9d2e7a831`
  2. **33 条候选的 `rule_layer`/`mandatory_level` 陈旧**：登记表声明 16 条 LEGAL，库中全为
     OPERATOR_POLICY ⇒ 发布将把 16 条法定规则静默降级为运营方政策
     → `scripts/backfill_candidate_rule_layer.py` 扩展为同时校正 level 并执行
  3. **发布门禁只信库中层级**：新增预检「登记表↔库」一致性校验（不一致即硬拒绝）
  4. **`RuleIn` 缺遗留值归一化**：写入 `discretionary` 报 422，而读取路径正常 → 已统一
  5. **`/places/{id}/extras` 抛 `AttributeError`**：`AccessPath` 无 `zone_id` → 已修 + 补测试
  6. **Place Detail 分区徽标复用场所级结果**：把「明确限制」误显示为「尚未核验」→ 改为按需评估分区
- 影响: 上述 gate 现可继续推进；P02 的写库部分仍需 GOV-01（具名人类签署）

## GOV-01 缺少具名人类评审员（治理红线）
- Type: 流程与治理（非技术）
- Affected gate: P01（最终签署）/ P02 / P04
- Missing external input: 一名具名的人类评审员（含角色）对 33 条候选逐条签署
- Why code cannot complete it: Master Goal §0.9 / ADR-005 / `REVIEW_WORKLIST_R1.md` 纪律规定
  **AI 不做最终规则裁决**；由 AI 代签即为项目明令禁止的「无审查批量 APPROVE」
- Work already completed: 逐条 evidence / place_match / license 摘要与建议决策
  （21 建议批准 / 8 建议批准附注记 / 3 建议挂起 / 1 建议拒绝）；
  发布脚本已实现签署门禁并 `--dry-run` 实测拒绝未签署输入；
  **2026-09-14 新增可签署工作表 `RULE_REVIEW_SHEET_R1.md`（33 行，可复现生成，
  每行含 AI 建议 / 理由 / 空白 final_decision / reviewer / reviewed_at）**
- Exact user action: 由具名评审员在 `RULE_REVIEW_SHEET_R1.md` 逐行填写后回填
  `docs/reality_audit/review_decisions_r1.json` 的 `final_decision` / `reviewer` / `reviewed_at`，
  并回答 `REAL_DATA_REVIEW_DECISIONS_R1.md` §5 的裁定项
- Exact verification after resolution: `python scripts/publish_reviewed_r1.py --dry-run` 返回 signed=true
  （当前实测：exit 3，33 行 `final_decision 未填`）

## BLK-LAYER-02 `AccessRule` 无 `mandatory_level` ⇒ 法定禁止可被运营方规则覆盖
- Type: 架构/数据模型缺口
- Affected gate: P02 的正确性
- **状态：FIXED（2026-09-14，ADR-023）**
- 原现状: resolver 的 `legal_mandatory` 分支（`v05_resolver.py:274`）要求
  `mandatory_level == "mandatory"`，但 `AccessRule` 无此列 ⇒ 对 DB 来源规则永不可达；
  且 `v05_resolver.py:409` 将非强制 LEGAL 规则排除在 `governing` 之外
- 原后果（已用测试钉住）: 运营方 `allowed` 规则会胜过《上海市养犬管理条例》第23条的法定禁止
- **处置（方案 A：Schema 修复 + ADR，明确不采用"按现状发布并登记为已知限制"）**:
  1. 一等公民词表 `MandatoryLevel`（`mandatory` / `advisory` / `operator_discretion`）
     + `normalize_mandatory_level()` 归一化遗留 `discretionary`（`app/models/enums.py`）
  2. `AccessRule.mandatory_level`（nullable String(20) + `ck_access_rule_mandatory_level`）；
     `RuleCandidate.mandatory_level`
  3. resolver：法定强制**禁止**与法定强制**条件**均构成 floor（净增能力：法定强制条件
     不再能被下层 `allowed` 静默降级）；遮蔽逻辑扩展 `drops_obligation` 分支；
     存在 `mandatory_conditional` 时 effect 合成 `allowed → conditional`
  4. 发布门禁检查 4b：`rule_layer == LEGAL` 且 `mandatory_level` 为空 ⇒ **拒绝发布**（绝不猜默认值）
  5. 迁移 `e3b7a1c4f920`：**additive**、回填**幂等**（LEGAL→mandatory；已知层→operator_discretion；
     NULL 层遗留行保持 NULL）、归一化 `discretionary`
  6. API / Admin / `PetAccessJSON` / audit / 脚本同步；新增
     `PATCH /admin/candidates/{id}/mandatory-level`（校验 + 审计）
  7. 与 `RuleLayer` / `RuleException` / supersession 正交兼容
- 测试: `tests/unit/test_mandatory_level.py`（22 用例，含 Hypothesis 性质不变量与迁移回填幂等）；
  `tests/integration/test_mandatory_level.py`（真实 DB，本轮 BLOCKED_EXTERNAL）；
  `tests/unit/test_publish_layer_integrity.py` F2 由 "open" 改为 fixed
- 参考: `DECISIONS.md` ADR-023、`P0_PUBLISH_CLOSURE_REPORT.md` §3

## BLK-LEGAL-01 法律文本未经执业律师审阅
- Type: 法律确认
- Affected gate: P07 / P16 / P12
- Missing external input: 律师对 `docs/legal/` 下 6 份草案的审阅意见
- Work already completed: 6 份草案 + 索引 + 事实基线（均有工程证据）
- Exact user action: 聘请执业律师审阅并出具意见；确认运营主体、个人信息保护负责人、数据存储地域
- 影响: `COMPLIANCE_GATE = PASS_WITH_EXTERNAL_LEGAL_REVIEW`；不得对外展示草案为正式条款

## BLK-PLAT-01 平台审核未提交
- Type: 平台审核
- Affected gate: P09 / P22 / P26
- Missing external input: 微信小程序类目与隐私接口审批；应用商店上架审核
- Work already completed: manifest 已含 `requiredPrivateInfos` 与位置用途说明；
  贡献流程为结构化表单（无自由评论区），显著降低类目风险
- Exact user action: 注册主体 → 选择类目 → 提交隐私接口审批 → 提交上架
- 影响: P22–P26 `BLOCKED_EXTERNAL`；H5 可先行 Beta，其余端 `SUBMISSION_PENDING`


---

## 2026-09-15 接管复核（AGENT_MASTER_CONTINUE）

### GOV-01 — 缺具名人类评审员（**仍成立，唯一剩余发布阻塞**）

- Type: 治理 / 人工裁决
- Affected gate: `PILOT_REVIEW_PUBLISH_GATE`、`B Publish`、30–50 Place 扩量
- Missing external input: 具名人类评审员对 R2 的 33 条候选逐条给出最终决定
- Work already completed:
  - R2 全套已生成且可复现：`docs/reality_audit/review_decisions_r2.json`、
    `HUMAN_REVIEW_PACKET_R2.md`、`HUMAN_REVIEW_QUICK_TABLE_R2.md`、
    `HUMAN_REVIEW_DECISIONS_R2.json`、`scripts/gen_human_review_packet_r2.py`
  - R1 的 AI 建议**未被继承**（R1 建立在已被 ADR-025 撤回的 `service_dog` 泛化上），
    33 条建议全部按源忠实 scope 重算
  - 发布工具就绪：`python scripts/publish_reviewed_r1.py --dry-run`（自动读 R2 登记表），
    含「登记表 ↔ 库」一致性校验 + Pre-Publish Validation 六闸
  - `test_11b_no_registry_row_is_pre_signed_by_the_agent` 把「AI 不代签」钉成回归测试
- Exact user action（四步）:
  1. 在 `HUMAN_REVIEW_DECISIONS_R2.json` 填顶层 `reviewer`（具名）与 `reviewed_at`（ISO 8601）；
  2. 逐条填 `final_decision` ∈ {`APPROVED`,`APPROVED_WITH_NOTE`,`HOLD`,`REJECTED`}（+ 可选 `review_note`）；
  3. 回填 `docs/reality_audit/review_decisions_r2.json` 的
     `final_decision` / `reviewer` / `reviewed_at`（发布脚本读该文件）；
  4. 由人类执行 `python scripts/publish_reviewed_r1.py --execute --reviewer "<具名>" --max-approve 20`
- 影响: `PILOT_REVIEW_PUBLISH_GATE = BLOCKED_HUMAN`；
  30–50 Place 扩量 = **NOT_ALLOWED**（两 Gate 必须同时 PASS）；
  **但 A / C 两线不受阻塞，已分别 PASS**

### 复核期内已修复、不再构成阻塞

| ID | 内容 | 处置 |
|---|---|---|
| T-01 | 迁移 `a2d5e8b91c47` 被"部分应用后打标"⇒ `rule_exception` 缺 5 列 | FIXED — 幂等修复迁移 `c1f7a3e8d502` |
| T-02 | ADR-025 精确 scope 未同步旧测试/旧数据（19 例红） | FIXED — 见 `ANIMAL_SCOPE_REMODEL_FINAL_REPORT.md` |
| T-03 | `reality_audit` 忽略注入 `now`（测试随真实日期漂移） | FIXED — threading `now` + 样本去 time-bomb |
| T-05 | `policy_template_rule` 缺 scope 列（模板 service_dog 条目静默失效） | FIXED — 迁移 `d4a8b2f6c903` |

### 当前仍成立的外部阻塞（按现状重核）

以下项目只阻塞各自对应的 Gate，不应被扩大解释为“整个 PetAccess 都不能继续”：

- `GOV-01`：R2 规则候选缺具名人类评审员最终签署；
- `BLK-LEGAL-01`：法律文本仍需执业律师审阅；
- `BLK-PLAT-01`：应用商店 / 小程序等平台审核尚未提交；
- `B-04`：腾讯地图 client/server Key 未提供，因此只能声明 provider-neutral fallback；
- `B-05`：真实 Vision/OCR Provider Key 未提供，真实 AI 识别保持 BLOCKED_EXTERNAL；
- `B-07`：生产域名、备案与正式法务主体信息未冻结；
- `B-08`：signed Release 需要真实 HTTPS `PETACCESS_PUBLIC_API_BASE`；
- standalone **Android Phone Preview** 需要 `PETACCESS_PHONE_PREVIEW_API_BASE`，当前 workflow 会显式显示
  `BLOCKED_BY_API_BASE`；这不阻塞 USB Preview / emulator Preview。

以下旧项**不再属于当前 Android / Consumer 阻塞**：

- `B-01` 已 RETIRED：uni-app x / HBuilderX 不是当前发行路径；
- `B-02` 是未来 WeChat channel 的 DEFERRED 项，不是当前 Windows/Android gate；
- `B-03` Android 工程签名链已 RESOLVED；只剩商店账号/提交属于外部发行工作；
- `B-06` OAuth / 短信属于可选登录方式扩展，当前账密登录闭环不依赖它。

因此不要再使用旧的“`B-01…B-07` 全部仍成立”概括。

---

## 2026-09-22 会话追加（v0.9-R1 Reality Layer 六阶段推进）

### LOCAL_DOCKER_DESKTOP_ENGINE_UNSTABLE —— Docker daemon 不可达（当前）

> 状态：BLOCKED_EXTERNAL（本轮只探测与记录，不做启动循环；契约边界 #2）

- Type: 执行环境
- Affected gate: AC2–AC5（Reality DB Migration Verification / 真实持久化 /
  Migration Drill / 验证文档 PASS）、PostgreSQL 集成、全量 pytest
  （root conftest fail-closed 需要 TEST DB）、Playwright
- 实测（2026-09-22 12:44 UTC+8，原始输出存档 scratch `ac1-docker-probe/`）:
  - `docker version` → client 29.2.1 OK，daemon 连接失败
    （npipe `//./pipe/dockerDesktopLinuxEngine` 找不到，exit 1）
  - `docker ps -a` → 同上（exit 1）
  - named pipe 探测：`\\.\pipe\docker_engine` = False、
    `\\.\pipe\dockerDesktopLinuxEngine` = False
- 历史对照: ENV-01（2026-09-14）曾 RESOLVED（PostgreSQL 17.5 + PostGIS healthy、
  alembic up/down/up 通过、319 passed）；本会话实测再次不可达。
- Work completed without DB: Reality 静态审计（migration↔ORM 对照）、
  ruff + mypy + 非 DB 测试子集 28 passed、AC5 文档（NOT_VERIFIED）、
  测试盘点、Divergence / CoexistenceSnapshot / Consumer / Admin 代码推进。
- Exact user action: 启动/修复 Docker Desktop（本会话按契约不代做启动尝试）；
  daemon 稳定后执行 `alembic upgrade head` + `docs/reality/REALITY_DB_MIGRATION_VERIFICATION.md`
  的执行步骤。
- Exact verification after resolution: `docker ps` 正常 →
  `uv run python scripts/isolated_db.py --role TEST --reset` →
  `DATABASE_URL=…petaccess_test uv run pytest -q` 全量绿；
  `docs/reality/REALITY_DB_MIGRATION_VERIFICATION.md` 结论改 PASS。
