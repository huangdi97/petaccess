# DATA_PIPELINE_SPEC.md

## 数据来源
1. government / official
2. operator official
3. platform verification
4. trusted verifier / mapping mission
5. ordinary user
6. external lead

external lead 只能产生 Candidate。

## 生命周期
DISCOVER → CAPTURE → EXTRACT → NORMALIZE → MATCH → VERIFY → REVIEW → PUBLISH → MONITOR → SUPERSEDE

## RuleCandidate
状态：
- DISCOVERED
- EXTRACTED
- MATCH_PENDING
- REVIEW_PENDING
- APPROVED
- REJECTED
- PUBLISHED
- SUPERSEDED

## SourceMonitor
只监控合法、安全来源。
必须有：
- content hash
- last checked
- last changed
- status
- failure count
- next check

changed → diff → Candidate，不直接改 Rule。

## Freshness
review_due ≠ invalid。
过期只表示“需要复核”。

## MappingMission
基础数据结构：
- scope
- target places
- target fields
- assignee
- completion
- QA sample

## 数据质量
- Rule Coverage
- Answerability
- Stale Rate
- Source Mix
- Candidate Approval Rate
- Attribution Error
- Change Latency
