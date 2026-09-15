# Error Model

> 统一错误模型（规范 §20）。所有对外错误都走同一条路径，不泄漏内部细节。

## 1. 领域异常

`services/api/app/core/errors.py`：

| 类 | HTTP | `code` |
|---|---|---|
| `ApiError`（基类） | 400 | `bad_request` |
| `NotFound` | 404 | `not_found` |
| `PermissionDenied` | 403 | `permission_denied` |
| `Unauthorized` | 401 | `unauthorized` |
| `Conflict` | 409 | `conflict` |
| `RateLimited` | 429 | `rate_limited` |

用法：

```python
raise ApiError("证据超过 180 天未核验，须先复核来源", code="evidence_stale")
raise NotFound("规则不存在")
raise Conflict("相同幂等键的请求正在处理中")
```

发布门禁（`app/services/publish_gate.py`）用的是带稳定 code 的 `ApiError`，
顺序固定、首个失败即抛，便于测试与评审 UX 对齐：

`evidence_bundle_missing` → `evidence_missing` → `evidence_not_traceable` →
`lead_only_source_not_publishable` → `place_match_missing` → `schema_unsupported` →
`legal_requires_mandatory_level` → `scope_normalization_incomplete` →
`service_dog_scope_unproven` → `unresolved_conflict` → `evidence_stale`。

## 2. 对外错误体

```json
{
  "error": {
    "code": "evidence_stale",
    "message": "证据超过 180 天未核验，须先复核来源",
    "request_id": "…",
    "details": {}
  }
}
```

`request_id` 由 `core/observability.py` 注入，不对外解释内部状态。

## 3. 禁止出现在响应里的东西

- SQL 语句 / ORM 异常文本
- 栈回溯
- 文件系统路径
- 密钥 / token / Authorization 头
- 内部 UUID 之外的调试节点信息（Consumer 端连 UUID 都不展示，见 §46）

`install_error_handlers` 统一接管：
`ApiError` → 上表映射；`RequestValidationError` → 400 + 字段级 details；
`IntegrityError` → 409；未捕获异常 → 500 且只暴露 `request_id`。

## 4. 日志

`core/audit.py` 的 `record_audit` 在评审/发布/撤回/取代/例外/来源变更等关键动作上落
`action / target / before_state / after_state / actor / at`。测试见
`tests/integration/test_rollback_l1.py::test_l1_withdraw_is_audited`。

**不记录**：Authorization / Cookie / 口令 / 密钥 / token / 完整敏感 payload。

## 5. 配置错误

`app/core/config.py::validate_runtime()` 在启动期抛出 `InsecureDefaultSecret`，
属于「启动即失败」，不是运行期 500（见 SECURITY_AUDIT.md §2）。
