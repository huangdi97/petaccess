# SECURITY_AUDIT.md

日期：2026-09-13（PART A · A8）· 全部结论基于本日实跑命令与代码核查。

## 1. 依赖漏洞

| 扫描 | 命令 | 结果 |
|---|---|---|
| Python | `uvx pip-audit --skip-editable` | **No known vulnerabilities found** |
| Node（全量） | `pnpm audit` | **No known vulnerabilities found** |
| Node（仅 prod） | `pnpm audit --prod` | **No known vulnerabilities found** |

## 2. Secrets

- `.env` 在 `.gitignore`（`git check-ignore` 实证）；`git ls-files` 中仅 `.env.example`。
- 对全部 tracked 文件扫描私钥头/AWS/GitHub/OpenAI/Slack/Google/JWT 模式：**0 命中**。
- 本轮修复：开发用 `JWT_SECRET` 30 字节 → 49 字节（此前 pytest 持续报
  `InsecureKeyLengthWarning`，RFC 7518 要求 ≥32 字节）。修复后全量测试警告 60 → 1。
- 默认值均为显式 dev-only 标记（`CHANGE_ME_FOR_ANY_NONLOCAL_USE` 语义保留在
  config 默认与 `.env.example`）。

## 3. API 面

| 项 | 状态 | 证据 |
|---|---|---|
| RBAC | PASS | 五级角色；`test_rbac_requires_auth` + admin/owner 用例；v05 写端点 `Depends(require_admin)` |
| 认证过期 | PASS | JWT exp（`core/security.py`），登录/注册/REST 测试 |
| IDOR | PASS | 资源按 `user.id` 过滤（pets/watches/boundary profile 归属校验）；跨用户访问测试 |
| Rate limit | PASS | Redis 限流；观察/核验 429 实测（`test_observation_idempotent_and_rate_limited_flow`、`test_verification_rate_limited`） |
| CORS | PASS | 显式 dev origin 白名单（5173/5174/5175 等 9 项），**无通配**，`allow_credentials=True` 仅对白名单生效 |
| Idempotency | PASS | `Idempotency-Key` 头 + Redis 缓存（观察/核验重放实测同 id） |
| Privilege escalation | PASS | 角色仅在 DB 侧可变；admin 端点统一守卫；无自提升路由 |

## 4. Upload 安全（media.py + test_media.py 实证）

| 威胁 | 防护 | 测试 |
|---|---|---|
| MIME 伪造 | magic bytes 校验（magic_mismatch） | `test_upload_rejects_bad_content` |
| 扩展名/MIME 不一致 | 拒绝 | 同上 |
| 不支持类型 | 白名单 | 同上 |
| 超大文件 | >10MB 拒绝 | 同上 |
| 畸形图片 | 解码校验 | 同上 |
| Path traversal | object key = `media/{uid8}/{uuid4}/{name[-40:]}`，随机 UUID 路径，不使用用户路径 | 结构核查 |
| Filename injection | 文件名截尾 40 字符且仅作展示；存储键随机 | 结构核查 |
| Decompression bomb | PNG/JPEG 解码由 Pillow 处理且大小上限前置；OCR 走 mock | 记录为低风险（本地 RC 无真实解码服务） |

## 5. SourceMonitor / 外部抓取 SSRF 防护（source_monitor.py，95% 覆盖）

| 防护 | 测试 |
|---|---|
| 仅 http/https（file:// 等拒绝） | `test_monitor_rejects_non_http_scheme` |
| 私网/回环/link-local/reserved/multicast DNS 解析拒绝 | `test_monitor_blocks_private_and_loopback_hosts` |
| DNS 失败包装 | `test_fetch_dns_failure_is_wrapped`（本轮新增） |
| 重定向逐跳重校验（含 location 协议） | `test_fetch_follows_redirect_and_revalidates_each_hop`（本轮新增） |
| `trust_env=False`（不继承代理环境） | 代码（WorkBuddy 接管修复） |
| 响应 ≤2MB | `test_fetch_rejects_oversized_payload`（本轮新增） |
| Content-Type 白名单（html/plain/json） | `test_monitor_rejects_unknown_content_type` |
| 超时（默认 5s）+ 网络错误包装 | `test_fetch_network_error_is_wrapped`（本轮新增） |

## 6. 本轮修复清单

1. `JWT_SECRET` 开发默认值 30 → 49 字节（消除 RFC 7518 告警）。
2. `candidate_service.publish()` 并发 CAS（`candidate_already_published`）——同时是
   完整性修复（防重复发布规则），见 `TEST_COVERAGE_REPORT.md` A12。

## 7. 遗留（登记，不阻塞本地 RC）

- 真实 HTTPS/域名/反代部署加固属 B-07（生产项）。
- `apps/client`（uni-app x）构建与真实地图/AI live smoke 属 B-01/B-04/B-05。

结论：PART A A8 全项 **PASS**（含 2 项修复）。
