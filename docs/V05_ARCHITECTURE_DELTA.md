# V05_ARCHITECTURE_DELTA.md

## 增量架构

```text
Legal / Regulatory
        ↓
Organization PolicyTemplate
        ↓
Place Override
        ↓
Zone Override
        ↓
Temporary/Event Rule
        ↓
EffectiveRuleResolver
        ↓
EffectiveRuleSet
        ├─ Pet Access Evaluation
        └─ Boundary Matching
```

数据生产：

```text
Source
→ DataSourceJob
→ Capture / OCR / AI / Import
→ RuleCandidate
→ Place/Zone Match
→ Review
→ AccessRule / RuleVersion
→ Freshness + SourceMonitor
```

空间：

```text
Place
├─ Zone
├─ Entrance
├─ AccessPath
└─ Amenity
```

用户：

```text
PetProfile
BoundaryProfile
        ↓
Explainable result
```

必须保留：
- Observation 独立
- Place UUID
- OpenAPI SSOT
- FastAPI/PostGIS/Redis/Celery
- client-core + uni-app x
- Vue Admin
- audit/dispute/watch

禁止：
- 重建 monorepo
- LLM 做 resolver
- BoundaryProfile 做综合评分
