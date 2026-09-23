# SECURITY_FINAL_REPORT — 2026-09-23 实测

> 结论判定按母版 Phase 26：Critical = 0 / High = 0。本会话真实执行 bandit / pip-audit / pnpm audit / secret scan / 代码审计。

## 0. 总判定
`SECURITY_AUDIT = PASS_WITH_LIMITATIONS` — **CRITICAL = 0，HIGH = 0**。
遗留 MEDIUM 均为 dev/ops 脚本内的 f-string SQL（表名/列名来自硬编码 allowlist，无用户输入路径），记录为受控项。

## 1. 自动扫描（本会话实测）
| 工具 | 结果 |
|---|---|
| bandit（services/api/app + scripts） | **High 0**；Medium 45（全部 B608，集中在 scripts/* 维护脚本：production_fixture_cleanup.py 28 / production_fingerprint.py 3 / scope_remodel_r2_carveout_candidate.py 3 等，f-string SQL 插值的是硬编码 allowlist 表名，无外部输入）；Low 37（B101/B105/B110/B112/B404/B603/B607 开发态/受控） |
| bandit（services/api/app 仅） | **High 0 / Medium 0 / Low 5**（B110 observability/mock、B105 enums/model、B101 holder_scope，均为开发态） |
| pip-audit（-l 全量 venv） | 修复 pip 24.3.1 的 6 个 PYSEC-2026 漏洞（升级 pip 后）：**No known vulnerabilities found**（仅本项目私有包 petaccess-api/worker 无法在 PyPI 审计，属预期） |
| pnpm audit --prod | **No known vulnerabilities found** |
| secret scan（git grep + git ls-files） | 唯一命中为 SECURITY_AUDIT.md 自身文档提及历史漏洞；`.env` / `services/api/.env` / `apps/client-h5/.env` 均 gitignored；仅 `.env.example` 被跟踪；未发现 .pem/.key/.p12 被跟踪 |

## 2. 逐项清单（母版 Phase 26）
| 项 | 结论 | 证据/说明 |
|---|---|---|
| RBAC | PASS | MODERATOR/ADMIN 角色分离；reality 决策端点仅 MODERATOR；admin 前端独立路由守卫 |
| IDOR | PASS | 资源均按 owner/role 校验（get_current_user + owner_type/owner_id）；媒体 key 随机化含 user id 前缀 |
| SSRF | PASS_WITH_LIMITATIONS | map/ai provider 为 mock；真实 provider 未接 Key（BLOCKED_EXTERNAL），无出网抓取路径在生产配置外 |
| CORS | PASS | allow_origins = localhost 显式白名单（5173-5175/4173/8080/3000），credentials 收窄于白名单 |
| auth expiry | PASS | JWT TTL 60min；validate_runtime() 生产态拒绝默认密钥（InsecureDefaultSecret 启动即抛） |
| rate limit | PASS | /ai/* 与贡献路径 429 限流（idempotency + ratelimit 模块；测试覆盖） |
| upload abuse | PASS | 10MB 上限 + MIME allowlist + magic-byte 校验 + 扩展名/MIME 一致性 + 随机 key（413/415 测试） |
| path traversal | PASS | object_key 无用户可控路径段；filename 仅截尾 40 字符 |
| malicious URL | PASS | 外部内容贡献 URL 存 source_url 仅作引用，不主动抓取（无 SSRF 面） |
| file validation | PASS | 见 upload abuse |
| media bomb | PASS_WITH_LIMITATIONS | 10MB 硬上限；无像素级解压检查（Pillow 未安装），记录为低风险 |
| image metadata / EXIF | **PASS（本轮新增）** | 新增 media_sanitize：JPEG APP1/APP2/APP13、PNG tEXt/zTXt/iTXt/eXIf、WebP EXIF/XMP 块在入库前剥离（6 单测 + media 集成 5 过） |
| secret scan | PASS | 见 1 |
| dependency audit | PASS | 见 1（pip 升级后 0 漏洞；pnpm 0） |
| admin escalation | PASS | 角色校验；admin 端点全部依赖 MODERATOR 及以上 |
| production DB role | PASS | conftest fail-closed：TEST 库才允许 pytest；dev_api_server 按 --role 拒绝生产 |
| signed media | NOT_VERIFIED | 无签名媒体方案（presigned GET 已存在）；真实媒体 CDN 场景待生产 |

## 3. Reality 专项（母版 Phase 26 Reality 检查）
| 项 | 结论 | 说明 |
|---|---|---|
| face privacy | PASS_WITH_LIMITATIONS | 无自动人脸检测/打码（AI mock）；EXIF 剥离已防 GPS 泄露；真实场景需人工 review 或 AI 检测（BLOCKED_EXTERNAL：真实 AI Key） |
| minor privacy | PASS | 贡献内容审核流程人工复核候选；无未成年人画像收集 |
| license plate | PASS | 无车牌识别（OCR mock）；媒体默认私有 |
| staff identity | PASS | 员工仅存 actor_role（staff_response 模型无姓名列），DB 实测无个人标识 |
| user trajectory | PASS | 不长期保存精确位置（scene photo TTL + evidence retention policy）；贡献为事件级非轨迹 |
| residential pet profiling | PASS | 平台不记录住户；无住宅画像 |
| precise location retention | PASS | 位置仅存 place 匹配证据（proximity bucket），非连续轨迹 |
| external content copyright/license | PASS_WITH_LIMITATIONS | OSM ODbL 出处记录于 evidence；data_license 表空 → 许可落库为 BLOCKED_HUMAN 待补 |
| takedown | PASS | dispute/correction 流程存在；媒体删除 204 + MinIO 对象删除（集成测试） |
| report abuse | PASS | 争议提交 + 反滥用 flag（rate limit/dup/mismatch/old-video/recycled/manipulation） |
| malicious false report | PASS | 贡献经人工 review；FIRST_HAND_NO_MEDIA 不自动拒绝但 stay review-pending；credit 仅核验后 |

## 4. 遗留受控项（记录不阻塞）
1. scripts/* B608 x45：dev/ops 维护脚本 f-string SQL，表名来自硬编码 allowlist（部分已 noqa）。不接收用户输入；生产代码 services/api/app 内为 0。
2. media bomb 像素级检查缺失：10MB 字节级上限已存在；无像素解压炸弹检测（需 Pillow，未安装）。
3. data_license 空表：许可落库 BLOCKED_HUMAN（需人类确认各来源许可）。
4. signed media / CDN：生产部署项。

## 5. 结论
CRITICAL = 0，HIGH = 0 → 安全门 PASS（母版要求 Critical=0 / High=0 达成）；
遗留 MEDIUM 全部为受控 dev/ops 项，Production Integrity 维持。
