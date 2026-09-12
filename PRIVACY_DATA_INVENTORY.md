# PRIVACY_DATA_INVENTORY.md

日期：2026-09-13（PART A · A9）· 基于模型/代码核查与测试证据。

## 数据清单（收集什么、存哪、多久）

| 数据 | 位置 | 形态 | 保留策略 | 依据 |
|---|---|---|---|---|
| 用户账户 | `user` | email + display_name + bcrypt hash | 账户生命周期 | 注册流程 |
| 宠物档案 | `pet` | 用户主动填写（species/breed/体重等） | 账户生命周期 | 用户可控 |
| 位置（nearby） | 请求期内存 | **仅查询参数，不落库** | 不保存 | ADR-012 |
| 用户观察位置 | `observation` / `verification_event` | **分桶**：`distance_bucket` / `accuracy_bucket`（16/20 字符枚举），无原始坐标、无连续轨迹 | 随观察保留 | GOAL #15、模型实查 |
| 上传媒体 | `media_object` + MinIO | `privacy_class` 字段 + sha256 去重 | `expires_at` TTL（`test_ttl_purge_removes_expired` 真跑） | Track A1 |
| 证据（Evidence） | `evidence_bundle` / `source_artifact` | 公开页面引文/哈希/URL + 派生引用；设计上不含用户 PII | 随候选/规则保留（可追溯要求） | ADR-006、V37–V39 |
| 边界偏好 | `boundary_profile` / `boundary_preference` | 最小化：仅 (attribute, stance) 二元组 | 用户可改/删 | COEXISTENCE_BOUNDARY_SPEC |
| 审计日志 | `audit_log` | 动作/目标/主体（管理侧） | 长期（合规要求） | G16 |
| 通知 | Redis mock sink | 标题/正文（场所名+规则数），无 UUID 无位置 | 24h expire | mock 通知实现 |

## 逐项核查（A9 要求）

1. **raw GPS 不长期默认保存** — PASS。位置只进分桶字段；无 location history 表；
   ADR-012 + G15 测试锁定。
2. **media 默认 private** — PASS。`privacy_class` 非空默认；对象仅经 presigned URL 访问
   （`test_upload_minio_object_metadata_and_presigned`）。
3. **Evidence 不保存无必要 PII** — PASS（设计核查）。证据面向公开来源（官方页面引文/哈希）；
   用户上传证据走 media 管线（private + TTL + 审核），非公开人物素材无收集理由。
4. **face / license plate redaction** — **NOT_PRESENT（如实登记）**。当前无自动脱敏能力；
   缓解：media 默认 private、审核队列人工把关、TTL 自动清理。登记为
   TECH_DEBT TD-05（真实数据扩量前需补能力或策略），并作为 PART B 隐私约束执行：
   试点不采集含人脸/车牌特写的素材。
5. **evidence retention / deletion** — PASS（部分）。媒体有 TTL；证据包以可追溯性要求长期
   保留（产品语义：来源变更可审计）；删除走候选驳回 + media delete 流程。
6. **BoundaryProfile 最小化** — PASS。仅 attribute+stance，无自由文本、无位置。
7. **小区不存住户养宠档案** — PASS。`residential_community` 仅作为 place_type；
   无住户/住户宠物模型（全库 39 表核查无 resident 类实体）；松风社区 demo 只含公共区域规则。

## 结论

隐私基线 **PASS**（7 项中 6 项有代码/测试实证；redaction 能力如实登记为缺口并给出
缓解与 PART B 执行约束）。小区住户数据、连续轨迹、遇宠率三项产品红线持续为零。
