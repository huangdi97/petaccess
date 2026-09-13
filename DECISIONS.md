# DECISIONS.md
# Frozen Architecture Decisions

- ADR-001: Product models Access, not Friendliness.
- ADR-002: Core domain = Place → Zone → AccessRule.
- ADR-003: Place identity = platform UUID; map IDs are external refs.
- ADR-004: ObservationClaim never auto-converts to AccessRule.
- ADR-005: Deterministic rule evaluator; LLM only parses/extracts.
- ADR-006: Multi-dimensional Provenance; no core single trust score.
- ADR-007: Client = uni-app x + Vue 3 + TypeScript.
- ADR-008: Map = provider adapter; Tencent first.
- ADR-009: Backend = FastAPI + PostgreSQL/PostGIS + Redis + Celery.
- ADR-010: Admin = Vue 3 + TypeScript + Vite.
- ADR-011: OpenAPI = API contract SSOT.
- ADR-012: No default continuous location history.
- ADR-013: Residential communities = public-space rules only.
- ADR-014: User-selected filtering is neutral; editorial moral ranking is not.
- ADR-015: MVP does not depend on mass social scraping.
- ADR-016: Demo data is synthetic by default.

- ADR-017: Place.location is a denormalized geography(Point,4326) representative
  point synced by app logic; all authoritative geometry lives in place_geometry
  (Point/LineString/Polygon/MultiPolygon). Context: nearby queries need an
  indexed point without polygon centroid ambiguity. Status: accepted.
- ADR-018: Client = uni-app x source (apps/client, HBuilderX-built, all five
  targets) + platform-neutral @petaccess/client-core (shared business logic) +
  @petaccess/client-h5 Vite app as the locally verifiable H5 vehicle for
  G07/G17. Context: uni-app x has no npm CLI build path (no vite-uts branch,
  HBuilderX-only), and HBuilderX cannot be installed headlessly (BLOCKER B-01).
  The H5 app reuses the identical core; no business logic duplicated. Status: accepted.
- ADR-019: SQLAlchemy String columns store enum values; DB reads return plain
  str, so role/status comparisons use str values. response_models coerce back
  to enums at the API boundary. Status: accepted.

任何重大变更追加正式 ADR：
- Context
- Decision
- Alternatives
- Evidence
- Migration impact
- Status

- ADR-020: 分层 Animal Scope 与 RuleException（SG-REAL-01）。Context: 现实法规
  常在同一句中"广范围管制 + 窄范围豁免"（如《上海市养犬管理条例》第23条禁止犬只
  进入商场，但书豁免导盲犬）。把豁免建成第二条独立规则时，resolver 看到同层两条
  规则按最严合成，工作犬被错误禁止；且 dog（生物学范围）与 ordinary_pet（语义
  范围）混用导致猫/其他动物被法规误覆盖。Decision: (1) Rule 的 animal_scope 沿用
  五值枚举，语义固定：dog/cat=生物学范围；service_dog=以用户声明的 working/
  in_training 角色为准（永不从照片/AI 推断，design #19）；ordinary_pet=宠物一般
  性条款，自动不约束服务犬角色。(2) 新增 RuleException（rule_id, animal_scope,
  effect, source_id NOT NULL, status, effective_from/to）：异常挂在 base rule 上，
  scope 匹配该异常声明的范围、窗口内、status=current、有 source 才生效；生效时
  替代 base rule 参与合成并给出解释步骤；窗口过期/withdrawn/superseded 自动回落
  base 规则；无 source 的异常永不生效；多条匹配异常效果冲突时 REVIEW_REQUIRED，
  绝不猜测。(3) 不写死 service_dog 分支——机制对任意 (scope, effect) 组合通用。
  (4) Guide dog 不引入新枚举：= service_dog + service_role=working（用户声明）。
  (5) Observation 永不参与 normative resolver（ADR-004 不变）。Alternatives:
  独立 allowed 规则（R1 现状建模，无法表达"豁免自本条"，同层冲突静默被吞）；
  evaluator 加 service_dog if（硬编码，违背通用性要求）；LEGAL 层互斥优先级
  （改 resolver 语义，影响面最大）。Evidence: docs/reality_audit/real_pilot_01
  resolver 探针：烘焙工坊/港汇/西岸导盲犬被禁止；smoke 测试六场景全过。
  Migration impact: additive（rule_exception 表 a7f3c2d91e04）；既有独立
  service_dog allowed 规则继续合法，可与 exception 并存。Status: accepted.

- ADR-021: EvidenceStrength 是描述性采集姿态枚举，不是可信度评分。Context:
  S7 要求区分证据获取方式（官方直抓/现场取证/可靠转述/搜索摘要/用户提交/社媒
  线索），但 ADR-006 禁止核心可信度单一评分。Decision: 六值枚举存于
  source_artifact.evidence_strength，由 collector_type + source_type +
  directness 确定性映射（strength_for_artifact），无聚合、无加权、无数值。
  SEARCH_SNIPPET/SOCIAL_LEAD 证据的候选在 Pre-Publish Validation 被硬性拦截，
  强制先完成 Evidence Repair。Status: accepted.

- ADR-022: Pre-Publish Validation 是发布边界的六项硬门（S8）。Context: R1 试点
  证明"先修系统再扩量"需要机器可执行的发布前置检查。Decision: publish() 前依次
  检查 evidence（bundle/media 锚可追溯）、place match、schema support、
  unresolved conflict（同源同位同 scope/action 的效果变更按 supersession 自动
  解决并留痕；跨来源冲突必须人工解决）、freshness（≤STALE_DAYS）、data license
  （lead-only/不存储证据不得发布）。任一失败抛稳定错误码，永不静默降级。
  Status: accepted.
