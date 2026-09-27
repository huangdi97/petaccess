# PRODUCT.md — PetAccess

> **DERIVED DOCUMENT**
> Derived from `宠物准入与公共空间共处规则平台_v0.10-R1_RealityReport贡献体系_产品体验多端发行工程治理与Android全量验收_统一全量母版_2026-09-27.md`（Canonical Master）。
> **Canonical Master wins on conflict.**

## PetAccess 是什么

PetAccess = **Place Animal Coexistence Intelligence**：场所 · 动物 · 公共空间共处的规则与现实信息平台。回答用户去一个场所前的真实问题：

- 这里规则怎么说？
- 现实中最近发生了什么？
- 最近有没有看到动物？
- 工作人员怎么处理？
- 有没有动物设施？
- 规则和现实是否一致？
- 这些信息什么时候发生？
- 这些信息有什么证据？

核心模型 = **Rule Layer + Reality Layer + Evidence / Governance**。

## PetAccess 不是什么

- 不是宠物友好地图 / 萌宠社区 / 宠物点评 / 宠物友好榜 / 避雷黑榜 / 员工态度评分 / 大众点评宠物版 / 萌宠电商。

## 核心用户任务

去之前，查清规则与现场（"去之前，先看看这里的规则和现场"），在 ~20 秒内获得：

1. 该场所的规则结论（明确允许 / 有条件 / 明确限制 / 信息不足 / 来源不一致）；
2. 近期现场 Reality 概览（有无动物出现、工作人员处理、设施）；
3. 数据新鲜度与证据来源；
4. 规则与现实的 Divergence（仅真实相关时）。

## Rule / Reality / Evidence 模型

- **RuleAnswer**：统一结论（effect/compliance_state/summary/governing layer/mandatory levels），scope（zone/place/jurisdiction/mixed/none），conditions 与 unmet/missing inputs，evidence_state（provenance），conflict_state，rights_information。
- **RealityAnswer**：六种 RealitySummary state（OBSERVED_RECENTLY…DISPUTED）、last_seen、evidence_count、distinct_source_count、observed_zones/actions、staff_response_summary、facility_summary、freshness、verification。
- **StaffResponseSummary / FacilitySummary**：count + state + last_verified。
- **RuleRealityDivergence**：rule_effect vs reality_state + note。
- **EvidenceSummary**：rule evidence（provenance chain）、reality evidence count/sources/verification。
- **CoexistenceSnapshot** = 上述聚合，是 Consumer SSOT（Home/Search/Map/Place 统一消费，不得自拼第二套）。

## 核心 semantic invariants（永不动摇）

- Observation != Rule；Reality != Rule；StaffResponse != OperatorPolicy；Facility != EntryPolicy；Report != Claim；External Content != Official Policy；Place Mention != Exact Place Match；Publication Time != Event Time。
- No Observation != No Animal Presence；No Intervention Observed != Staff Deliberately Allowed。
- UNKNOWN != allowed / prohibited；暂无现场记录 != 没有动物。
- AI != final rule judge；AI/OCR 只生成待审候选。
- High-impact Rule 必须有 Source；管理方声明与用户观察并存。
- 小区不记录住户；不做遇宠率；不长期默认保存位置轨迹；不记员工态度分。
- Transport error 不得成为 domain fact：REQUEST_ERROR ≠ UNKNOWN ≠ EMPTY ≠ OFFLINE。
- 高影响 Rule 必须有 Source；管理方声明与用户观察并存。

## 当前阶段

- v0.1.0 Early Preview 已发布（Windows + Android）。v0.2.0 M1–M8 已完成；**当前 = M3 Consumer Core 深化收口**（UI/UX 全量设计实现 + 多端验收）；下一里程碑 M9_ANDROID_FINAL。
- 本轮范围：AppShell / Home / Search / 共享 Consumer primitives / Design Tokens + Consumer 架构收口。不吞并 M4（Map+Passport 深化）/ M5（Reality Trace+Evidence）/ M7（Contribution）完整 UX。
- 已有：CoexistenceSnapshot API、PlacePreview（桌面 Search split）、Design Token SSOT、AppShell（mobile tabbar + desktop rail）、Empty/Error/Offline 规范、状态守卫。

## 当前不做什么

- 不做真人 UAT、真实 Reality seed、真实 30 Place 覆盖、全国扩量、Public Beta、Production Publish、生产 DB 操作。
- 不重写 backend / Rule / Reality evaluator / DB / 前端框架 / Tauri。
- 不迁移技术栈（Vue 3 + TypeScript + Tauri + 现有 design system 不变）。

## 主要 Consumer surfaces

| Surface | 职责 | 本轮 |
|---|---|---|
| AppShell | navigation / route frame / safe area / offline / toast-dialog / theme / error boundary / version | M3 深化 |
| Home | search-first decision home：primary search、lens、附近已核验 / 规则待核实、Rule+Reality summary、freshness、evidence | M3 深化 |
| Search | 深链 ?q=/?lens=、结果行（identity/rule/reality/freshness/evidence）、桌面 split preview、筛选（不改变结论） | M3 深化 |
| Map / Place Passport | M4 | 仅共享层自然影响 |
| Reality Trace / Evidence | M5 | 仅共享层自然影响 |
| Contribution | M7 | 仅共享层自然影响 |
| Mine / Settings / Privacy | M2 既有 | 不受影响 |

## 视觉原则（详见 DESIGN.md）

Calm · Neutral · Urban · Evidence-first · Modern · Structured · Trustworthy · Lightweight。明确排除 cute / pet-commerce / social feed / government dashboard / cyberpunk / AI-gradient / gaming。
