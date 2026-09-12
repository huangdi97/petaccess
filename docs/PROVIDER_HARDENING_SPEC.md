# PROVIDER_HARDENING_SPEC.md

## Map
- MockMapProvider 保留
- TencentMapProvider 完整实现
- timeout/retry/error mapping
- fixture contract tests
- ExternalPlaceRef only
- 不持久化未授权 provider 数据

## AI
- VisionProvider
- OCRProvider
- NLQueryProvider
- timeout/retry/error normalization
- secret redaction
- fixture tests

## Storage
- real local MinIO integration
- protected object
- TTL delete
- audit

## Live Smoke
无 Key 只阻塞 live smoke，不阻塞 adapter code/tests。
