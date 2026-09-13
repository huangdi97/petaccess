# PUBLISHED_RULES_SNAPSHOT_R1.md

> P0 — PILOT-REVIEW-PUBLISH-01 发布快照
> 快照时间：2026-09-13（GMT+8）· 基准 commit `08ee60c`
> 生成方式：`scripts/publish_reviewed_r1.py --dry-run`（未写库，见 §2 阻塞）

---

## 1. 已发布规则（Actual）

| 指标 | 值 |
|---|---|
| **Published AccessRule** | **0** |
| 已发布 RuleException | 0 |
| APPROVED 候选 | 0 |
| REJECTED 候选 | 0 |
| REVIEW_PENDING 候选 | 33 |
| ObservationCandidate（lead-only） | 3 |

> **0 是真实值，不是失败值。** 发布被两项外部条件阻塞（见 `REAL_DATA_PUBLISH_R1_REPORT.md` §2），本轮未发生任何数据库写入。

---

## 2. 阻塞状态

```text
ENV-01  数据层不可用（无 PostGIS）        → 阻塞写库
GOV-01  缺少具名人类评审员               → 阻塞 APPROVED 决策
```

`--dry-run` 实跑输出（真实执行结果）：

```json
{ "mode": "dry-run", "signed": false,
  "planned_counts": { "approved": 29, "rejected": 1, "held": 3,
                      "published": 0, "failed": 0 } }
```

---

## 3. 计划发布集（R1-A，17 条，待签署 → 待写库）

> 下表是**计划**，不是已发布事实。签署 + 数据层恢复后按此批次执行。

| # | 候选 ID | Place · Zone | scope / action / effect | layer | 证据 |
|---|---|---|---|---|---|
| 1 | `8151db71-3622-429d-81bc-0a0212f23290` | 前滩太古里 · 商场室内空间 | dog / enter / prohibited | LEGAL | primary_direct |
| 2 | `958d4d4c-6cd5-467e-9bc4-5eae2f67630e` | 前滩太古里 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+ADR-020 注记） |
| 3 | `49f2894e-2eae-4f57-bc97-f5ab7e0e0ba3` | 上海图书馆东馆 · 全馆 | dog / enter / prohibited | LEGAL | primary_direct |
| 4 | `caa28a93-94e9-4643-b6c1-bbd5d77c3ecc` | 上海图书馆东馆 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+注记） |
| 5 | `70d10467-a771-4331-bc3e-444eac424df2` | 港汇恒隆广场 · 室内商业空间 | dog / enter / prohibited | LEGAL | primary_direct |
| 6 | `d91706de-9447-4b3d-8977-fbfe08760c7e` | 港汇恒隆广场 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+注记） |
| 7 | `c8a3f92b-27eb-443e-bc0e-083458158582` | 和平饭店 · 全酒店 | dog / enter / prohibited | LEGAL | primary_direct |
| 8 | `e94d2259-7f77-4bb5-a81c-c5ac5bc81239` | 和平饭店 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+注记） |
| 9 | `1a97f24e-3cd0-445c-804d-741be34a0dad` | 星巴克烘焙工坊 · 全店 | dog / enter / prohibited | LEGAL | primary_direct |
| 10 | `b8cffbee-855a-4754-ad84-b01db0351ea3` | 星巴克烘焙工坊 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+注记） |
| 11 | `c2b179b9-77bf-433a-9219-5a406c42d5c7` | Manner 凯德虹口店 · 室内 | dog / enter / prohibited | LEGAL | primary_direct |
| 12 | `52936479-c385-4279-814e-aa7fe8ab0a42` | Manner 凯德虹口店 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+注记） |
| 13 | `6fc38502-85c7-4d7e-8a24-56fd5cc68e8a` | 西岸梦中心店 · 室内 | dog / enter / prohibited | LEGAL | primary_direct |
| 14 | `6bf5128a-17ad-4a2f-83e5-eabecc7afb9f` | 西岸梦中心店 · 场所级 | service_dog / enter / allowed | LEGAL | primary_direct（+注记） |
| 15 | `8f98fd01-9a1a-4d64-b354-01632d7bcd` | 广场公园（黄浦段）· H6宠物试点区域 | ordinary_pet / enter / conditional | TEMPORARY_POLICY | primary_direct |
| 16 | `70cc7579-1764-4177-82b5-fd2d5b255b37` | 大吉路公园 · 全园 | ordinary_pet / enter / conditional | TEMPORARY_POLICY | primary_direct |

> 注：第 15 行候选 ID 完整值为 `8f98fd01-9a1a-4d64-b354-01632d7bdbcd`（上表缩写排版，执行以 `review_decisions_r1.json` 为准）。
> 「+注记」= `RECOMMEND_APPROVE_WITH_NOTE`，须评审员确认 ADR-020 的 `service_role` 泛化。

---

## 4. 不进首批的候选

| 候选 | 处置 | 原因 |
|---|---|---|
| `f5a8d87f-…` dl-legal-dog | HOLD | 条例「文化娱乐场所」是否覆盖主题乐园属法律解释 |
| `ffb804af-…` gc-other-keep | HOLD | 原文无「禁止」表述，结论为推断 |
| `887f21ba-…` gh-outdoor-keep | HOLD | R2 修复未能证实；牵引条件为审慎默认值 |
| `ed79071d-…` mn-outdoor-media | REJECT | 归因错误实锤（CBNData 原文未报道该店） |

---

## 5. 快照校验

| 校验 | 结果 |
|---|---|
| `review_decisions_r1.json` 行数 | 33 |
| 与入库清单候选 ID 一一对应 | ✅（生成器强校验，缺失即 `SystemExit`） |
| 重复发布保护 | ✅ `publish()` 内 CAS（`candidate_already_published`） |
| 自反 supersession 保护 | ✅ `AccessRule.id != rule.id` |
| 弱证据发布拦截 | ✅ publish_gate `lead_only_source_not_publishable` + 脚本 preflight |
