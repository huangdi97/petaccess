# Blind-Model UI — Consumer Language（消费者语言契约）

> 目标（契约 §B）：用户可见文本中 UUID / snake_case 内部 token / 原始状态枚举 / 工程不变量命中数 = **0**（内在代码中存在但 DOM 不可见可接受）。

## 1. 映射层（Consumer Mapping Layer）

集中位置：`apps/client-h5/src/consumer/labels.ts`（及 `packages/client-core/src/labels.ts` 的 freshness 等共享词汇）。

| 模块 | 覆盖 | 示例 |
|---|---|---|
| `labels.ts` | zone 类型 / 楼层 / 动物范围 / 规则动作 / 规则状态 / 规则层级 / 约束力 / 观察动作 / 工作人员响应 / 设施状态与类型 / 便利设施 / 共处属性与值 / 入口类型 / 来源 | `zoneConsumerLine()`：种子名 `1F 公共区` → `一层公共区域`；`室内堂食区` 等消费者名保留 |
| `copy.ts`（design-tokens） | Reality 状态文案 | `NO_RECENT_RECORD` →「暂无记录不代表现实中没有动物。」 |
| `copy-empty.ts`（design-tokens） | 统一空态 | REALITY / EVIDENCE / SEARCH / MAP / HOME 等 |

页面**不得**自行拼 raw enum；全部经 `animalScopeLabel / ruleActionLabel / staffActionLabel / observedActionLabel / confidenceLabel / freshnessLabel` 等函数。

## 2. 本轮修复的泄漏点

| 位置 | 修复前（raw） | 修复后（consumer） |
|---|---|---|
| RealityTraceView 事件行 | `{{ o.animal_scope }} · {{ o.observed_action }}`（dog · enter） | `{{ animalScopeLabel(...) }} · {{ ruleActionLabel(...) }}`（犬 · 进入） |
| RealityTraceView 工作人员 | `{{ o.staff_action }}`（no_interaction_observed） | `{{ staffActionLabel(...) }}`（未观察到干预） |
| EvidenceView 证据条目 | 同上 raw enums | 同上 mapped |
| EvidenceView 来源 | `LABELS[x] ?? s.source_type`（未知值泄漏 raw） | `?? "其他来源"` / `?? "核验状态未知"` |
| EvidenceView 场所名 | `场所 {{ placeId }}`（UUID 泄漏） | `场所信息暂不可用`（契约 EVIDENCE_NO_UUID_TEXT） |
| PlaceView zone 行 | `1F 公共区`（种子名泄漏 `1F`） | `一层公共区域`（floorLabel + zoneTypeLabel） |
| reality_reports.py（后端展示文案） | `…（NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE）` | `暂无记录不代表现场没有动物。`（纯 copy，不改语义） |

## 3. 语言扫描结果（UI_ORACLE_STAGE=final）

`tools/ui-oracle/language-scan.ts` 对 7 个 Consumer 页面渲染后的可见文本扫描：

```
[language:final] total=21 FAIL=0
```

- 21 个页面/状态（含 global 7 页 + 各契约页）全部 PASS：`uuidHits / enumHits / invariantHits / allcapsHits` 均为空。
- 覆盖了「内在代码存在但 DOM 不可见可接受」的边界：如 `data-testid` 中的 `entry-reality-observed_presence`（属性名，非可见文本）、`data-ui` 值、`data-status` 值。

## 4. 语义不变量保持（本轮未改动 Domain）

- Observation ≠ Rule：Reality 页面明确「现场记录与平台核验姿态分开呈现」，事实≠规则。
- UNKNOWN ≠ allowed/prohibited：空态/未核验文案「尚未核验 ≠ 允许或禁止」。
- 服务犬 ≠ 普通宠物：label 层 `service_dog → 服务犬`、`ordinary_pet → 普通宠物`，无合并。
- 管理方声明与用户观察并存：evidence 页同时呈现管理方来源与用户观察条目。

## 5. 复现

```powershell
$env:UI_ORACLE_STAGE="final"; $env:PLAYWRIGHT_CHANNEL="chrome"
pnpm exec playwright test -c playwright.ui-oracle.config.ts   # 先产 probe
node --experimental-strip-types tools/ui-oracle/run-language.ts final
# 产物: artifacts/blind-ui-recovery/reports/language-scan.json
```
